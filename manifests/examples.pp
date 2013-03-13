class pump::examples {

file { '/opt/pump/bin/kenyaemr_sample_query_to_statsd':
    ensure  => present,
    mode => '0755',
    source => 'puppet:///modules/pump/examples/kenyaemr_sample_query_to_statsd.sh',
    require => File['/opt/pump/bin'],
  }

cron { 'cron_statsd_examples':
    command => '/opt/pump/bin/kenyaemr_sample_query_to_statsd',
    minute => '*',
  }
}
