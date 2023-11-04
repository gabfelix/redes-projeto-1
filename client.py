#!/usr/bin/python3

"""
This module contains the implementation of an FTP client using Python's socket library.
It provides a class FtpClient that represents an FTP client and has methods to connect
to an FTP server, login, logout, list files in the current directory or a specific file,
and disconnect from the server.
It also defines several custom exceptions that can be raised during the execution of the client.
The client uses the colorama library to print debug messages in color.
"""

import socket
import errno
from contextlib import contextmanager
from colorama import Fore, Style


class FtpClient:
    """
    A class representing an FTP client.

    Attributes:
    - PORT: int - the default port for FTP connections
    - SOCKET_TIMEOUT: int - the timeout for socket connections in seconds
    - SOCKET_RCV_BYTES: int - the number of bytes to receive from a socket at a time

    Methods:
    - __init__(self, debug: bool = False) - initializes a new FtpClient instance
    - connect(self, host=None) - connects to an FTP server
    - disconnect(self) - disconnects from the FTP server
    - login(self, user, password) - logs in to the FTP server
    - logout(self) - logs out from the FTP server
    - list(self, filename=None) - lists the files in the current directory or a specific file
    """
    class Command():
        """
        A class that defines FTP commands as constants.
        """
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
        """
        A class that defines the status codes used in the FTP client.
        """
        LOGIN_SUCCESS = str.encode('230')
        LOGIN_FAIL = str.encode('530')
        FILE_NOT_FOUND = str.encode('550')

    class UnknownHost(Exception):
        """Exception raised when a host is not found."""

        def __init__(self):
            self.message = "Host not found"

        def __str__(self):
            return repr(self.message)

    class NotConnected(Exception):
        """
        Exception raised when attempting to perform an operation that requires a connection,
        but the client is not currently connected to a server.
        """

        def __init__(self):
            self.message = "Not connected"

        def __str__(self):
            return repr(self.message)

    class NotAuthenticated(Exception):
        """
        Exception raised when a user is not authenticated.
        """

        def __init__(self):
            self.message = "Not authenticated"

        def __str__(self):
            return repr(self.message)

    class ConnectionRefused(Exception):
        """Exception raised when a connection is refused by the server."""

        def __init__(self):
            self.message = "Connection refused"

        def __str__(self):
            return repr(self.message)

    class SocketTimeout(Exception):
        """Exception raised when a socket times out."""

        def __init__(self):
            self.message = "A socket has timed out"

        def __str__(self):
            return repr(self.message)

    class LocalIOError(Exception):
        """Exception raised when a local IO error occurs."""

        def __init__(self):
            self.message = "A local IO error has occurred"

        def __str__(self):
            return repr(self.message)

    PORT = 21
    SOCKET_TIMEOUT = 5  # in seconds
    SOCKET_RCV_BYTES = 4096

    def __init__(self, debug: bool = False):
        self._debug = debug
        self._command_socket = None
        self._data_socket = None
        self._data_port = None
        self._data_socket_is_connected = False

        self.host = None
        self.user = None
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

        if self._data_socket_is_connected:
            return

        self._send_command(FtpClient.Command.EPSV)
        data = self._receive_command_data()
        self._data_port = int(data.decode("utf-8").split("|")[3])

        try:
            self._data_socket.connect((self.host, self._data_port))
        except socket.gaierror as e:
            self._reset_sockets()
            raise FtpClient.UnknownHost from e
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                raise FtpClient.ConnectionRefused from e

        self._log(f'passive connection {Fore.GREEN}opened{Style.RESET_ALL} at '
                  f'{Fore.CYAN}{self.host}{Style.RESET_ALL}:'
                  f'{Fore.MAGENTA}{self._data_port}{Style.RESET_ALL}')
        self._data_socket_is_connected = True

    def _close_data_connection(self):
        self._data_socket.close()
        self._data_socket_is_connected = False
        self._reset_data_socket()
        self._data_port = None
        self._log(
            f'passive connection {Fore.RED}closed{Style.RESET_ALL}')

    @contextmanager
    def _data_connection(self):
        """
        A context manager for opening and closing a data connection.
        """
        self._open_data_connection()
        yield
        self._close_data_connection()

    def _read_from_data_connection(self):
        total_data = b''
        while True:
            data = self._data_socket.recv(FtpClient.SOCKET_RCV_BYTES)
            total_data += data
            if not data:
                break
        self._log(f'received data - {total_data}')
        return total_data

    def _write_to_data_connection(self, data):
        # TODO: Check if data connection is opened
        self._log(f'sending data - {data}')
        self._data_socket.sendall(data)
        self._data_socket.close()

    def list(self, filename=None):
        """
        Sends a LIST command to the server to retrieve a list of files
        in the current or specified directory.

        Args:
            filename (str, optional): The name of the directory to list.
            If not specified, the current directory is listed.

        Returns:
            str: The response from the server, including the list of files
            in the specified directory (if any).
        """

        self._is_connected()
        self._is_authenticated()

        with self._data_connection():
            if filename is not None:
                self._send_command(FtpClient.Command.LIST, filename)
            else:
                self._send_command(FtpClient.Command.LIST)

            data = self._receive_command_data()

            if not data.startswith(FtpClient.Status.FILE_NOT_FOUND):
                list_data = self._read_from_data_connection().decode(
                    "utf-8").replace('\\r\\n', '\n')
                data += list_data.encode() + self._receive_command_data()

        self._log(f'LIST data:\n{data.decode("utf-8")}')

        return data

    def pwd(self):
        """
        Sends a PWD command to the server to retrieve the current directory.
        """
        self._is_connected()
        self._is_authenticated()

        with self._data_connection():
            self._send_command(FtpClient.Command.PWD)
            data = self._receive_command_data().decode("utf-8")
            data = data.split('\"')[1]

        return data

    def cwd(self, directory):
        """
        Send CWD command to host.
        """
        self._is_connected()
        self._is_authenticated()

        self._send_command(FtpClient.Command.CWD, directory)
        data = self._receive_command_data()

        return data

    def cdup(self):
        """
        Send CDUP command to host.
        """
        self._is_connected()
        self._is_authenticated()

        self._send_command(FtpClient.Command.CDUP)
        data = self._receive_command_data()

        return data

    def mkd(self, directory):
        """
        Send MKD command to host.
        """
        self._is_connected()
        self._is_authenticated()

        self._send_command(FtpClient.Command.MKD, directory)
        data = self._receive_command_data()

        return data

    def dele(self, filename):
        """
        Send DELE command to host.
        """
        self._is_connected()
        self._is_authenticated()

        self._send_command(FtpClient.Command.DELE, filename)
        data = self._receive_command_data()

        return data

    def rm(self, filename):
        """
        An alias for dele().
        """
        self.dele(filename)

    def rmd(self, directory):
        """
        Send RMD command to host.
        """
        self._is_connected()
        self._is_authenticated()

        self._send_command(FtpClient.Command.RMD, directory)
        data = self._receive_command_data()

        return data

    def rmdir(self, directory):
        """
        An alias for rmd().
        """
        self.rmd(directory)

    def rename(self, old_filename, new_filename):
        """
        Send RNFR and RNTO commands to host.
        """
        self._is_connected()
        self._is_authenticated()

        self._send_command(FtpClient.Command.RNFR, old_filename)
        data = self._receive_command_data()
        if not data.startswith(FtpClient.Status.FILE_NOT_FOUND):
            self._send_command(FtpClient.Command.RNTO, new_filename)
            _ = self._receive_command_data()

    def _reset_data_socket(self):
        self._data_socket = socket.socket()
        self._data_socket.settimeout(FtpClient.SOCKET_TIMEOUT)

        self._data_socket_is_connected = False

    def connect(self, host=None):
        """
        Connect to the FTP server at the specified host.

        If a connection is already established, it will be reset before attempting to connect again.

        Args:
            host (str): The hostname or IP address of the FTP server to connect to.

        Raises:
            UnknownHost: If the specified host cannot be resolved to an IP address.
            ConnectionRefused: If the FTP server is not accepting connections.
        """

        if self.host is not None:
            self._reset_sockets()
        # FIXME: Handle errors correctly
        try:
            self._command_socket.connect((host, FtpClient.PORT))
            self.host = host
        except socket.gaierror as e:
            self._reset_sockets()
            raise FtpClient.UnknownHost from e
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                raise FtpClient.ConnectionRefused from e

        return self._receive_command_data()

    def disconnect(self):
        """
        Disconnects from the FTP server by sending the QUIT command and resetting sockets.

        Returns:
            The response data received from the server after sending the QUIT command.
        """

        self._is_connected()
        if self._is_authenticated():
            self.logout()
        self._send_command(FtpClient.Command.QUIT)
        data = self._receive_command_data()
        self._reset_sockets()

        return data

    def login(self, user, password):
        """
        Logs in to the FTP server with the given username and password.

        Args:
            user (str): The username to use for login.
            password (str): The password to use for login.

        Returns:
            str: The response message from the server after attempting to login.
        """
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
        """
        Logs out the current user by setting the `user` attribute to `None`.
        Raises an exception if the client is not connected or authenticated.
        """

        self._is_connected()
        self._is_authenticated()
        self._log(f'logging out {Fore.YELLOW}{self.user}{Style.RESET_ALL}')
        self.user = None

    def retrieve(self, filename, local_filename=None):
        """
        Retrieves the specified file from the server and saves it locally.
        """
        self._is_connected()
        self._is_authenticated()

        if local_filename is None:
            local_filename = filename

        with self._data_connection():
            self._send_command(FtpClient.Command.RETR, filename)
            data = self._receive_command_data()

            if not data.startswith(FtpClient.Status.FILE_NOT_FOUND):
                file_data = bytearray(self._read_from_data_connection())
                try:
                    # TODO: We must check that a sent file is binary or text,
                    # and open the file in the appropriate mode.
                    with open(local_filename, 'wb') as f:
                        f.write(file_data)
                except IOError as e:
                    raise FtpClient.LocalIOError from e

    def store(self, local_filename, filename=None):
        """
        Stores the specified file on the server.

        Note that local_filename and filename's order is reversed from the RETR command.
        """
        self._is_connected()
        self._is_authenticated()

        if filename is None:
            filename = local_filename

        with self._data_connection():
            try:
                with open(local_filename, 'rb') as local_file:
                    file_data = bytearray(local_file.read())
                    self._send_command(FtpClient.Command.STOR, filename)
                    _ = self._receive_command_data()
                    self._write_to_data_connection(file_data)
                    _ = self._receive_command_data()
            except IOError as e:
                raise FtpClient.LocalIOError from e

    def _send_command(self, command: str, *args: str):
        for arg in args:
            command += f' {arg}'
        try:
            self._log(
                f'sending command: {Fore.YELLOW}{command}{Style.RESET_ALL}')
            self._command_socket.sendall(str.encode(f'{command}\r\n'))
        except socket.timeout as e:
            raise FtpClient.SocketTimeout from e

    def _receive_command_data(self):
        data = self._command_socket.recv(FtpClient.SOCKET_RCV_BYTES)
        self._log(
            f'received command data - {Fore.BLUE}{data}{Style.RESET_ALL}')
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
client.list()
client.rename('TestUpload.kml', 'TestUpload2.kml')
client.list()
client.rename('TestUpload2.kml', 'TestUpload.kml')
client.disconnect()
