class pump::collectd {
include pump::collectd

package { [
    'curl',
	'build-essential',
	'libssl-dev',
  ]:
    ensure => installed,
  }

file { '/opt/collectd':,
    ensure => directory,
    mode => '0775',
  }

exec { 'download-collectd':
    cwd     => '/opt/collectd',
    creates => '/opt/collectd/collectd-5.1.1.tar.gz',
    command => '/usr/bin/wget \'http://collectd.org/files/collectd-5.1.1.tar.gz\'',
	timeout => 5000,
	require => File['/opt/collectd'],
  }

exec { 'unzip-collectd':
    cwd     => '/opt/collectd',
    command => '/bin/tar -zxvf collectd-5.1.1.tar.gz',
    require => Exec['download-collectd'],
    timeout => 5000,
  }
  
exec { 'configure-collectd':
    cwd     => '/opt/collectd/collectd-5.1.1',
    command => '/opt/collectd/collectd-5.1.1/configure',
    require => Exec['unzip-collectd'],
  }

exec { 'make-collectd':
    cwd     => '/opt/collectd/collectd-5.1.1',
    command => '/usr/bin/make',
	require => Exec['configure-collectd'],
  }
  
exec { 'makeinstall-collectd':
    cwd     => '/opt/collectd/collectd-5.1.1',
    command => '/usr/bin/make install',
	require => Exec['make-collectd'],
  }  
  
file { '/etc/init.d/collectd':
    ensure  => present,
    source  => 'puppet:///modules/pump/collectd/collectd',
    require => Exec['makeinstall-collectd'],
  }  

file { '/opt/collectd/etc/collectd.conf':
    ensure  => present,
    source  => 'puppet:///modules/pump/collectd/collectd.conf',
    require => Exec['makeinstall-collectd'],
  }
  
service { 'collectd':
    ensure  => 'running',
    enable  => true,
    require => File['/etc/init.d/collectd'],
  }  
}
