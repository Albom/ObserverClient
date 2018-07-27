# Copyright © 2018 Stanislav Hnatiuk.  All rights reserved.

# !/usr/bin/env python3

from PyQt5 import QtCore
import requests
from datetime import datetime
import psutil


class ThreadServer(QtCore.QThread):
    """Поток получения информации о ресурсах компьютера."""
    # Сигнал получения запроса
    requestReceived = QtCore.pyqtSignal(list, str, str, datetime)
    # Сигнал ошибки
    requestFailed = QtCore.pyqtSignal(str, str, datetime)

    def __init__(self):
        """Инициализация потока."""
        super().__init__()
        self.address = 'localhost'

    def run(self):
        """Основная функция потока."""
        try:
            timeBegin = datetime.now()

            cpu = psutil.cpu_percent(10)
            disk = psutil.disk_usage('/').percent
            mem = psutil.virtual_memory().percent
            temp = ['4301 {}'.format(cpu),
                    '4801 {}'.format(disk),
                    '5201 {}'.format(mem)]

            timeEnd = datetime.now()
            delta = self.deltaTimeStr(timeBegin, timeEnd)
            self.requestReceived.emit(temp, self.address, delta, timeBegin)
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
