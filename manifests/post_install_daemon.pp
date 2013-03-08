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
    source  => 'puppet:///modules/pump/post_install_daemon/init',
    require => File['/opt/pump/bin/pump_post_install_daemon'],
  }

service { 'pump_post_install_daemon':
    ensure  => 'running',
    enable  => true,
    require => File['/etc/init.d/pump_post_install_daemon'],
  }  
}
