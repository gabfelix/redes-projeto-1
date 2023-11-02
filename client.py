#!/usr/bin/python3

import socket
import errno
from colorama import Fore, Style
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
        def __init__(self):
            self.message = "Host not found"

        def __str__(self):
            return(repr(self.message))

    class NotConnected(Exception):
        def __init__(self):
            self.message = "Not connected"

        def __str__(self):
            return(repr(self.message))

    class ConnectionRefused(Exception):
        def __init__(self):
            self.message = "Connection refused"

        def __str__(self):
            return(repr(self.message))
    
    class SocketTimeout(Exception):
        def __init__(self):
            self.message = "A socket has timed out"

        def __str__(self):
            return(repr(self.message))


    PORT = 21
    SOCKET_TIMEOUT = 5 # in seconds
    SOCKET_RCV_BYTES = 4096


    def __init__(self, debug: bool = False):
        self._debug = debug
        self._reset_sockets()

    def _log(self, msg: str):
        msg = f'{Fore.GREEN}[DEBUG]{Style.RESET_ALL} {msg}'
        if self._debug:
           print(msg) 

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
                raise FtpClient.ConnectionRefused

        return self._receive_command_data()

    def disconnect(self):
        self._check_connection()
        self._send_command(FtpClient.Command.QUIT)
        data = self._receive_command_data()
        self._reset_sockets()

        return data


    def _send_command(self, command: str, *args: str):
        for arg in args:
            command = f'{command} {arg}'
        try:
            self._log(f'sending command: {Fore.YELLOW}{command}{Style.RESET_ALL}')
            self._command_socket.sendall(str.encode(f'{command}\r\n'))
        except socket.timeout:
            raise FtpClient.SocketTimeout

    def _receive_command_data(self):
        data = self._command_socket.recv(FtpClient.SOCKET_RCV_BYTES)
        self._log(f'received command data - {Fore.BLUE}{data}{Style.RESET_ALL}')
        return data

    def _check_connection(self):
        if self.host is None:
            raise FtpClient.NotConnected

client = FtpClient(debug=True)
client.connect(host='ftp.dlptest.com')
client.disconnect()
