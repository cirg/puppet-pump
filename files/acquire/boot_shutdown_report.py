#!/usr/bin/env python

"""Manages communicating boot and shutdown times to PUMP

Due to race conditions at system boot and shutdown, statsd can't be
used, as the timestamp needs to match the event.

By writing marker files to record events, this script can continue to
alert carbon of the pre-recorded event until it shows up.

"""
import argparse
import datetime
import json
import logging
import os
import socket
import sys
import time
from urllib2 import urlopen, URLError

# work around a lack of packaging and a non .py file needing to be imported
import imp
pump = imp.load_source('pump_post_install_daemon', 
                       '/opt/pump/bin/pump_post_install_daemon')

GRAPHITE_HOST = 'localhost'
CARBON_HOST = 'localhost'
CARBON_PORT = 2003
BOOTTAG = "system.boot"
SHUTDOWNTAG = "system.shutdown"

path = '/var/log'
REPORT_FILE = os.path.join(path, "pending_boot_shutdown_events")

def server_code():
    """Looks up the unique server code, such as an MFL from the install

    This code is prepended to all carbon stats to differentiate the
    data being sent to a common HUB.  Typically handled by statsd or
    collectd configs, necessary when sending directly to carbon.

    """
    plc = pump.PuppetLocalConfig()
    code = plc.get(pump.PUMP_PREFIX_KEY)
    return code if code else pump.PUMP_UNINITIALIZED_PREFIX

def convert_fromtime(eventtime):
    """Translate the eventtime into a graphite from value

    The graphite API accepts values like '-1hours'.  Return a value
    that safely covers the eventtime.

    """
    # Start at one hour back, increase until the eventtime is greater
    hours = 1
    while True:
        trytime = time.time() -\
            datetime.timedelta(hours=hours).seconds
        if trytime < eventtime:
            return '-%dhours' % hours
        hours += 1

def check_for_value(event, eventtime):
    """Return value for event at eventtime, if found in carbon.

    Hits the Graphite API looking for a value stored at eventtime in
    the named event.  If found returns that value, otherwise returns
    None

    """
    assert(event in (BOOTTAG, SHUTDOWNTAG))
    params = {'host': GRAPHITE_HOST,
              'event': '.'.join((server_code(), event)),
              'fromtime': convert_fromtime(eventtime)}

    # Query the Graphite API for recent values for this event
    url = 'https://%(host)s/render?target=%(event)s'\
        '&format=json'\
        '&from=%(fromtime)s' % params
    logging.debug("query: %s",url)
    try:
        response = urlopen(url, timeout=5)
    except URLError, e:
        logging.exception(e)
        logging.debug("assuming graphite isn't ready - continue iteration")
        return None

    if response.code != 200:
        return None
    results = json.loads(response.read())
    logging.debug(results)
    if not results:
        return None
    #eventtime must be floored to the nearest min to match carbon's settings
    eventtime = eventtime - (eventtime % 60)
    value = [(v,tm) for v,tm in results[0]['datapoints'] if tm == eventtime]
    if len(value) == 1:
        return value[0]
    else:
        return None

def send_carbon_message(event, eventtime):
    "Send message directly to carbon"
    message = ("%s.%s 1 %d\n" % (server_code(), event, eventtime))
    logging.debug("sending carbon message: %s", message)
    sock = socket.socket()
    sock.connect((CARBON_HOST, CARBON_PORT))
    sock.sendall(message)
    sock.close()

def mark_event(event):
    # drop timestamp in report file for this event
    assert(event in (BOOTTAG, SHUTDOWNTAG))
    timestamp = int(time.time())
    with open(REPORT_FILE, 'a') as f:
        line = "%s %d\n" % (event, timestamp)
        f.write(line)
        logging.debug("write to file: %s line: %s", f.name, line)

def start():
    """Entry point from system boot - start the service

    Mark's the startup event and handles bookkeeping of any missing
    events in carbon.

    """
    mark_event(BOOTTAG)

    # Queue up all events potentially needing to be recorded
    with open(REPORT_FILE, 'r') as f:
        queue = [el for el in f.readlines()]

    # Iterate and handle all queued events
    while len(queue) > 0:
        event, timestamp = queue[-1].split()
        assert(event in (BOOTTAG, SHUTDOWNTAG))
        timestamp = int(timestamp)
        if check_for_value(event, timestamp):
            logging.info("poping %s %d", event, timestamp)
            queue.pop()
        # Attempt to write this event, then sleep for a bit
        # should we be caught in the bootup cycle yet
        send_carbon_message(event, timestamp)
        time.sleep(3)

    # All done!  Implies all event in the log are persisted - purge
    with open(REPORT_FILE, 'w') as f:
        f.truncate()

def stop():
    """Entry point for system shutdown - stop the service"""
    mark_event(SHUTDOWNTAG)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('start', 'stop'))
    parser.add_argument('--logfile', dest='logfile', default=None)
    parser.add_argument('--verbosity', dest='verbosity', type=int,
                        default=1)
    args = parser.parse_args()
    pump.configure_logging(logfile=args.logfile, verbosity=args.verbosity)
    logging.info("begin - command %s", args.command)

    if args.command == 'start':
        start()
    elif args.command == 'stop':
        stop()

    logging.info("exiting - completed %s", args.command)

