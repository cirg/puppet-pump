#!/usr/bin/env python
"""
Every remote PUMP instance requires a unique label to identify the
source of all metrics found.

For KenyaEMR installations, the MFL is used as the unique identifier,
but it's not available at install time.

This module, typically provoked by an init script
(/etc/init.d/pump-post-install-daemon) sits in a check / sleep
loop until the MFL can be found in the database,
at which point it updates any necessary configuration files and
restarts the respective services.

"""
import argparse
import logging
import os
import sys
import subprocess
import time
import traceback
import yaml
import MySQLdb
import ConfigParser

DATABASE = 'openmrs'
PUMP_PREFIX_KEY = 'PUMP_PREFIX'
PUMP_UNINITIALIZED_PREFIX = 'NOT_INITIALIZED'
script_base_dir = os.path.join(os.path.dirname(__file__), '..')
script_base_dir = '/opt/appliance-setup'


class MysqlAccess(object):
    """Lightweight wrapper for accessing a mysql database """

    def __init__(self):
        self._conn = None

    def __exit__(self):
        """Called on exit from with statement"""
        self._conn.close()

    def __del__(self):
        if self._conn:
            self._conn.close()

    def close(self):
        if self._conn:
            self._conn.close()
        self._conn = None

    def cursor(self):
        """Returns a live cursor """
        if not self._conn:
            self.__connect()

        return self._conn.cursor()

    def __connect(self):
        """Obtain a database connection using the values in ~/.my.cnf

        """
        user, password, host = self.__fetchMyCnfProps()
        assert(user)
        try:
            logging.debug("Attempt mysql connection")
            self._conn = MySQLdb.connect(host=host,
                                         user=user,
                                         passwd=password,
                                         db=DATABASE)
            logging.debug("mysql connection to %s succeeded",
                          DATABASE)
        except MySQLdb.Error, e:
            raise Exception("Database connection error %d: %s" %
                            (e.args[0], e.args[1]))

    def __fetchMyCnfProps(self):
        """Read mysql connection properties from ~/.my.cnf

        returns tuple (user,passwd,host)

        """
        # work around a bootstrap problem when invoked by init script
        # before user directory correctly resoves...
        path = os.path.join(os.path.expanduser('~'), '.my.cnf')
        if path == '/.my.cnf' and os.getuid() == 0:
            path = '/root/.my.cnf'

        cp = ConfigParser.ConfigParser()
        with open(path, 'r') as mycnf:
            cp.readfp(mycnf)
        user = cp.get('client', 'user')
        pw = cp.get('client', 'password')
        host = cp.get('client', 'host')
        return user, pw, host


class PuppetLocalConfig(object):
    """Encapsulate interaction with puppet's local config file"""

    def __init__(self):
        self.local_yaml = os.path.join(script_base_dir,
                                       'puppet/etc/hieradb/local.yaml')
        self.global_yaml = os.path.join(script_base_dir,
                                        'puppet/etc/hieradb/global.yaml')

    def get(self, key):
        """lookup 'key' and return its value if found, else None"""
        # Prefer a local over global
        with open(self.local_yaml, 'r') as local_config:
            config = yaml.load(local_config.read())

            if config and key in config:
                return config[key]
            else:
                # Not found in local, try global
                with open(self.global_yaml, 'r') as global_config:
                    config = yaml.load(global_config.read())

                    if config and key in config:
                        return config[key]
        # Not found in either
        return None

    def set(self, key, value):
        """set 'key' to 'value' in puppet's local config file"""
        with open(self.local_yaml, 'r') as local_config:
            config = yaml.load(local_config.read())
            if config is None:
                raise RuntimeError("Unable to yaml-parse '%s'" %
                                   self.local_yaml)
            if key in config and config[key] == value:
                logging.warn("ignoring request to set `%s` to existing"
                             " value `%s`", key, value)
                return
            config[key] = value

        # write config back to disk to persist change
        # YAML comments are lost during parsing.  Prepend the global
        # configuration as a comment regardless.
        with open(self.local_yaml, 'w') as local_config:
            with open(self.global_yaml, 'r') as global_config:
                for i in global_config.readlines():
                    local_config.write('#%s' % i)
            local_config.write(yaml.dump(config,
                                         default_flow_style=False))
        logging.debug("set `%s` to `%s` in %s", key, value,
                      self.local_yaml)


class ConfigFile(object):
    """ Abstraction for each config file needing attention """
    def __init__(self, filepath, init_file=None):
        self.name = filepath
        self.init_file = init_file

    def write_pump_prefix(self, prefix):
        """Writes prefix to confix file - returns true if changed"""
        # don't mess unless we need to:
        devnull = open('/dev/null', 'w')
        if subprocess.call(["grep", PUMP_UNINITIALIZED_PREFIX,
                            self.name], stdout=devnull):
            logging.warn("No config changes for %s", self.name)
            return None

        # simply replace the uninitialized with the new prefix and
        # write back to disk.
        with open(self.name, 'r') as config:
            contents = config.read()

        results = []
        with open(self.name, 'w') as config:
            line = contents.replace(PUMP_UNINITIALIZED_PREFIX,
                                    prefix,)
            config.write(line)
            results.append(line)
        if ''.join(results) != contents:
            logging.info("New PUMP prefix: '%s' written to %s", prefix,
                         self.name)
            return True
        return False

    def restart(self):
        """Attempt a restart using the init_file provided at instantiation"""
        assert(self.init_file)
        logging.info("execute `%s restart`", self.init_file)
        feedback = subprocess.Popen([self.init_file, 'restart'],
                                    stdout=subprocess.PIPE)
        out, err = feedback.communicate()
        logging.debug(out)
        if err:
            logging.error(err)
            logging.exception(RuntimeError(
                "Unexpected STDERR from restart of %s:"
                "%s" % (self.init_file, err)))

CollectDConfig = ConfigFile('/opt/collectd/etc/collectd.conf',
                            init_file='/etc/init.d/collectd')
StatsDConfig = ConfigFile('/opt/statsd/local.js',
                          init_file='/etc/init.d/statsd')


class PumpPostInstall(object):
    """ Handles initialization steps following inital install of PUMP

    Sits in a check / sleep loop until it's satisfied the job is done.

    """
    def __init__(self):
        self.complete = False
        self.plc = PuppetLocalConfig()
        self.pump_prefix = self.plc.get(PUMP_PREFIX_KEY)
        self.config_files = (CollectDConfig, StatsDConfig)

    def satisfied(self):
        """Determine if the post setup state is satisfied

        returns True once all post setup data looks to be inplace, False
        otherwise (implying we should continue to occasionally poll).

        """
        if self.pump_prefix is not None:
            logging.info("Found well defined PUMP prefix '%s'",
                         self.pump_prefix)
        return self.pump_prefix is not None

    def poll_for_data(self):
        """Periodically look for data of interest

        Some data isn't available till after a user takes action, such as
        the site name and / or MFL.  This function knows where to look,
        and returns True if and only if the "interesting data" is found.

        """
        try:
            db = MysqlAccess()
            cursor = db.cursor()
            cursor.execute("SELECT property_value FROM global_property"
                           " WHERE property = 'kenyaemr.defaultLocation'")

            row = cursor.fetchone()
            location_id = row[0] if row else None
            # Prior to first Open MRS run, this may be null
            if location_id is None:
                logging.debug("'kenyaemr.defaultLocation' not yet set")
                return

            # Darius suggest future proofing this query using
            # this magic uuid
            UUID_OF_MFL_CODE_LOCATION_ATTRIBUTE_TYPE =\
                '8a845a89-6aa5-4111-81d3-0af31c45c002'

            # Darius says using that location_id will provide
            # the MFL code via:
            query = """select la.value_reference from
            location_attribute la  inner join
            location_attribute_type lat on
            lat.location_attribute_type_id =
            la.attribute_type_id where la.location_id =
            '%s'
            and lat.uuid =
            '%s'""" % (location_id,
                       UUID_OF_MFL_CODE_LOCATION_ATTRIBUTE_TYPE)

            cursor.execute(query)
            mfl = cursor.fetchone()[0]
            # For time being, the MFL alone is our lable with a
            # defining prefix
            self.pump_prefix = "MFL_%s" % mfl
            return self.pump_prefix

        except:
            logging.error(sys.exc_info())

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'db' in locals():
                db.close()

    def handle_new_prefix(self, prefix):
        """Called once when new data is found

        Method responsible for reacting to new data, i.e. the
        pump_prefix is freshly defined.  Trigger all necessary
        steps such as persisting, editing config files and
        restarting any necessary services

        """
        self.persist_data()
        needing_restart = []
        for config in self.config_files:
            if config.write_pump_prefix(self.pump_prefix):
                needing_restart.append(config)

        for app in needing_restart:
            app.restart()

    def persist_data(self):
        """Store prefix in puppet config for subsequent runs. """
        if self.plc.get(PUMP_PREFIX_KEY) != self.pump_prefix:
            logging.debug("persisting pump_prefix: '%s'", self.pump_prefix)
            self.plc.set(PUMP_PREFIX_KEY, self.pump_prefix)

    def main(self):
        wait_interval = 5
        logging.info("Launch time")
        time.sleep(wait_interval)
        while not self.satisfied():
            if not self.poll_for_data():
                logging.debug("sleep(%d)", wait_interval)
                time.sleep(wait_interval)
        self.handle_new_prefix(self.pump_prefix)
        logging.info("Exit time")


def log_uncaught_exceptions(type, value, tb):
    logging.critical(''.join(traceback.format_tb(tb)))
    logging.critical('{0}: {1}'.format(type, value))
    
def configure_logging(logfile, verbosity=0):
    """Configure logging - sent to stdout so redirection works"""
    kwargs = {'format': '%(asctime)s [%(levelname)s] %(message)s',
              'datefmt': '%a %b %d %H:%M:%S %Y', 'filemode': 'a',
              'filename': '/tmp/fa'}
    level = (logging.WARNING, logging.INFO, logging.DEBUG)
    kwargs['level'] = level[verbosity]
    kwargs['filename'] = logfile
    logging.basicConfig(**kwargs)
    sys.excepthook = log_uncaught_exceptions

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logfile', dest='logfile', default=None)
    parser.add_argument('--verbosity', dest='verbosity', type=int,
                        default=1)
    args = parser.parse_args()
    configure_logging(logfile=args.logfile, verbosity=args.verbosity)
    PumpPostInstall().main()
