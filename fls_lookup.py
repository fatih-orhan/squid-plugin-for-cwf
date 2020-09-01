import ConfigParser
import logging
import socket
import struct
import sys
import traceback

from fls_socket_client import FlsSocketClient

LENGTH_OF_REQUEST = 26  # length of the rest of request, starting from next byte ((4 + 1 +2 + 1 + 16 + 2 ) #  + urllength bytes)
LENGTH_OF_ALLREQUEST = 32  # (1 + 1 + 1 + 1 + 2 + 4 + 1 + 2 + 1 + 16 + 2 ) + (urllength) bytes
REQUEST_ID = 444
MARKER = 239
LOOKUP_REQUEST_TYPE = 36
LOOKUP_PROTO_VERSION = 7
APPLICATION_ID = 7  # ??
CALLER_TYPE_ON_DEMAND = 2
APPLICATION_VERSION = 10  # ??
UUID_LENGTH = '16'
XXXXLL = 6
TTN = 3  # (byte value (tt 2 bytes, n 1 byte))
CCSS = 4  # (byte value (cc 2 bytes, ss 2 byte))


config = None
try:
    config = ConfigParser.ConfigParser()
    config.readfp(open('/etc/squid/cwf_redirect_properties.conf'))
except:
    e = sys.exc_info()[0]
    logging.error("cannot open properties file, error: %s" % e)

try:
    fls_host = config.get('properties', 'fls_host')
except:
    e = sys.exc_info()[0]
    logging.error("cannot get fls host from properties file, error: %s" % e)
try:
    fls_tcp_port = int(config.get('properties', 'fls_tcp_port'))
except:
    e = sys.exc_info()[0]
    logging.error("cannot get fls port from properties file, error: %s" % e)

try:
    fls_udp_port = int(config.get('properties', 'fls_udp_port'))
except:
    e = sys.exc_info()[0]
    logging.error("cannot get fls udp port from properties file, error: %s" % e)


class Category:
    def __init__(self, category_id, url_length):
        self.category_id = category_id
        self.url_length = url_length


def to_hex(byte_array):
    return bytearray(byte_array)


def to_numbers(byte_array):
    appended_string = ""
    for val in byte_array:
        appended_string = appended_string + " " + str(hex(val))

    return appended_string


def to_bytes(val):
    return bytes(chr(val))

    # request format MPTRLLXXXXAVC[GUID]NN[URL]+


def serialize_lookup_request(url, uuid):
    length_of_url = len(url)
    length_of_request = LENGTH_OF_REQUEST + length_of_url

    data = struct.pack('>ccccHichc' + UUID_LENGTH + 'sh' + str(length_of_url) + 's',
                       to_bytes(MARKER), to_bytes(LOOKUP_PROTO_VERSION), to_bytes(LOOKUP_REQUEST_TYPE), to_bytes(1),
                       length_of_request,
                       REQUEST_ID, to_bytes(APPLICATION_ID), APPLICATION_VERSION, to_bytes(CALLER_TYPE_ON_DEMAND), uuid,
                       length_of_url, url)

    request_length = LENGTH_OF_ALLREQUEST + length_of_url

    return data, request_length


# response format XXXXLL[TTN[CCSS]+]+
def deserialize_detect_response(received_data):
    category_list = []
    try:
        other_urls = 0
        request, length_of_response = struct.unpack_from('>lH', received_data, 0)
        if request == REQUEST_ID:
            while length_of_response != other_urls:
                other_urls = 0
                ttl, number_of_categories = struct.unpack_from('>hc', received_data, XXXXLL + other_urls)
                number_of_categories = int(to_numbers(to_hex(number_of_categories)), 16)
                j = 0
                if number_of_categories > 0:
                    for i in range(0, number_of_categories, 1):
                        if struct.unpack_from('>h', received_data, 9 + other_urls + j).__len__() > 0:
                            category_id = int(struct.unpack_from('>h', received_data, 9 + other_urls + j)[0])
                        else:
                            continue

                        if struct.unpack_from('>H', received_data, 11 + other_urls + j).__len__() > 0:
                            url_length = int(struct.unpack_from('>H', received_data, 11 + other_urls + j)[0])
                        else:
                            continue

                        category = Category(category_id, url_length)
                        category_list.append(category)
                        j = j + CCSS

                    other_urls = other_urls + (TTN + (number_of_categories * CCSS))

    except Exception:
        logging.error(traceback.format_exc())

    return category_list


# create dgram udp socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
    logging.error('Failed to create socket')
    sys.exit()


def fls_vendor_lookup(url, uuid):
    categories_for_url = -1

    try:
        send_data, length_data = serialize_lookup_request(url, uuid)

        client_obj = FlsSocketClient(host=fls_host, tcp_port=fls_tcp_port, udp_port=fls_udp_port, tcp_timeout=4.0,
                                     udp_timeout=2.0)

        received_data = client_obj.get_response_using_hybrid(send_data=send_data, size=1024)

        categories_for_url = deserialize_detect_response(received_data)

    except Exception, ex:
        logging.error(ex)

    return categories_for_url