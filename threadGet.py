# Copyright © 2018 Stanislav Hnatiuk.  All rights reserved.

# !/usr/bin/env python3

from PyQt5 import QtCore
import requests
from datetime import datetime


class ThreadGet(QtCore.QThread):
    """Поток отправки запроса."""
    # Сигнал получения запроса
    requestReceived = QtCore.pyqtSignal(list, str, str, datetime)
    # Сигнал ошибки
    requestFailed = QtCore.pyqtSignal(str, str, datetime)

    def __init__(self, address):
        """Инициализация потока."""
        super().__init__()
        self.address = address

    def run(self):
        """Основная функция потока."""
        try:
            timeBegin = datetime.now()
            request = requests.get(
                'http://{0}'.format(self.address), timeout=(10, 10))
            timeEnd = datetime.now()
            delta = self.deltaTimeStr(timeBegin, timeEnd)
            if request.status_code == 200:
                if len(request.text) > 0:
                    temp = request.text.split('\n')
                    try:
                        temp.remove('')
                    except Exception:
                        pass
                    self.requestReceived.emit(
                        temp, self.address, delta, timeBegin)
            elif int(request.status_code / 100) == 1:
                print("{0}: Informational".format(request.status_code))
            elif int(request.status_code / 100) == 2:
                print("{0}: Success".format(request.status_code))
            elif int(request.status_code / 100) == 3:
                print("{0}: Redirection ".format(request.status_code))
            elif int(request.status_code / 100) == 4:
                print("{0}: Client Error".format(request.status_code))
            elif int(request.status_code / 100) == 5:
                print("{0}: Server Error".format(request.status_code))

        except requests.RequestException:
            timeEnd = datetime.now()
            delta = self.deltaTimeStr(timeBegin, timeEnd)
            self.requestFailed.emit(self.address, delta, timeBegin)

    def deltaTimeStr(self, begin, end):
        """Вернуть строкой разницу во времени"""
        delta = end - begin
        deltaStr = str(delta.total_seconds())
        delimeter = deltaStr.find('.')
        if delimeter < (len(deltaStr) - 2):
            deltaStr = deltaStr[0:(delimeter + 2)]
        return deltaStr
