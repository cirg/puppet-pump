class pump::acquire {

package { [
    'python-statsd',
  ]:
    ensure => installed,
    provider => pip,
  }

file { '/opt/pump/bin/check_host':
    ensure  => present,
    mode => '0755',
    source  => 'puppet:///modules/pump/acquire/check_host.py',
    require => File['/opt/pump/bin'],
  }

cron { 'pump_check_host':
    command => '/opt/pump/bin/check_host',
    minute => '*',
    require => File['/opt/pump/bin/check_host'],
  }
}
