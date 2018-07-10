#!/usr/bin/python3
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
    """class Observer - ядро программы."""
    logged = QtCore.pyqtSignal(str, str)
    dataAdded = QtCore.pyqtSignal()

    def __init__(self):
        """__init__()"""
        QtCore.QObject.__init__(self)
        self.pathAddresses = "config/addresses"
        self.pathConfig = "config/config"
        self.pathEmails = 'config/emails'
        self.pathFolder = 'config'
        self.pathData = "data"
        self.pathSensors = "config/sensors"
        self.currentDate = datetime.now()
        self.addresses = {}

        self.sensors = {}
        self.groups = {}

        self.period = 60
        self.countPeriod = 2
        self.threads = []
        self.emails = ((12, 0),)
        self.email = threadMail.ThreadMail()
        self.email.mailReceived.connect(self.mailReceivedEvent)
        self.email.mailFailed.connect(self.mailFailedEvent)

        self.chart = threadChart.ThreadChart()
        self.chart.chartSaved.connect(self.onChartSaved, QtCore.Qt.QueuedConnection)
        # self.chart.finished.connect(self.chart.deleteLater, QtCore.Qt.QueuedConnection)

        self.timerRequests = QtCore.QTimer()
        self.timerRequests.timeout.connect(self.timerRequestsEvent)
        self.timerChart = QtCore.QTimer()
        self.timerChart.timeout.connect(self.timerChartEvent)
        self.timerMail = QtCore.QTimer()
        self.timerMail.timeout.connect(self.timerMailEvent)
        self.read()
    


    def start(self):
        """start() - начать мониторинг и запустить таймер."""
        if not (self.timerRequests.isActive() and self.timerChart.isActive()):
            now = datetime.now()
            self.checkCurrentDay(now)
            self.configSave()
            self.logged.emit('{} Observation started:'.format(now.strftime('%H:%M:%S')), 'lf')
            self.read()
            self.timerRequests.start(int(self.period) * 1000)
            self.timerChart.start(int(self.period) * 1000 * self.countPeriod)

            self.timerRequestsEvent()
            #self.timerChartEvent(self.timerChart)
    


    def stop(self):
        """stop() - остановить мониторинг и таймер."""
        if self.timerRequests.isActive() and self.timerChart.isActive():
            self.timerRequests.stop()
            self.timerChart.stop()
            text = '{} Observation stopped.'.format(datetime.now().strftime('%H:%M:%S'))
            self.logged.emit('\n{}'.format(text), 'l')
            self.logged.emit(text, 'f')



    def timerRequestsEvent(self):
        """timerEvent(timer) - событие таймера."""
        self.sendRequests()



    def timerChartEvent(self):
        """timerChartEvent(timer) - событие таймера."""
        self.draw()
        
    
    def timerMailEvent(self):
        self.email.start()
        self.timerMail.setInterval()
    
   
    def checkCurrentDay(self, date):
        """checkCurrentDay()"""
        if self.currentDate.date() != date.date():
            self.draw()
            self.send_mail()
            self.currentDate = date
            self.logged.emit('New day {}.'.format(self.currentDate.strftime('%Y.%m.%d')), 'l')


    def checkCurrentTime(self):
        period = int(self.period)
        countPeriod = int(self.countPeriod)

        def check(curr, new):
            need1 = datetime(now.year, now.month, now.day, new[0], new[1], 0)
            need2 = need1 + timedelta(seconds=period * countPeriod)
            # print(need1.time(), '-', need2.time())
            return (curr >= need1) and (curr < need2)

        now = datetime.now()
        for tt in self.emails:
            if check(now, tt):
                return True
        return False


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
        self.getServer()



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
        # self.emailsRead()
    


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
        self.logged.emit('{0} Request to {1} failed ({2} s)!'.format(time.strftime('%H:%M:%S'), address, delta), 'f')

    def addData(self, lines, date):
        """addData(mlist, lines) - добавить данные в указанный список."""
        directory = '{0}\\{1}\\{2}\\{3}'.format(self.pathData, date.strftime('%Y'), date.strftime('%m'), date.strftime('%d'))
        name = date.strftime('%Y.%m.%d')
        if not os.path.exists(directory):
            os.makedirs(directory, 0o777, True)
        try:
            with open('{0}\\{1}.csv'.format(directory, name), 'a') as file:
                for line in lines:
                    #if line != ' ':
                        temp = line.split(' ')
                        if len(temp) == 2:
                            #temp[1] = temp[1].replace('\0', '')
                            #temp[1] = temp[1].replace('\n', '')
                            temp[1] = temp[1].replace('\r', '')
                            if temp[0] in self.sensors.keys():
                                self.sensors[temp[0]].value = temp[1]
                                #sprint('"{}" "{}"'.format(temp[0], temp[1]));
                                #temp[1] = temp[1].replace('\0', '');
                            else:
                                group = 'Unknown'
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
        if self.checkCurrentTime():
            print('send...')
            self.send_mail()


    def get(self, address):
        """get() - получить запрос в новом потоке."""
        thread = threadGet.ThreadGet(address)
        thread.requestReceived.connect(self.onRequestReceived, QtCore.Qt.QueuedConnection)
        thread.requestFailed.connect(self.onRequestFailed, QtCore.Qt.QueuedConnection)
        thread.finished.connect(self.onFinished, QtCore.Qt.QueuedConnection)
        self.threads.append(thread)
        thread.start()


    def getServer(self):
        thread = threadServer.ThreadServer()
        thread.requestReceived.connect(self.onRequestReceived, QtCore.Qt.QueuedConnection)
        thread.requestFailed.connect(self.onRequestFailed, QtCore.Qt.QueuedConnection)
        thread.finished.connect(self.onFinished, QtCore.Qt.QueuedConnection)
        self.threads.append(thread)
        thread.start()

     
    def draw(self):
        """draw()"""
        self.chart.set_path(self.pathData, self.currentDate)
        self.chart.start()

    def send_mail(self):
        self.email.set_path(self.pathData, self.currentDate)
        self.email.start()

    def mailReceivedEvent(self, message, s):
        self.logged.emit('{} ({})'.format(message, s), 'ls')

    def mailFailedEvent(self, message, time, s):
        self.logged.emit('{} ({})'.format(message, s), 'l')
        self.logged.emit('{} {} ({})'.format(time.strftime('%H:%M:%S'), message, s), 'sf')
