class pump::statsd {

  package { [
    'curl',
	'build-essential',
	'libssl-dev',
  ]:
    ensure => installed,
  }
  
  exec{ 'nodejs-git-clone':
    command => '/usr/bin/git clone --depth 1 git://github.com/joyent/node.git /opt/node',
    creates => '/opt/node',
    logoutput => 'true',
	require => Package['libssl-dev'],
  }
  
  exec{ "nodejs-install-1":
    cwd => '/opt/node',
    command => '/usr/bin/git checkout v0.8.9', 
    logoutput => 'on_failure',
	require => Exec['nodejs-git-clone'],
  }
  
  exec{ "nodejs-install-2":
    cwd => '/opt/node',
    command => './configure --prefix=/opt/node', 
    logoutput => 'on_failure',
	require => Exec['nodejs-install-1'],
  }
  
  exec{ "nodejs-install-3":
    cwd => '/opt/node',
    command => 'make', 
    logoutput => 'on_failure',
	require => Exec['nodejs-install-2'],
  }
  
  exec{ "nodejs-install-4":
    cwd => '/opt/node',
    command => 'make install', 
    logoutput => 'on_failure',
	require => Exec['nodejs-install-3'],
  }
  
  exec{ 'statsd-git-clone':
    command => '/usr/bin/git clone https://github.com/etsy/statsd /opt/statsd',
    creates => '/opt/statsd',
    logoutput => 'true',
	require => Exec['nodejs-install-4'],
  }
  
  file {"/usr/share/tomcat6/.OpenMRS/openmrs-runtime.properties":
    content => '
  {
 graphitePort: 2003
, graphiteHost: "localhost"
, port: 8125
, backends: [ "./backends/graphite" ]
, flushInterval: 1000
}',
  require => Exec['statsd-git-clone'],
  }  
}
