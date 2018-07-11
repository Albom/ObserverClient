#!/usr/bin/python3
from PyQt5 import QtCore
from datetime import datetime
from smtplib import SMTP_SSL
from email.message import EmailMessage
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

# https://gist.github.com/turicas/1455741

class ThreadMail(QtCore.QThread):
    """class ThreadMail"""
    mailReceived = QtCore.pyqtSignal(str, str)
    mailFailed = QtCore.pyqtSignal(str, datetime, str)         

    # def __init__(self, username, password, address):
    def __init__(self):
        """__init__()"""
        super().__init__()
        self.username = ''
        self.password = ''
        self.address = ''
        if not self.username or not self.password or not self.address:
            raise ValueError('Empty email username, password or address!')
        self.url = 'smtp.gmail.com'
        self.port = 465


    def set_path(self, pathData, currentDate):
        self.path = '{0}\\{1}\\{2}\\{3}'.format(pathData, currentDate.strftime('%Y'), currentDate.strftime('%m'), currentDate.strftime('%d'))
        self.name = currentDate.strftime('%Y.%m.%d')

    def run(self):
        """run() - основная функция потока."""
        begin = datetime.now()
        # message = EmailMessage()
        message = MIMEMultipart()
        message['From'] = self.username
        message['To'] = self.address
        message['Subject'] = 'Мониторинг радара.'
        # message.set_content(self.name)
        try:
            # file_name = '{}\\{}.png'.format(self.path, self.name)
            with open('{}\\{}.png'.format(self.path, self.name), 'rb') as file:
                img = file.read()
                img = MIMEImage(img)
                img.add_header('Content-Disposition', 'attachment', filename='{}.png'.format(self.name))
                # message.add_attachment(img)
                message.attach(img)
                with SMTP_SSL(self.url, self.port, timeout=10) as server:
                    server.ehlo()
                    server.login(self.username, self.password)
                    server.send_message(message)
                end = datetime.now()
                self.mailReceived.emit('Email sent.', self.deltaTimeStr(begin, end))
        except Exception as e:
            print(e)
            end = datetime.now()
            self.mailFailed.emit('Email don`t sent!', begin, self.deltaTimeStr(begin, end))

    def deltaTimeStr(self, begin, end):
        """deltaTimeStr(begin, end) - вернуть разницу во времени в строковом виде."""
        delta = end - begin
        deltaStr = str(delta.total_seconds())
        delimeter = deltaStr.find('.')
        if delimeter < (len(deltaStr) - 2):
            deltaStr = deltaStr[0:(delimeter + 2)]
        return deltaStr
