class pump::statsd {

include pump::collectd
    
  exec{ 'nodejs-git-clone':
    command => '/usr/bin/git clone --depth 1 git://github.com/joyent/node.git /opt/node',
    creates => '/opt/node',
    logoutput => 'true',
	timeout => -1,
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
    command => '/opt/node/configure --prefix=/opt/node', 
    logoutput => 'on_failure',
	require => Exec['nodejs-install-1'],
    timeout => -1,
  }
  
  exec{ "nodejs-install-3":
    cwd => '/opt/node',
    command => '/usr/bin/make', 
    logoutput => 'on_failure',
    timeout => -1,
	require => Exec['nodejs-install-2'],
  }
  
  exec{ "nodejs-install-4":
    cwd => '/opt/node',
    command => '/usr/bin/make install', 
    logoutput => 'on_failure',
    timeout => -1,
	require => Exec['nodejs-install-3'],
  }
  
  exec{ 'statsd-git-clone':
    command => '/usr/bin/git clone https://github.com/etsy/statsd /opt/statsd',
    creates => '/opt/statsd',
    logoutput => 'true',
	require => Exec['nodejs-install-4'],
  }
  
  file {"/opt/statsd/local.js":
    content => '
  {
 graphitePort: 2003
, graphiteHost: "localhost"
, port: 8125
, backends: [ "./backends/graphite" ]
, flushInterval: 1000
, graphite: { legacyNamespace: false
,   globalPrefix: "NOT_INITIALIZED."
,   prefixCounter: ""
,   prefixTimer: ""
,   prefixGauge: ""
,   prefixSet: ""
}',
  require => Exec['statsd-git-clone'],
  }  
  
  file { '/etc/init.d/statsd':
    ensure  => present,
    source  => 'puppet:///modules/pump/statsd/statsd',
    require => Exec['statsd-git-clone'],
  } 
  
  service { 'statsd':
    ensure  => 'running',
    enable  => true,
    require => File['/etc/init.d/statsd'],
  }  
}
