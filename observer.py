#!/usr/bin/python3
import requests
import os
from PyQt5 import QtCore
from datetime import datetime

import threadGet
import threadChart
import sensor



class Observer(QtCore.QObject):
    """class Observer - ядро программы."""
    logged = QtCore.pyqtSignal(str, str)
    dataAdded = QtCore.pyqtSignal()

    def __init__(self):
        """__init__()"""
        QtCore.QObject.__init__(self)
        self.pathAddresses = "config/addresses"
        self.pathConfig = "config/config"
        self.pathFolder = 'config'
        self.pathData = "data"
        self.pathSensors = "config/sensors"
        self.currentDate = datetime.now()
        self.addresses = {}

        self.sensors = {}
        self.groups = {}

        self.period = 60
        self.threads = []
        self.timer = QtCore.QBasicTimer()
        self.read()
    


    def start(self):
        """start() - начать мониторинг и запустить таймер."""
        if not self.timer.isActive():
            self.checkCurrentDay(datetime.now())
            self.configSave()
            self.logged.emit('{} Observation started:'.format(datetime.now().strftime('%H:%M:%S')), 'lf')
            self.read()
            self.timer.start(int(self.period) * 1000, self)
            self.timerEvent(self.timer)
    


    def stop(self):
        """stop() - остановить мониторинг и таймер."""
        if self.timer.isActive():
            self.timer.stop()
            text = '{} Observation stopped.'.format(datetime.now().strftime('%H:%M:%S'))
            self.logged.emit('\n{}'.format(text), 'l')
            self.logged.emit(text, 'f')



    def timerEvent(self, timer):
        """timerEvent(timer) - событие таймера."""
        self.sendRequests()

    

    def checkCurrentDay(self, date):
        """checkCurrentDay()"""
        if  self.currentDate.date() != date.date():
            self.draw()
            self.currentDate = date
            self.logged.emit('New day {}.'.format(self.currentDate.strftime('%Y.%m.%d')), 'l')



    def sendRequests(self):
        """sendRequests() - отправить запросы по адресам."""
        for key in self.sensors.keys():
            self.sensors[key].value = None

        self.requestsCount = len(self.addresses)
        self.requestsFailedCount = 0
        timeBegin = datetime.now()
        self.logged.emit('\n{0} Sending requests:'.format(timeBegin.strftime('%H:%M:%S')), 'l')
        self.logged.emit('Sending requests...', 's')
        self.checkCurrentDay(timeBegin)
        for address in self.addresses:
            self.get(address)



    def configRead(self):
        """configRead() - считать настройки приложения."""
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
                                self.currentDate = self.currentDate.replace(int(t[0]), int(t[1]), int(t[2]))
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
                self.logged.emit('{} Config not readed from "{}"!'.format(datetime.now().strftime('%H:%M:%S'), self.pathConfig), 'lsf')
        else:
            self.configSave()



    def configSave(self):
        """configSave() - сохранить настройки приложения."""
        if not os.path.exists(self.pathFolder):
            os.makedirs(self.pathFolder, 0o777, True)
        try:
            with open(self.pathConfig, 'w', encoding="utf-8") as file:
                file.write('currentDate = {}\n'.format(self.currentDate.strftime('%Y.%m.%d')))
                file.write("pathAddresses = {}\n".format(self.pathAddresses))
                file.write("pathData = {}\n".format(self.pathData))
                file.write("pathSensors = {}\n".format(self.pathSensors))
                file.write("period = {}".format(self.period))
                file.close()
        except Exception as error:
            self.logged.emit('{} Config not saved to "{}"!'.format(datetime.now().strftime('%H:%M:%S'), self.pathConfig), 'lsf')



    def addressesRead(self):
        """addressesRead()"""
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
                self.logged.emit('{} Addresses not readed from "{}"!'.format(datetime.now().strftime('%H:%M:%S'), self.pathAddresses), 'lsf')
        else:
            os.makedirs(self.pathFolder, 0o777, True)



    def addressesSave(self):
        """addressesSave() - сохранить адреса указанного списка."""
        if not os.path.exists(self.pathFolder):
            os.makedirs(self.pathFolder, 0o777, True)
        try:
            if len(self.addresses) != 0:
                with open(self.pathAddresses, 'w', encoding="utf-8") as file:
                    for key in self.addresses.keys():
                        file.write("{0} = {1}\n".format(key, self.addresses[key]))
                    file.close()
        except Exception:
            self.logged.emit('{} Addresses not saved to "{}"!'.format(datetime.now().strftime('%H:%M:%S'), self.pathSensors), 'lsf')



    def sensorsRead(self):
        """sensorsRead()"""
        if os.path.exists(self.pathSensors):  
            try:
                fileList = os.listdir(self.pathSensors)
                for fileName in fileList:
                    with open('{}/{}'.format(self.pathSensors, fileName), 'r', encoding="utf-8") as file:
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
                self.logged.emit('{} Sensors not readed from "{}"!'.format(datetime.now().strftime('%H:%M:%S'), self.pathSensors), 'lsf')
        else:
            os.makedirs(self.pathSensors, 0o777, True)



    def sensorsSave(self):
        """sensorsSave()"""
        if not os.path.exists(self.pathSensors):
            os.makedirs(self.pathSensors, 0o777, True)
        try:
            if len(self.sensors) != 0:
                for group, sens in self.groups.items():
                    with open('{}/{}'.format(self.pathSensors, group), 'w', encoding="utf-8") as file:
                        for item in sens:
                            file.write('{} = {}\n'.format(item.address, item.name))
                        file.close()
        except Exception as error:
            self.logged.emit('{} Sensors not saved to "{}"!'.format(datetime.now().strftime('%H:%M:%S'), self.pathSensors), 'lsf')



    def read(self):
        """read() - считать все списки."""
        self.configRead()
        self.addressesRead()
        self.sensorsRead()
    


    def save(self):
        """save() - сохранить все списки."""
        self.sensorsSave()
        self.addressesSave()
        self.configSave()



    def onRequestReceived(self, lines, address, delta, date):
        """onRequestReceived(lines) - событие запрос получен: сохранить данные."""
        self.addData(lines, date)
        if address in self.addresses:
            if self.addresses[address] != 'No name': 
                address = self.addresses[address]
        self.logged.emit('{0} received ({1} s).'.format(address, delta), 'l')



    def onRequestFailed(self, address, delta, time):
        """onRequestFailed(address, delta)"""
        if address in self.addresses:
            if self.addresses[address] != 'No name':
                address = self.addresses[address]
        self.requestsFailedCount += 1
        self.logged.emit('{0} failed ({1} s)!'.format(address, delta), 'l')
        self.logged.emit('{0} request to {1} failed ({2} s)!'.format(time.strftime('%H:%M:%S'), address, delta), 'f')




    def addData(self, lines, date):
        """addData(mlist, lines) - добавить данные в указанный список."""
        directory = '{0}\\{1}\\{2}\\{3}'.format(self.pathData, date.strftime('%Y'), date.strftime('%m'), date.strftime('%d'))
        name = date.strftime('%Y.%m.%d')
        if not os.path.exists(directory):
            os.makedirs(directory, 0o777, True)
        try:
            with open('{0}\\{1}.csv'.format(directory, name), 'a') as file:
                for line in lines:
                    temp = line.split(' ')
                    if len(temp) == 2:
                        if temp[0] in self.sensors.keys():
                            self.sensors[temp[0]].value = temp[1]
                        else:
                            group = 'unknown'
                            ss = sensor.Sensor(temp[0], group, 'No name', temp[1])
                            self.sensors[temp[0]] = ss
                            if group in self.groups:
                                self.groups[group].add(ss)
                            else:
                                self.groups[group] = {ss}

                        file.write('{0};{1};{2};{3}\n'.format(date.strftime('%H:%M:%S'), temp[0], self.sensors[temp[0]].name, self.sensors[temp[0]].value))
            self.dataAdded.emit()
        except Exception:
            self.logged.emit('{} Data not saved to {}!'.format(date.strftime('%H:%M:%S'), name), 'lsf')



    def onFinished(self):
        """onFinished() - событие завершения потока: удалить поток."""
        for thread in self.threads:
            if thread.isFinished():
                self.threads.remove(thread)
                #break
        text = '{} of {} responses'.format(self.requestsCount -  len(self.threads), self.requestsCount)
        
        if self.requestsFailedCount != 0:
            text += ' ({} is failed)'.format(self.requestsFailedCount)
        
        if len(self.threads) == 0:
            text += '.'
        else:
            text += '...'
        self.logged.emit(text, 's')
                


    def onChartSaved(self, message):
        """onChartSaved(message)"""
        self.logged.emit(message, 'ls')



    def get(self, address):
        """get() - получить запрос в новом потоке."""
        thread = threadGet.ThreadGet(address)
        thread.requestReceived.connect(self.onRequestReceived, QtCore.Qt.QueuedConnection)
        thread.requestFailed.connect(self.onRequestFailed, QtCore.Qt.QueuedConnection)
        thread.finished.connect(self.onFinished, QtCore.Qt.QueuedConnection)
        self.threads.append(thread)
        thread.start()

        

    def draw(self):
        """draw()"""
        self.chart = threadChart.ThreadChart(self.pathData, self.currentDate)
        self.chart.chartSaved.connect(self.onChartSaved, QtCore.Qt.QueuedConnection)
        self.chart.finished.connect(self.chart.deleteLater, QtCore.Qt.QueuedConnection)
        self.chart.start()