# == Class: pump
#
# Installs suite of tools used for collection, storage and
# visualization of system and application data and utilization.
#
# === Authors
#
# Anikate Singh <aniksing@uw.edu>
# Paul Bugni <pbugni@u.washington.edu>
#
# === Copyright
#
# Copyright 2013 University of Washington
#
class pump {
  include pump::acquire
  include pump::graphite
  include pump::collectd
  include pump::statsd
  include pump::pump_rsync
  include pump::post_install_daemon
}
