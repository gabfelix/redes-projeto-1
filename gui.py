#!/usr/bin/python3

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QPushButton, QTextEdit,
                               QVBoxLayout, QWidget)

from client import FtpClient


class FTPClientGUI(QMainWindow):
    def __init__(self, debug: bool = False):
        super().__init__()

        self._debug = debug

        self.setWindowTitle("FTP Client")
        self.setGeometry(100, 100, 600, 400)  # Set the initial window size

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

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

        directory_layout = QHBoxLayout()
        self.directory_label = QLabel("Diretório:")
        self.directory_input = QLineEdit()
        directory_layout.addWidget(self.directory_label)
        directory_layout.addWidget(self.directory_input)
        layout.addLayout(directory_layout)

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
        layout.addWidget(self.message_display)

        central_widget.setLayout(layout)

        self.client = FtpClient(self._debug)

        # FIXME: This will change after removing server hardcode
        if self._debug:
            self.connect_button.click()
            self.login_button.click()

    def handle_connect(self):
        response = self.client.connect(host='ftp.dlptest.com')
        self.message_display.append(response.decode("utf-8"))

    def handle_login(self):
        response = self.client.login(user="dlpuser", password="rNrKYTX9g7z3RgJRmxWuGHbeu")
        self.message_display.append(response.decode("utf-8"))

    def handle_list(self):
        response = self.client.list()
        self.message_display.append(response.decode("utf-8"))

    def handle_retrieve(self):
        #directory = self.directory_input.text()
        filename = self.filename_input.text()

        thread = FTPClientGUI.RetrieveThread(self.client, filename)
        thread.start()

    def handle_store(self):
        directory = self.directory_input.text()
        filename = self.filename_input.text()

        class StoreThread(QThread):
            def run(self):
                response = self.client.store(filename, directory)
                self.message_display.append(response.decode("utf-8"))

        thread = StoreThread(self)
        thread.start()

    def handle_clear(self):
        self.message_display.clear()

if __name__ == "__main__":
    app = QApplication([])
    app.setStyleSheet("QMainWindow{background-color: #f2f2f2;}"  # Set the background color of the main window
                      "QLabel{color: #333; font-size: 16px;}"  # Style for labels
                      "QLineEdit{padding: 8px;}"  # Style for line edits
                      "QTextEdit{padding: 8px;}")
    window = FTPClientGUI(debug=True)
    window.show()
    app.exec()
