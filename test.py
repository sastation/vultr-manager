#!/usr/bin/env python

import json

fs = open('vultr-mgr.conf', 'r')
lines = fs.readlines()
content = ''.join(lines)
fs.close()

data = json.loads(content)
print(data)

print data['sshid']
print data['location']
