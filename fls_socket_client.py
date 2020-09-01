import socket
import traceback
import time
import logging


logger = logging.getLogger('main')


def fls_timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        return ret

    return wrap


class FlsSocketClient:
    def __init__(self, host, tcp_port, udp_port, tcp_timeout, udp_timeout):
        self.host = host
        self.host_ip = socket.gethostbyname(self.host)
        self.tcp_port = tcp_port
        self.tcp_timeout = tcp_timeout
        self.udp_timeout = udp_timeout
        self.udp_port = udp_port
        self.tcp_sock = None
        self.udp_sock = None

    def refresh_tcp_connection(self):
        self.close_tcp_socket()
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.settimeout(self.tcp_timeout)

    def refresh_udp_instance(self):
        self.close_udp_socket()
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.settimeout(self.udp_timeout)

    def connect_tcp(self):
        self.refresh_tcp_connection()
        self.tcp_sock.connect((self.get_ip(), self.tcp_port))

    def send_tcp_data(self, send_data):
        self.connect_tcp()
        self.tcp_sock.sendall(send_data)

    def receive_tcp_response(self, size):
        return self.tcp_sock.recv(size)

    def close_tcp_socket(self):
        if self.tcp_sock is not None:
            try:
                self.tcp_sock.close()
            except:
                logger.error("FlsSocketClient - Problem while closing tcp socket")

    def send_udp_data(self, send_data):
        self.refresh_udp_instance()
        self.udp_sock.sendto(send_data, (self.get_ip(), self.udp_port))

    def receive_udp_response(self, size):
        return self.udp_sock.recvfrom(size)

    def close_udp_socket(self):
        if self.udp_sock is not None:
            try:
                self.udp_sock.close()
            except:
                logger.error("FlsSocketClient - Problem while closing udp socket")

    def get_ip(self):
        return self.host_ip

    @fls_timing
    def get_response_using_hybrid(self, send_data, size):
        data = -1
        for step in range(1, 4):
            try:
                self.send_udp_data(send_data)
                data, addr = self.receive_udp_response(size)
                break
            except:
                logger.error("get_response_using_hybrid {} - UDP Connection error in step: ".format(self.host_ip) + "\n"
                             + traceback.format_exc())
            finally:
                self.close_udp_socket()
        if data == -1:
            try:
                self.send_tcp_data(send_data)
                data = self.receive_tcp_response(size)
            except:
                logger.error("get_response_using_hybrid {} - TCP Connection error".format(self.host_ip) + "\n" +
                             traceback.format_exc())
            finally:
                self.close_tcp_socket()

        if data == -1:
            logger.info("get_response_using_hybrid - " + " verdict is -1")
        else:
            logger.info("get_response_using_hybrid {} - Successfully received data from ".format(self.host_ip))
        return data
