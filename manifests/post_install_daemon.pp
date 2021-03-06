class pump::post_install_daemon {

package { [
    'python-argparse',
  ]:
    ensure => installed,
  }

file { '/opt/pump/bin/pump_post_install_daemon':
    ensure  => present,
    mode => '0755',
    source  => 'puppet:///modules/pump/post_install_daemon/post_install.py',
    require => File['/opt/pump/bin'],
  }

file { '/etc/init.d/pump_post_install_daemon':
    ensure  => present,
    source  => 'puppet:///modules/pump/post_install_daemon/pump_post_install_daemon',
    require => File['/opt/pump/bin/pump_post_install_daemon'],
  }

# Require also the files that get edited, as race conditions exist
# between multiple puppet threads
service { 'pump_post_install_daemon':
    ensure  => 'running',
    enable  => true,
    require => [File['/opt/statsd/local.js'], File['/opt/collectd/etc/collectd.conf'], File['/etc/init.d/pump_post_install_daemon']],
  }  
}
