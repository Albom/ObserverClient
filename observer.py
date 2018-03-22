#!/usr/bin/python3
import requests
import os
from PyQt5 import QtCore
import threadGet
from datetime import datetime
import matplotlib.pyplot as plt
#import matplotlib as mpl

class Observer(QtCore.QObject):
    """class Observer - ядро программы."""
    logged = QtCore.pyqtSignal(str)
    dataAdded = QtCore.pyqtSignal()

    def __init__(self):
        """__init__()"""
        QtCore.QObject.__init__(self)
        self.pathAddresses = "config/addresses"
        self.pathConfig = "config/config"
        self.pathData = "data"
        self.pathSensors = "config/sensors"
        self.addresses = {}
        self.sensors = {}
        self.period = 30
        self.threads = []
        self.temperatures = {}
        self.consumptions = {}
        self.timer = QtCore.QBasicTimer()
        self.log = ''
        self.configRead()



    def __del__(self):
        """__del__()"""
        self.configSave()
    


    def start(self):
        """start() - начать мониторинг и запустить таймер."""
        if not self.timer.isActive():
            self.configSave()
            self.read()
            self.timer.start(int(self.period) * 1000, self)
            self.timerEvent(self.timer)
    


    def stop(self):
        """stop() - остановить мониторинг и таймер."""
        if self.timer.isActive():
            self.timer.stop()


    def timerEvent(self, timer):
        """timerEvent(timer) - событие таймера."""
        self.sendRequests()



    def sendRequests(self):
        """sendRequests() - отправить запросы по адресам."""
        for key in self.sensors.keys():
            self.sensors[key][1] = ''
        timeBegin = datetime.now()
        self.logged.emit('\n{0} Sending requests'.format(timeBegin.strftime('%H:%M:%S')))
        for address in self.addresses:
            self.get(address)



    def configRead(self):
        """configRead() - считать настройки приложения."""
        try:
            with open(self.pathConfig, 'tr') as file:
                for line in file:
                    line = line.replace('\n', '')
                    line = line.replace(' = ', '=')
                    temp = line.split('=')
                    if len(temp) == 2:
                        if temp[0] == "pathAddresses":
                            self.pathAddresses = temp[1]
                        elif temp[0] == "pathData":
                            self.pathData = temp[1]
                        elif temp[0] == "pathSensors":
                            self.pathSensors = temp[1]
                        elif temp[0] == "period":
                            self.period = temp[1]
        except Exception as error:
            print(error)
            self.configSave()



    def configSave(self):
        """configSave() - сохранить настройки прложения."""
        try:
            with open(self.pathConfig, 'w', encoding="utf-8") as file:
                file.write("pathAddresses = {0}\n".format(self.pathAddresses))
                file.write("pathData = {0}\n".format(self.pathData))
                file.write("pathSensors = {0}\n".format(self.pathSensors))
                file.write("period = {0}".format(self.period))
        except Exception as error:
            print(error)



    def __read(self, mlist, path):
        """__read(mlist, path) - считать адреса указанного списка."""
        try:
            with open(path, 'r', encoding="utf-8") as file:
                for line in file:
                    line = line.replace('\n', '')
                    line = line.replace(' = ', '=')
                    temp = line.split('=')
                    if len(temp) > 1:
                        mlist[temp[0]] = [temp[1], '']
                    else:
                        mlist[temp[0]] = ['No name', '']
        except Exception as error:
            print(error)



    def read(self):
        """read() - считать все списки."""
        self.__read(self.addresses, self.pathAddresses)
        self.__read(self.sensors, self.pathSensors)



    def __save(self, mlist, path):
        """__save(mlist, path) - сохранить адреса указанного списка."""
        try:
            with open(path, 'w', encoding="utf-8") as file:
                for key in mlist.keys():
                    file.write("{0} = {1}\n".format(key, mlist[key][0]))
        except Exception as error:
            print(error)



    def save(self):
        """save() - сохранить все списки."""
        self.__save(self.addresses, self.pathAddresses)
        self.__save(self.sensors, self.pathSensors)



    def onRequestReceived(self, lines, address, delta, date):
        """onRequestReceived(lines) - событие запрос получен: сохранить данные."""
        self.addData(self.sensors, lines, date)
        if address in self.addresses:
            if self.addresses[address][0] != 'No name': 
                self.logged.emit('{0} received ({1} s).'.format(self.addresses[address][0], delta))
                return
        self.logged.emit('{0} received ({1} s).'.format(address, delta))
        #if lines[0] == 'Temperatures':
        #    self.addData(self.temperatures, lines[1:])
        #elif lines[0] == 'Consumptions':
        #    self.addData(self.consumptions, lines[1:])



    def onRequestFailed(self, address, delta, time):
        """onRequestFailed(address, delta)"""
        if address in self.addresses:
            if self.addresses[address][0] != 'No name':
                self.logged.emit('{0} failed ({1} s)!'.format(self.addresses[address][0], delta))
                return
        self.logged.emit('{0} failed ({1} s)!'.format(address, delta))



    def addData(self, mlist, lines, date):
        """addData(mlist, lines) - добавить данные в указанный список."""
        directory = '{0}\\{1}\\{2}\\{3}'.format(self.pathData, date.strftime('%Y'), date.strftime('%m'), date.strftime('%d'))
        os.makedirs(directory, 0o777, True)
        with open('{0}\\{1}.csv'.format(directory, date.strftime('%Y.%m.%d')), 'a') as file:
            for line in lines:
                temp = line.split(' ')
                if len(temp) == 2:
                    if temp[0] in mlist:
                        mlist[temp[0]][1] = temp[1]
                    else:
                        mlist[temp[0]] = ['No name', temp[1]]
                    file.write('{0};{1};{2};{3}\n'.format(date.strftime('%H:%M:%S'), temp[0], mlist[temp[0]][0], mlist[temp[0]][1]))
        self.dataAdded.emit()
                #with open(request_start.strftime('%Y') + '\\' + request_start.strftime('%m') + '\\' + request_start.strftime('%Y.%m.%d') + '.csv', 'a') as file:
                #    file.write(record)
            #print(line)
        #print(mlist)



    def onFinished(self):
        """onFinished() - событие завершения потока: удалить поток."""
        for thread in self.threads:
            if thread.isFinished():
                self.threads.remove(thread)
                break



    def get(self, address):
        """get() - получить запрос в новом потоке."""
        thread = threadGet.ThreadGet(address)
        thread.requestReceived.connect(self.onRequestReceived, QtCore.Qt.QueuedConnection)
        thread.requestFailed.connect(self.onRequestFailed, QtCore.Qt.QueuedConnection)
        thread.finished.connect(self.onFinished, QtCore.Qt.QueuedConnection)
        self.threads.append(thread)
        thread.start()
        #for address in self.addresses.keys():
        #    try:
        #        print("Get {0}".format(address))
        #        request = requests.get('http://' + address)

        #        if request.status_code == 200:
        #            temp = request.text
        #            print(temp)
        #        elif int(request.status_code / 100) == 1:
        #            print("{0}: Informational".format(request.status_code))
        #        elif int(request.status_code / 100) == 2:
        #            print("{0}: Success".format(request.status_code))
        #        elif int(request.status_code / 100) == 3:
        #            print("{0}: Redirection ".format(request.status_code))
        #        elif int(request.status_code / 100) == 4:
        #            print("{0}: Client Error".format(request.status_code))
        #        elif int(request.status_code / 100) == 5:
        #            print("{0}: Server Error".format(request.status_code))

        #    except requests.RequestException as error:
        #        print(error)
        

    def draw(self):
        """draw("""
        x = []
        y = []
        with open('2018.03.22.csv', 'r') as file:
            for line in file:
                temp = line.split(';')
                if temp[1] == '287F2D9F04000053':
                    t = temp[0].split(':')
                    time = float(t[0]) + float(int(t[1]) * 60 + int(t[2])) / 3600
                    x.append(time)
                    y.append(int(temp[3]))

        plt.figure(figsize = (16, 9), dpi = 120)
        plt.yticks(range(-30, 40, 5), )
        plt.xticks(range(0, 24))
        plt.plot(x, y, color = 'red', label = 'Opened')
        plt.plot([0, 24], [0, 0], color = 'black')
        plt.ylim(-30, 40)
        plt.xlim(0, 24)
        plt.title('Temperature')
        plt.xlabel('Decimal time')
        plt.legend()
        plt.ylabel('°C')
        plt.grid(True, which = 'major', color = 'grey')
        plt.grid(True, which = 'minor', color = 'lightgrey')
        plt.minorticks_on()
        plt.savefig('{}.{}'.format('Opened', 'png'))
        #pic.show()