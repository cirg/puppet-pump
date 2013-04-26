#!/usr/bin/env python
import statsd
from urllib2 import urlopen, URLError

# Move the following to a YAML config file
prefix = 'KenyaEMR_status'
url = 'https://localhost/openmrs/index.htm'
timeout = 5
acceptable_codes = [200,]


counter = statsd.Counter(prefix)
def success():
    "Call on success - generates statsd call"
    counter.increment('success')

def fail():
    "Call on failure - generates statsd call"
    counter.increment('failure')


try:
    response = urlopen(url, timeout=timeout)
    if response.code in acceptable_codes:
        success()
    else:
        fail()
except URLError, e:
    fail()
