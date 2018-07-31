# Copyright © 2018 Stanislav Hnatiuk.  All rights reserved.

# !/usr/bin/env python3

import requests
import os
from PyQt5 import QtCore
from datetime import datetime, timedelta

import threadGet
import threadServer
import threadChart
import threadMail
import time
import sensor


class Observer(QtCore.QObject):
    """Логическое ядро программы."""
    logged = QtCore.pyqtSignal(str, str)
    dataAdded = QtCore.pyqtSignal()

    def __init__(self):
        """Инициализация параметров программы по умолчанию."""
        QtCore.QObject.__init__(self)
        self.pathAddresses = "config/addresses"
        self.pathConfig = "config/config"
        self.pathEmails = 'config/emails'
        self.pathFolder = 'config'
        self.pathData = "data"
        self.pathSensors = "config/sensors"
        self.currentDate = datetime.now()
        self.prevDate = datetime(
            self.currentDate.year,
            self.currentDate.month,
            self.currentDate.day - 1
        )
        self.addresses = {}
        self.sensors = {}
        self.groups = {}
        self.period = 60
        self.countPeriod = 2
        self.threads = []

        self.email = threadMail.ThreadMail(self.pathEmails)
        self.email.mailReceived.connect(self.mailReceivedEvent)
        self.email.mailFailed.connect(self.mailFailedEvent)

        self.chart = threadChart.ThreadChart()
        self.chart.chartSaved.connect(
            self.onChartSaved,
            QtCore.Qt.QueuedConnection
        )

        self.timerRequests = QtCore.QTimer()
        self.timerRequests.timeout.connect(self.timerRequestsEvent)
        self.timerChart = QtCore.QTimer()
        self.timerChart.timeout.connect(self.timerChartEvent)
        self.read()

    def start(self):
        """Запустить мониторинг и таймеры."""
        if not (self.timerRequests.isActive() and self.timerChart.isActive()):
            now = datetime.now()
            self.checkCurrentDay(now)
            self.configSave()
            self.logged.emit(
                '{} Observation started'.format(now.strftime('%H:%M:%S')),
                'lf'
            )
            self.read()
            self.timerRequests.start(int(self.period) * 1000)
            self.timerChart.start(int(self.period) * 1000 * self.countPeriod)
            self.timerRequestsEvent()

    def stop(self):
        """Остановить мониторинг и таймеры."""
        if self.timerRequests.isActive() and self.timerChart.isActive():
            self.timerRequests.stop()
            self.timerChart.stop()
            text = '{} Observation stopped.'.format(
                datetime.now().strftime('%H:%M:%S')
            )
            self.logged.emit('\n{}'.format(text), 'l')
            self.logged.emit(text, 'f')

    def timerRequestsEvent(self):
        """Событие таймера запросов."""
        self.sendRequests()

    def timerChartEvent(self):
        """Событие таймера рисования графиков."""
        self.draw()

    def checkCurrentDay(self, date):
        """Проверить и изменить текущую дату."""
        if self.currentDate.date() != date.date():
            self.draw()
            # self.send_mail()
            self.prevDate = self.currentDate
            self.currentDate = date
            self.logged.emit(
                'New day {}.'.format(self.currentDate.strftime('%Y.%m.%d')),
                'l'
            )

    def sendRequests(self):
        """Отправить запросы."""
        for key in self.sensors.keys():
            self.sensors[key].value = None

        self.requestsCount = len(self.addresses)
        self.requestsFailedCount = 0
        timeBegin = datetime.now()
        self.logged.emit(
            '{0} Sending requests\n'.format(timeBegin.strftime('%H:%M:%S')),
            'l'
        )
        self.logged.emit('Sending requests...', 's')
        self.checkCurrentDay(timeBegin)
        for address in self.addresses:
            self.get(address)
        self.getServer()

    def configRead(self):
        """Считать из файла настройки приложения."""
        if os.path.exists(self.pathConfig):
            try:
                with open(self.pathConfig, 'tr') as file:
                    for line in file:
                        line = line.replace('\n', '')
                        line = line.replace(' = ', '=')
                        temp = line.split('=')
                        if len(temp) == 2:
                            if temp[0] == 'currentDate':
                                self.currentDate = datetime.today()
                                t = temp[1].split('.')
                                self.currentDate = self.currentDate.replace(
                                    int(t[0]),
                                    int(t[1]),
                                    int(t[2])
                                )
                            elif temp[0] == 'prevDate':
                                t = temp[1].split('.')
                                self.prevDate = self.prevDate.replace(
                                    int(t[0]),
                                    int(t[1]),
                                    int(t[2])
                                )
                            elif temp[0] == "pathAddresses":
                                self.pathAddresses = temp[1]
                            elif temp[0] == "pathData":
                                self.pathData = temp[1]
                            elif temp[0] == "pathSensors":
                                self.pathSensors = temp[1]
                            elif temp[0] == "period":
                                self.period = temp[1]
                    file.close()
            except Exception as error:
                self.logged.emit(
                    '{} Config not readed from "{}"!'.format(
                        datetime.now().strftime('%H:%M:%S'),
                        self.pathConfig
                    ),
                    'lsf'
                )
        else:
            self.configSave()

    def configSave(self):
        """Сохранить в файл настройки приложения."""
        if not os.path.exists(self.pathFolder):
            os.makedirs(self.pathFolder, 0o777, True)
        try:
            with open(self.pathConfig, 'w', encoding="utf-8") as file:
                file.write(
                    'currentDate = {}\n'.format(
                        self.currentDate.strftime('%Y.%m.%d')
                    )
                )
                file.write(
                    'prevDate = {}\n'.format(
                        self.prevDate.strftime('%Y.%m.%d')))
                file.write(
                    "pathAddresses = {}\n".format(self.pathAddresses))
                file.write(
                    "pathData = {}\n".format(self.pathData))
                file.write("pathSensors = {}\n".format(self.pathSensors))
                file.write("period = {}".format(self.period))
                file.close()
        except Exception as error:
            self.logged.emit(
                '{} Config not saved to "{}"!'.format(
                    datetime.now().strftime('%H:%M:%S'), self.pathConfig),
                'lsf')

    def addressesRead(self):
        """Считать из файла адреса модулей."""
        if os.path.exists(self.pathAddresses):
            try:
                with open(self.pathAddresses, 'r', encoding="utf-8") as file:
                    for line in file:
                        line = line.replace('\n', '')
                        line = line.replace(' = ', '=')
                        temp = line.split('=')
                        if len(temp) > 1:
                            self.addresses[temp[0]] = temp[1]
                        else:
                            self.addresses[temp[0]] = 'No name'
                file.close()
            except Exception as error:
                self.logged.emit(
                    '{} Addresses not readed from "{}"!'.format(
                        datetime.now().strftime('%H:%M:%S'),
                        self.pathAddresses),
                    'lsf')
        else:
            os.makedirs(self.pathFolder, 0o777, True)

    def addressesSave(self):
        """Сохранить в файл адреса модулей."""
        if not os.path.exists(self.pathFolder):
            os.makedirs(self.pathFolder, 0o777, True)
        try:
            if len(self.addresses) != 0:
                with open(self.pathAddresses, 'w', encoding="utf-8") as file:
                    for key in self.addresses.keys():
                        file.write(
                            "{0} = {1}\n".format(key, self.addresses[key]))
                    file.close()
        except Exception:
            self.logged.emit(
                '{} Addresses not saved to "{}"!'.format(
                    datetime.now().strftime('%H:%M:%S'), self.pathSensors),
                'lsf')

    def sensorsRead(self):
        """Считать датчики из файла."""
        if os.path.exists(self.pathSensors):
            try:
                fileList = os.listdir(self.pathSensors)
                self.sensors.clear()
                self.groups.clear()
                for fileName in fileList:
                    with open(
                        '{}/{}'.format(self.pathSensors, fileName),
                        'r',
                        encoding="utf-8"
                    ) as file:
                        for line in file:
                            line = line.replace('\n', '')
                            line = line.replace(' = ', '=')
                            temp = line.split('=')
                            if len(temp) > 1:
                                name = temp[1]
                            else:
                                name = 'No name'
                            ss = sensor.Sensor(temp[0], file, name)
                            self.sensors[temp[0]] = ss
                            if fileName in self.groups:
                                self.groups[fileName].add(ss)
                            else:
                                self.groups[fileName] = {ss}
                        file.close()
            except Exception:
                self.logged.emit(
                    '{} Sensors not readed from "{}"!'.format(
                        datetime.now().strftime('%H:%M:%S'),
                        self.pathSensors),
                    'lsf')
        else:
            os.makedirs(self.pathSensors, 0o777, True)

    def sensorsSave(self):
        """Сохранить датчики в файл."""
        if not os.path.exists(self.pathSensors):
            os.makedirs(self.pathSensors, 0o777, True)
        try:
            if len(self.sensors) != 0:
                for group, sens in self.groups.items():
                    with open(
                        '{}/{}'.format(self.pathSensors, group),
                        'w',
                        encoding="utf-8"
                    ) as file:
                        for item in sens:
                            file.write(
                                '{} = {}\n'.format(item.address, item.name))
                        file.close()
        except Exception as error:
            self.logged.emit(
                '{} Sensors not saved to "{}"!'.format(
                    datetime.now().strftime('%H:%M:%S'),
                    self.pathSensors),
                'lsf')

    def read(self):
        """Считать все настройки."""
        self.configRead()
        self.addressesRead()
        self.sensorsRead()

    def save(self):
        """Сохранить все настройки."""
        self.sensorsSave()
        self.addressesSave()
        self.configSave()

    def onRequestReceived(self, lines, address, delta, date):
        """Ответ на запрос получен: сохранить данные."""
        self.addData(lines, date)
        if address in self.addresses:
            if self.addresses[address] != 'No name':
                address = self.addresses[address]
        self.logged.emit('{0} received ({1} s).'.format(address, delta), 'l')

    def onRequestFailed(self, address, delta, time):
        """Запрос не удался."""
        if address in self.addresses:
            if self.addresses[address] != 'No name':
                address = self.addresses[address]
        self.requestsFailedCount += 1
        self.logged.emit('{0} failed ({1} s)!'.format(address, delta), 'l')
        self.logged.emit(
            '{0} Request to {1} failed ({2} s)!'.format(
                time.strftime('%H:%M:%S'),
                address,
                delta),
            'f')

    def addData(self, lines, date):
        """Записать данные в файл с указанной датой."""
        directory = '{0}\\{1}\\{2}\\{3}'.format(
            self.pathData,
            date.strftime('%Y'),
            date.strftime('%m'),
            date.strftime('%d')
        )
        name = date.strftime('%Y.%m.%d')
        if not os.path.exists(directory):
            os.makedirs(directory, 0o777, True)
        try:
            with open('{0}\\{1}.csv'.format(directory, name), 'a') as file:
                for line in lines:
                    if line != ' ':
                        temp = line.split(' ')
                        if len(temp) == 2:
                            temp[1] = temp[1].replace('\r', '')
                            if temp[0] in self.sensors.keys():
                                self.sensors[temp[0]].value = temp[1]
                            else:
                                group = 'unknown'
                                ss = sensor.Sensor(
                                    temp[0],
                                    group,
                                    'No name',
                                    temp[1]
                                )
                                self.sensors[temp[0]] = ss
                                if group in self.groups:
                                    self.groups[group].add(ss)
                                else:
                                    self.groups[group] = {ss}

                            file.write(
                                '{0};{1};{2};{3}\n'.format(
                                    date.strftime('%H:%M:%S'),
                                    temp[0],
                                    self.sensors[temp[0]].name,
                                    self.sensors[temp[0]].value
                                )
                            )
            self.dataAdded.emit()
        except Exception:
            self.logged.emit(
                '{} Data not saved to {}!'.format(
                    date.strftime('%H:%M:%S'),
                    name),
                'lsf')

    def onFinished(self):
        """Событие завершения потока: удалить поток."""
        for thread in self.threads:
            if thread.isFinished():
                self.threads.remove(thread)
        text = '{} of {} responses'.format(
            self.requestsCount - len(self.threads),
            self.requestsCount)

        if self.requestsFailedCount != 0:
            text += ' ({} is failed)'.format(self.requestsFailedCount)

        if len(self.threads) == 0:
            text += '.'
        else:
            text += '...'
        self.logged.emit(text, 's')

    def onChartSaved(self, message):
        """Событие сохранения графика: отправка графика по имейл."""
        self.logged.emit(message, 'ls')
        self.send_mail()

    def get(self, address):
        """Отправить запрос в новом потоке."""
        thread = threadGet.ThreadGet(address)
        thread.requestReceived.connect(
            self.onRequestReceived,
            QtCore.Qt.QueuedConnection)
        thread.requestFailed.connect(
            self.onRequestFailed,
            QtCore.Qt.QueuedConnection)
        thread.finished.connect(
            self.onFinished,
            QtCore.Qt.QueuedConnection)
        self.threads.append(thread)
        thread.start()

    def getServer(self):
        """Получить данные ресурсов компьютера в новом потоке."""
        thread = threadServer.ThreadServer()
        thread.requestReceived.connect(
            self.onRequestReceived,
            QtCore.Qt.QueuedConnection)
        thread.requestFailed.connect(
            self.onRequestFailed,
            QtCore.Qt.QueuedConnection)
        thread.finished.connect(
            self.onFinished,
            QtCore.Qt.QueuedConnection)
        self.threads.append(thread)
        thread.start()

    def draw(self):
        """Сохранить график в новом потоке."""
        self.chart.set_path(self.pathData, self.currentDate)
        self.chart.start()

    def send_mail(self):
        """Отправить имейлы в новом потоке."""
        self.email.set_path(
            self.pathData,
            self.currentDate,
            self.prevDate,
            int(self.period) * int(self.countPeriod)
        )
        self.email.start()

    def mailReceivedEvent(self, message, s):
        """Имейл отправлен."""
        self.logged.emit('{} ({})'.format(message, s), 'ls')

    def mailFailedEvent(self, message, time, s):
        """Отправка имейла не удалась."""
        self.logged.emit('{} ({})'.format(message, s), 'l')
        self.logged.emit(
            '{} {} ({})'.format(time.strftime('%H:%M:%S'), message, s), 'sf')
