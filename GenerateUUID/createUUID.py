import uuid
import logging
import sys

try:
    uid = uuid.uuid4().hex
    print(uid)
    f = open('/etc/squid/uuid.txt', 'w')
    f.write(uid)
    f.close()

except:
    e = sys.exc_info()[0]
    logging.error("cannot open uuid.txt file, error: %s" % e)
