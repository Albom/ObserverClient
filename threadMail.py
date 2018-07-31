# Copyright © 2018 Stanislav Hnatiuk.  All rights reserved.

# !/usr/bin/env python3

import os
from PyQt5 import QtCore
from datetime import datetime
from smtplib import SMTP_SSL
from email.message import EmailMessage
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


class EmailInfo:
    """Информация об имейлах."""
    def __init__(self, address, mode, times):
        """Инициализация EmailInfo:
        
        address - адрес получателя;
        
        mode - режим отправки ('C' - текущие неполные сутки,
        'P' предыдущие полные сутки);
        
        times - список значений времени отправления в виде строк."""

        def split(time):
            """Разделение времени в виде строки на числовой кортёж."""
            temp = time.split(':')
            return (int(temp[0]), int(temp[1]))

        self.address = address
        self.mode = mode[0].upper() == 'C'
        self.times = tuple([split(time) for time in times])

    def check(self, interval, now):
        """Проверка времени отправки имейла на соответствие интервалу
        в текущем времени."""
        for tt in self.times:
            min_time = datetime(now.year, now.month, now.day, tt[0], tt[1], 0)
            max_time = datetime(
                now.year,
                now.month,
                now.day,
                tt[0] + int(int(tt[1] + interval / 60) / 60),
                (tt[1] + int(interval / 60)) % 60,
                interval % 60
            )
            if (now >= min_time) and (now < max_time):
                return True
        return False

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        # print(self.times)
        return '{} {}'.format(self.address, self.mode)


# https://gist.github.com/turicas/1455741
class ThreadMail(QtCore.QThread):
    """Поток отправки имейлов."""
    mailReceived = QtCore.pyqtSignal(str, str)
    mailFailed = QtCore.pyqtSignal(str, datetime, str)

    def __init__(self, path):
        """Инициализация потока с указанием пути файла настрйоик имейлов."""
        super().__init__()
        self.config = path
        self.info_list = []
        self.configRead()

        if not self.username or not self.password:
            raise ValueError('Empty email username, password or address!')
        self.url = 'smtp.gmail.com'
        self.port = 465

    def configRead(self):
        """Считать настройки модуля Email."""
        if os.path.exists(self.config):
            try:
                with open(self.config, 'tr') as file:
                    line = file.readline()
                    line = line.replace('\n', '')
                    temp = line.split(';')
                    self.username = temp[0]
                    self.password = temp[1]

                    for line in file:
                        line = line.replace('\n', '')
                        temp = line.split(';')
                        if len(temp) >= 3:
                            self.info_list.append(
                                EmailInfo(temp[0], temp[1], tuple(temp[2:])))
            except Exception as error:
                print(error)

    def set_path(self, pathData, currentDate, prevDate, interval):
        """Задание текущей и предыдущей дат для отправки соответствующего 
        графика."""
        self.path = '{0}\\{1}\\{2}\\{3}'.format(
            pathData,
            currentDate.strftime('%Y'),
            currentDate.strftime('%m'),
            currentDate.strftime('%d'))
        self.name = currentDate.strftime('%Y.%m.%d')
        self.prevPath = '{0}\\{1}\\{2}\\{3}'.format(
            pathData,
            prevDate.strftime('%Y'),
            prevDate.strftime('%m'),
            prevDate.strftime('%d'))
        self.prevName = prevDate.strftime('%Y.%m.%d')
        self.interval = interval

    def run(self):
        """Основная функция потока."""
        begin = datetime.now()
        for info in self.info_list:
            if info.check(self.interval, begin):
                message = MIMEMultipart()
                message['From'] = self.username
                message['To'] = info.address
                message['Subject'] = 'Мониторинг радара.'
                try:
                    if info.mode:
                        path = self.path
                        name = self.name
                    else:
                        path = self.prevPath
                        name = self.prevName
                    with open('{}\\{}.pdf'.format(path, name), 'rb') as file:
                        img = file.read()
                        # img = MIMEImage(img)
                        img = MIMEApplication(img)
                        img.add_header(
                            'Content-Disposition',
                            'attachment',
                            filename='{}.pdf'.format(self.name))
                        message.attach(img)
                        with SMTP_SSL(self.url, self.port, timeout=10) as serv:
                            serv.ehlo()
                            serv.login(self.username, self.password)
                            serv.send_message(message)
                        end = datetime.now()
                        self.mailReceived.emit(
                            'Email sent.',
                            self.deltaTimeStr(begin, end))
                except Exception as e:
                    print(e)
                    end = datetime.now()
                    self.mailFailed.emit(
                        'Email don`t sent!',
                        begin,
                        self.deltaTimeStr(begin, end))

    def deltaTimeStr(self, begin, end):
        """Вернуть строкой разницу во времени"""
        delta = end - begin
        deltaStr = str(delta.total_seconds())
        delimeter = deltaStr.find('.')
        if delimeter < (len(deltaStr) - 2):
            deltaStr = deltaStr[0:(delimeter + 2)]
        return deltaStr
