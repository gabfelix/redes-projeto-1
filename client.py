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
        EPSV = 'EPSV'
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

    # More on these codes at:
    # https://en.wikipedia.org/wiki/List_of_FTP_server_return_codes
    class Status():
        LOGIN_SUCCESS = str.encode('230')
        LOGIN_FAIL = str.encode('530')
        FILE_NOT_FOUND = str.encode('550')

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
    
    class NotAuthenticated(Exception):
        def __init__(self):
            self.message = "Not authenticated"

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

    def _open_data_connection(self):
        self._is_connected()
        self._is_authenticated()

        self._send_command(FtpClient.Command.EPSV)
        data = self._receive_command_data()
        self._data_port = int(data.decode("utf-8").split("|")[3])

        try:
            self._data_socket.connect((self.host, self._data_port))
        except socket.gaierror:
            self._reset_sockets()
            raise FtpClient.UnknownHost
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                raise FtpClient.ConnectionRefused

        self._log(f'passive connection established at {Fore.CYAN}{self.host}{Style.RESET_ALL}:{Fore.MAGENTA}{self._data_port}{Style.RESET_ALL}')
        self._data_socket_is_connected = True
        
    def _reset_data_socket(self):
        self._data_socket = socket.socket()
        self._data_socket.settimeout(FtpClient.SOCKET_TIMEOUT)
        self._data_socket_is_connected = False

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
        self._is_connected()
        self._send_command(FtpClient.Command.QUIT)
        data = self._receive_command_data()
        self._reset_sockets()

        return data

    def login(self, user, password):
        self._is_connected()
        self._send_command(FtpClient.Command.USER, user)
        _ = self._receive_command_data()
        self._send_command(FtpClient.Command.PASS, password)
        data = self._receive_command_data()

        if data.startswith(FtpClient.Status.LOGIN_SUCCESS):
            self.user = user
        elif data.startswith(FtpClient.Status.LOGIN_FAIL):
            self.user = None

        return data

    def logout(self):
        self._is_connected()
        self._is_authenticated()
        self._log(f'logging out {Fore.YELLOW}{self.user}{Style.RESET_ALL}')
        self.user = None

    def _send_command(self, command: str, *args: str):
        for arg in args:
            command += f' {arg}'
        try:
            self._log(f'sending command: {Fore.YELLOW}{command}{Style.RESET_ALL}')
            self._command_socket.sendall(str.encode(f'{command}\r\n'))
        except socket.timeout:
            raise FtpClient.SocketTimeout

    def _receive_command_data(self):
        data = self._command_socket.recv(FtpClient.SOCKET_RCV_BYTES)
        self._log(f'received command data - {Fore.BLUE}{data}{Style.RESET_ALL}')
        return data

    def _is_connected(self):
        if self.host is None:
            raise FtpClient.NotConnected

    def _is_authenticated(self):
        if self.user is None:
            raise FtpClient.NotAuthenticated

client = FtpClient(debug=True)
client.connect(host='ftp.dlptest.com')
client.login(user="dlpuser", password="rNrKYTX9g7z3RgJRmxWuGHbeu")
client._open_data_connection()
client.logout()
client.disconnect()
