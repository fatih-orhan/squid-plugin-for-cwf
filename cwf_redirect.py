#!/usr/bin/env python

import sys
import ConfigParser
import logging
import fls_lookup
import traceback

logging.basicConfig(filename="cwf_redirect.log", level=logging.DEBUG)

category_map = dict()
allowedMap = dict()

try:
    uuid_file = open('uuid.txt', 'r')
    UUID = uuid_file.read()
    if UUID == '':
        logging.error("uuid can not be empty!")
        exit(0)
except:
    logging.error("file read exception" + str(traceback.format_exc()))

try:
    config = ConfigParser.ConfigParser()
    config.readfp(open('cwf_redirect_properties.conf'))
except:
    e = sys.exc_info()[0]
    logging.error("cannot open properties file, error: %s" % e)

try:
    invalidUrl = config.get('properties', 'invalidUrl')
except:
    e = sys.exc_info()[0]
    logging.error("cannot get invalid url, error: %s" % e)

    # all categories with the category id is read from category_definitions.conf file and put the map
    # created allowedMap by checking properties file
    # all url is checked it enabled or disabled and return the message
try:
    with open("category_definitions.conf") as l:
        for url_line in l:
            one_line = url_line.split("=")
            category_map[int(one_line[0])] = one_line[1]
except:
    e = sys.exc_info()[0]
    logging.error("cannot get category definitions from file: category_definitions.conf, error: %s" % e)

try:
    for m in category_map:
        val = category_map.get(m).split("\n")[0];
        try:
            isAllowed = config.get('categories', val)
            allowedMap[m] = isAllowed
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            isAllowed = None
except:
    e = sys.exc_info()[0]
    logging.error("cannot create map for category permission, error: %s" % e)


def modify_url(url):
    blocked = False
    new_url = '\n'

    if url is None:
        return url + new_url

    url_list = url.split(' ')
    if url.__len__() < 1:
        return url + new_url

    # first element of the list is the URL
    old_url = url_list[0]

    logging.debug("requesting this url %s" % old_url)

    response = fls_lookup.fls_vendor_lookup(old_url, UUID)

    if response > 0:
        for category in response:
            logging.debug("for %s, category id is: %d" % (old_url, category.category_id))
            if allowedMap.get(category.category_id) is None:
                logging.debug("no information about %s category %d" % (old_url, category.category_id))
            else:
                if int(allowedMap.get(category.category_id)) == 0:
                    logging.debug("for %s, category is in blocked categories %d" % (old_url, category.category_id))
                    blocked = True
                else:
                    logging.debug("for %s, category is in allowed categories %d" % (old_url, category.category_id))

        if blocked:
            return invalidUrl + new_url
        else:
            return old_url + new_url

    else:
        logging.error("cannot get information from FLS")
        return old_url + new_url


while True:
    url_line = sys.stdin.readline().strip()

    modified_url = modify_url(url_line)

    logging.debug("modified url %s" % modified_url)

    sys.stdout.write(modified_url)
    sys.stdout.flush()
