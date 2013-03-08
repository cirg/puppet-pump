#!/usr/bin/env python
"""Unittest for PUMP post_install module.

NB - this does modify config files used in testing - avoid running in
production settings unless you know what you're doing!!  Perfect
however, for development work on an issolated VM.

"""
import unittest
from post_install import MysqlAccess, configure_logging
from post_install import PumpPostInstall, PuppetLocalConfig
from post_install import PUMP_UNINITIALIZED_PREFIX


class TestPuppetLocalConfig(unittest.TestCase):

    def setUp(self):
        self.plc = PuppetLocalConfig()

    def testBogus(self):
        """Confirm bogus lookup returns None"""
        self.assertEquals(None, self.plc.get('noEffinWay'))

    def testNearCertain(self):
        """'classes' will be defined on appliance-setup host"""
        self.assertNotEquals(None, self.plc.get('classes'))

    def testSet(self):
        """Confirm we can store a value"""
        key = 'unittest-fakekey'
        value = 'unittest-fakevalue'
        self.plc.set(key, value)
        self.assertEquals(self.plc.get(key), value)


class TestPumpPostInstall(unittest.TestCase):

    def setUp(self):
        self.db = MysqlAccess()

    def test_mysql(self):
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT VERSION()")
            self.assertTrue('5.' in cursor.fetchone()[0])
        finally:
            cursor.close()

    def test_OMRS_default_location(self):
        "Before the value is set, no property_value should be found"
        ppi = PumpPostInstall()
        if not ppi.satisfied():
            ppi.poll_for_data()
            if ppi.pump_prefix is not None:
                # counts as a pass, testing on a system that has
                # apparently completed OMRS initiation
                return
            # Otherwise, we shouldn't find any value, like it's pre-init.
            query = """SELECT property_value FROM global_property
            WHERE property = 'kenyaemr.defaultLocation'"""
            try:
                cursor = self.db.cursor()
                cursor.execute(query)
                self.assertEquals(None, cursor.fetchone()[0])
            finally:
                cursor.close()

    def test_config_files(self):
        """Look for updated config files"""
        ppi = PumpPostInstall()
        ppi.handle_new_prefix("unittest_prefix")
        for c in ppi.config_files:
            with open(c.name, 'r') as config:
                for l in config.readlines():
                    self.assertFalse(PUMP_UNINITIALIZED_PREFIX in l)

if __name__ == '__main__':
    configure_logging(2)
    unittest.main()
