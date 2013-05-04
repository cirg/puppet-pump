class pump::acquire {

package { [
    'python-statsd',
  ]:
    ensure => installed,
    provider => pip,
  }

file { '/opt/pump/bin/boot_shutdown_report':
    ensure  => present,
    mode => '0755',
    source  => 'puppet:///modules/pump/acquire/boot_shutdown_report.py',
    require => File['/opt/pump/bin'],
  }

file { '/etc/init.d/boot_shutdown_report':
    ensure  => present,
    source  => 'puppet:///modules/pump/acquire/boot_shutdown_report',
    require => File['/opt/pump/bin/boot_shutdown_report'],
  }

service { 'boot_shutdown_report':
    enable  => true,
    require => File['/etc/init.d/boot_shutdown_report'],
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
    require => [File['/opt/pump/bin/check_host'],
    	        Package['python-statsd']]
  }
}
