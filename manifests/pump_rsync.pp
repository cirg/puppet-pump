class pump::pump_rsync {
$username = 'pump_rsync_user'

file { '/opt/pump':,
    ensure => directory,
    mode => '0775',
  }

file { '/opt/pump/bin':,
    ensure => directory,
    mode => '0775',
    require => File['/opt/pump'],
  }

file { '/opt/pump/bin/pump_rsync':
    ensure  => present,
    mode => '0755',
    require => File['/opt/pump/bin'],
    content => 'rsync -az /opt/graphite/storage/whisper/ ${username}@pump.kenyaemr.org:/opt/graphite/storage/whisper',
  }

user { $username:
    comment => "user authenticated to rsync with hub",
    home    => "/home/$username",
    shell   => "/bin/bash",
  }

group { 'pump_rsync_user':
    require => User[$username]
  }

cron { 'cron_rsync':
    command => '/opt/pump/bin/pump_rsync',
    user => $username,
    minute => '*/10',
  }

file { "/home/$username/":
    ensure  => directory,
    owner   => $username,
    group   => $username,
    mode    => 750,
    require => [ User[$username], Group[$username] ]
  }

file { "/home/$username/.ssh":
    ensure  => directory,
    owner   => $username,
    group   => $username,
    mode    => 700,
    require => File["/home/$username/"]
  }

exec { "ssh-keygen -q -t rsa -f /home/$username/.ssh/id_rsa -P ''":
    creates     => "/home/$username/.ssh/id_rsa",
    path        => "/bin:/usr/bin",
    user        => $username,
    require     => File["/home/$username/.ssh"],
  }

# TODO: awaiting a mail transfer agent module to include...
# Mail the resultant public key </home/$username/.ssh/id_rsa.pub>
# to cirg administration.
}
