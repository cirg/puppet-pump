class pump::pump_rsync {
$username = 'pump_rsync_user'
$groupname = 'www-data'

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
    mode    => '0755',
    source  => 'puppet:///modules/pump/pump_rsync/pump_rsync',
    require => File['/opt/pump/bin'],
  }

user { $username:
    comment => "user authenticated to rsync with hub",
    gid     => "$groupname",
    home    => "/home/$username",
    shell   => "/bin/bash",
  }

cron { 'cron_rsync':
    command => '/opt/pump/bin/pump_rsync',
    user => 'root',
    minute => '*/10',
  }

file { "/home/$username/":
    ensure  => directory,
    owner   => $username,
    group   => $groupname,
    mode    => 750,
    require => User[$username],
  }

file { "/home/$username/.ssh":
    ensure  => directory,
    owner   => $username,
    group   => $groupname,
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
