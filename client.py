#!/usr/bin/python3

import socket
import errno
import colorama
from enum import Enum

class FtpClient(object):
    class Command():
        LIST = 'LIST'
        USER = 'USER'
        PASS = 'PASS'
        EPRT = 'EPRT'
        QUIT = 'QUIT'
        RETR = 'RETR'
        STOR = 'STOR'
        PWD = 'PWD'
        CWD = 'CWD'
        CDUP = 'CDUP'
        MKD = 'MKD'
        DELE = 'DELE'
        RMD = 'RMD'
        RNFR = 'RNFR'
        RNTO = 'RNTO'

    class Status():
        STATUS_230 = '230'
        STATUS_550 = '550'
        STATUS_530 = '530'

    class UnknownHost(Exception):
        f'Connection failed. Host unreachable.'
        pass

    PORT = 21
    SOCKET_TIMEOUT = 5 # in seconds
    SOCKET_RCV_BYTES = 4096


    def __init__(self):
        self._reset_sockets()

    def _reset_sockets(self):
        self._reset_command_socket()
        self._reset_data_socket()
        self.host = None
        self.user = None

    def _reset_command_socket(self):
        if getattr(self, 'host', None) is not None:
            self._command_socket.close()
        self._command_socket = socket.socket()
        self._command_socket.settimeout(FtpClient.SOCKET_TIMEOUT)

    def _reset_data_socket(self):
        if getattr(self, '_data_socket_listening', False):
            self._data_socket.close()
        self._data_socket = socket.socket()
        self._data_socket_listening = False

    def connect(self, host=None):
        if self.host is not None:
            self._reset_sockets()

         # FIXME: Handle errors correctly
        try:
            self._command_socket.connect((host, FtpClient.PORT))
            self.host = host
        except socket.gaierror:
            self._reset_sockets()
            raise FtpClient.UnknownHost
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                exit(1)

        return self._receive_command_data()

    def _receive_command_data(self):
        data = self._command_socket.recv(FtpClient.SOCKET_RCV_BYTES)
        print(f'received command data - {data}')
        return data

client = FtpClient()
client.connect(host='ftp.dlptest.com')
if client.host is None:
    print('Connection failed')
client._reset_sockets()
