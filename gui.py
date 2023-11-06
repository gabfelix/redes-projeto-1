#!/usr/bin/python3

import PySide6.QtGui
from PySide6.QtCore import QThread
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QPushButton, QTextEdit,
                               QVBoxLayout, QWidget)

from client import FtpClient


class HorizontalForm(QWidget):
    layout : QLineEdit

    def __init__(self, label_text : str | None = None, placeholder_text: str | None = None, is_password=False):
        super().__init__()

        self.layout = QHBoxLayout()

        if label_text is None or len(label_text) > 0:
            self.label = QLabel(label_text)
            self.layout.addWidget(self.label)

        self.placeholder_text = ''

        self.textbox = QLineEdit()
        if is_password:
            self.textbox.setEchoMode(QLineEdit.Password)
        if placeholder_text is not None and len(placeholder_text) > 0:
            self.textbox.setPlaceholderText(placeholder_text)
            self.placeholder_text = placeholder_text
        self.layout.addWidget(self.textbox)

    def text(self):
        if len(self.textbox.text()) == 0:
            return self.placeholder_text
        return self.textbox.text()

    def set_text(self, to : str):
        return self.textbox.setText(to)

class FTPClientGUI(QMainWindow):
    def __init__(self, debug: bool = False):
        super().__init__()

        self._debug = debug

        window_title = "FTP Client"
        if self._debug:
            window_title += " (Debug)"
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 600, 400)  # Set the initial window size

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        placeholder_hostname = None
        if self._debug:
            placeholder_hostname = "ftp.dlptest.com"
        self.hostname_form = HorizontalForm("Hostname:", placeholder_text=placeholder_hostname)
        layout.addLayout(self.hostname_form.layout)

        placeholder_user = None
        if self._debug:
            placeholder_user = "dlpuser"
        self.user_form = HorizontalForm("Usuário:", placeholder_text=placeholder_user)
        layout.addLayout(self.user_form.layout)

        placeholder_password = None
        if self._debug:
            placeholder_password = "rNrKYTX9g7z3RgJRmxWuGHbeu"
        self.password_form = HorizontalForm("Senha:", placeholder_text=placeholder_password, is_password=True)
        layout.addLayout(self.password_form.layout)

        button_style = "QPushButton { background-color: #4CAF50; color: white; border: none; padding: 10px; }" \
                       "QPushButton:hover { background-color: #45a049; }"

        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.handle_connect)
        self.connect_button.setStyleSheet(button_style)
        layout.addWidget(self.connect_button)

        self.login_button = QPushButton("Entrar")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setStyleSheet(button_style)
        layout.addWidget(self.login_button)

        self.list_button = QPushButton("Listar")
        self.list_button.clicked.connect(self.handle_list)
        self.list_button.setStyleSheet(button_style)
        layout.addWidget(self.list_button)

        filename_layout = QHBoxLayout()
        self.filename_label = QLabel("Arquivo:")
        self.filename_input = QLineEdit()
        filename_layout.addWidget(self.filename_label)
        filename_layout.addWidget(self.filename_input)
        layout.addLayout(filename_layout)

        button_style_secondary = "QPushButton { background-color: #008CBA; color: white; border: none; padding: 10px; }" \
                                 "QPushButton:hover { background-color: #007a99; }"

        self.retrieve_button = QPushButton("Recuperar")
        self.retrieve_button.clicked.connect(self.handle_retrieve)
        self.retrieve_button.setStyleSheet(button_style_secondary)
        layout.addWidget(self.retrieve_button)

        self.store_button = QPushButton("Armazenar")
        self.store_button.clicked.connect(self.handle_store)
        self.store_button.setStyleSheet(button_style_secondary)
        layout.addWidget(self.store_button)

        self.clear_button = QPushButton("Limpar")
        self.clear_button.clicked.connect(self.handle_clear)
        self.clear_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; border: none; padding: 10px; }"
                                        "QPushButton:hover { background-color: #d32f2f; }")
        layout.addWidget(self.clear_button)

        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)

        layout.addWidget(self.message_display)

        central_widget.setLayout(layout)

        self.client = FtpClient(self._debug)

    def handle_connect(self):
        response = self.client.connect(self.hostname_form.text())
        self.message_display.append(response.decode("utf-8"))

    def handle_login(self):
        user = self.user_form.text()
        password = self.password_form.text()
        if len(user) == 0 or len(password) == 0:
            return
        response = self.client.login(user, password)
        self.message_display.append(response.decode("utf-8"))

    def handle_list(self):
        response = self.client.list()
        self.message_display.append(response.decode("utf-8"))

    def handle_retrieve(self):
        filename = self.filename_input.text()

        thread = RetrieveThread(self, filename)
        thread.setParent(self)
        thread.start()

    def handle_store(self):
        filename = self.filename_input.text()

        thread = StoreThread(self, filename)
        thread.setParent(self)
        thread.start()

    def handle_clear(self):
        self.message_display.clear()

    def closeEvent(self, _):
        self.client.disconnect()

class StoreThread(QThread):
    def __init__(self, window: FTPClientGUI, filename: str):
        super().__init__()
        self._window = window
        self._filename = filename

    def run(self):
        response = self._window.client.store(self._filename)
        self._window.message_display.append(response.decode("utf-8"))

class RetrieveThread(QThread):
    def __init__(self, window: FTPClientGUI, filename: str):
        super().__init__()
        self._window = window
        self._filename = filename

    def run(self):
        response = self._window.client.retrieve(self._filename)
        self._window.message_display.append(response.decode("utf-8"))

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet("QMainWindow{background-color: #f2f2f2;}"  # Set the background color of the main window
                      "QLabel{color: #333; font-size: 16px;}"  # Style for labels
                      "QLineEdit{padding: 8px;}"  # Style for line edits
                      "QTextEdit{padding: 8px;}")
    window = FTPClientGUI(debug=True)
    window.show()
    app.exec()
