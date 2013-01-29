class pump::collectd {

file { '/opt/collectd':,
    ensure => directory,
    mode => '0775',
  }

exec { 'download-collectd':
    cwd     => '/opt/collectd',
    creates => '/opt/collectd/collectd-5.1.1.tar.gz',
    command => '/usr/bin/wget \'http://collectd.org/files/collectd-5.1.1.tar.gz\'',
	timeout => 5000,
  }

exec { 'unzip-collectd':
    cwd     => '/opt/collectd',
    command => 'tar -zxvf collectd-5.1.1.tar.gz',
	require => Exec['download-collectd'],
	timeout => 5000,
  }
  
exec { 'configure-collectd':
    cwd     => '/opt/collectd/collectd-5.1.1',
    command => './configure',
	require => Exec['unzip-collectd'],
  }
  
exec { 'make-collectd':
    cwd     => '/opt/collectd/collectd-5.1.1',
    command => 'make',
	require => Exec['configure-collectd'],
  }
  
exec { 'makeinstall-collectd':
    cwd     => '/opt/collectd/collectd-5.1.1',
    command => 'make install',
	require => Exec['make-collectd'],
  }  
}