class pump::graphite {
  include apache

  # Packages

  package { [
    'libapache2-mod-wsgi',
    'python-cairo',
    'python-django',
    'python-django-tagging',
    'python-memcache',
    'python-pip',
    'python-pysqlite2',
    'python-twisted',
	'python-mysqldb'
  ]:
    ensure => installed,
  }

  # PIP Packages
  # 
  # TODO: The package installation detection doesn't work for carbon
  # or graphite-web. `pip install graphite-web` reinstalls
  # graphite-web even if it already installed. (`pip install whisper`
  # will print "Requirement already satisfied".) This causes puppet to
  # reinstall these packages each time it is run.

  package { [
    'carbon',
    'graphite-web',
    'whisper',
  ]:
    ensure   => installed,
    provider => pip,
    require  => Package['python-pip'],
  }

  # Configuration files

  file { '/opt/graphite/webapp/graphite/local_settings.py':
    ensure  => present,
    source  => 'puppet:///modules/pump/graphite/local_settings.py',
    require => Package['graphite-web'],
  }

  file { '/opt/graphite/conf/carbon.conf':
    ensure  => present,
    source  => 'puppet:///modules/pump/graphite/carbon.conf',
    require => Package['graphite-web'],
  }

  file { '/opt/graphite/conf/dashboard.conf':
    ensure  => present,
    source  => 'puppet:///modules/pump/graphite/dashboard.conf',
    require => Package['graphite-web'],
  }

  file { '/opt/graphite/conf/graphite.wsgi':
    ensure  => present,
    source  => 'puppet:///modules/pump/graphite/graphite.wsgi',
    require => Package['graphite-web'],
  }

  file { '/opt/graphite/conf/storage-aggregation.conf':
    ensure  => present,
    source  => 'puppet:///modules/pump/graphite/storage-aggregation.conf',
    require => Package['graphite-web'],
  }

  file { '/opt/graphite/conf/storage-schemas.conf':
    ensure  => present,
    source  => 'puppet:///modules/pump/graphite/storage-schemas.conf',
    require => Package['graphite-web'],
  }

  # Ensure webapp/graphite is owned by www-data:www-data

  file { '/opt/graphite/storage':
    ensure  => directory,
    recurse => true,
    group   => 'www-data',
    owner   => 'www-data',
    require => Package['graphite-web'],
  }
  
  exec { 'graphite-syncdb':
    cwd     => '/opt/graphite/webapp/graphite',
    command => '/usr/bin/python manage.py syncdb --noinput',
	timeout => 5000,
	require => File['/opt/graphite/conf/storage-schemas.conf'],
  }

  # Carbon init scripts

  file { '/etc/init.d/carbon-cache':
    ensure  => present,
    source  => 'puppet:///modules/pump/graphite/carbon-cache',
    mode    => '0755',
    require => Package['carbon'],
  }

  service { 'carbon-cache':
    ensure  => 'running',
    enable  => true,
    require => File['/etc/init.d/carbon-cache'],
  }

  # Apache configuration

  file { '/etc/apache2/conf.d/pump.conf':
    ensure  => present,
    source  => 'puppet:///modules/pump/pump.conf',
    require => [
      Package['httpd'],
    ],
    notify  => Service['httpd'],
  }
}
