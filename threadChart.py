#!/usr/bin/python3
from PyQt5 import QtCore
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
import os
import gc

class ThreadChart(QtCore.QThread):
    """class ThreadChart"""
    chartSaved = QtCore.pyqtSignal(str) 

    def __init__(self, pathData, currentDate):
        """__init__()"""
        super().__init__()

        self.pathData = '{0}\\{1}\\{2}\\{3}'.format(pathData, currentDate.strftime('%Y'), currentDate.strftime('%m'), currentDate.strftime('%d'))
        self.name = currentDate.strftime('%Y.%m.%d')



    def run(self):
        """run() - основная функция потока."""
        sensorsList = dict()
        pathSensors = "config/sensors"
        if os.path.exists(pathSensors):  
            fileList = os.listdir(pathSensors)
            for fileName in fileList:
                sensorsList[fileName] = list()
                with open('{}/{}'.format(pathSensors, fileName), 'r', encoding="utf-8") as file:
                    for line in file:
                        line = line.replace('\n', '')
                        line = line.replace(' = ', '=')
                        temp = line.split('=')
                        sensorsList[fileName].append(temp[0])
                        if len(temp) > 1:
                            name = temp[1]
                            sensorsList[fileName].append(temp[1])
                    file.close()     
        #================================================================================================
#=======10========20========30========40========50========60========70========80
        #sensors2 = {'Opened' : [[1, 2, 3], [2.0, 2.4, 2.2]], 'Closed' : [[1, 2, 3], [1.9, 2.1, 2.0]]}
        sensors = {}

        # 24 хорошо различимых css цветов. TODO: Добавить до 40

        #cssColors = ('aquamarine', 'blue', 'blueviolet', 'brown', 'cadetblue', 
        #             'chocolate', 'coral', 'cornflowerblue', 'crimson', 'cyan', 
        #             'darkblue', 'darkcyan', 'darkgreen', 'goldenrod', 'green', 
        #             'indigo', 'lime', 'magenta', 'navy', 'orange', 'red', 
        #             'sienna', 'teal', 'yellow')

        cssColors = ('red', 'green', 'blue', 'yellow', 'brown', 'cyan', 'violet',
                     'darkred', 'darkgreen', 'darkblue', 'darkorange', 'darkgoldenrod', 'darkcyan', 'darkviolet',
                     'lightcoral', 'lightgreen', 'lightblue', 'lightsalmon', 'lightcyan', 'darkslategray')

        path = '{}\\{}.csv'.format(self.pathData, self.name)
        if os.path.exists(path):
            try:
                gc.collect()
                with open(path, 'r') as file:
                    for line in file:
                        line = line.replace('\n', '')
                        temp = line.split(';')
                        if len(temp[1]) >= 4:
                            t = temp[0].split(':')
                            time = float(t[0]) + float(int(t[1]) * 60 + int(t[2])) / 3600
                            if temp[2] != 'No name':
                                name = temp[2]
                            else:
                                name = temp[1]
                            if name in sensors:
                                sensors[name][0].append(time)
                                sensors[name][1].append(float(temp[3]))
                            else:
                                sensors[name] = [[time], [float(temp[3])]]

                
                # Настройка изображения
                fig = plt.figure(figsize = (10, 15), dpi = 128)
                fig.suptitle(self.name, fontsize = 24)

                # График температур
                fig1 = fig.add_subplot(311)
                plt.yticks(range(-35, 45, 5))
                plt.xticks(range(0, 25))
                plt.ylim(-35, 40)
                plt.xlim(0, 24)
                plt.title('Temperature')
                plt.xlabel('Decimal time')
                plt.ylabel('°C')
                plt.grid(True, which = 'major', color = 'grey')
                plt.grid(True, which = 'minor', color = 'lightgrey')
                iclr = 0
                for key in sensors.keys():
                    if key in sensorsList['temperature']:
                        fig1.plot(sensors[key][0], sensors[key][1], color = cssColors[iclr], label = key, alpha = 0.7)
                        iclr += 1
                        if iclr == len(cssColors):
                            iclr = 0
                fig1.legend()
                
                # График энергопотребления
                fig2 = fig.add_subplot(312)
                plt.yticks(range(0, 5500, 500))
                plt.xticks(range(0, 25))
                plt.ylim(0, 5000)
                plt.xlim(0, 24)
                plt.title('Power consumption')
                plt.xlabel('Decimal time')
                plt.ylabel('Wh')
                plt.grid(True, which = 'major', color = 'grey')
                plt.grid(True, which = 'minor', color = 'lightgrey')
                iclr = 0
                for key in sensors.keys():
                    if key in sensorsList['consumtion']:
                        fig2.plot(sensors[key][0], sensors[key][1], color = cssColors[iclr], label = key, alpha = 0.7)
                        iclr += 1
                        if iclr == len(cssColors):
                            iclr = 0
                fig2.legend()
                
                # График ресурсов
                fig3 = fig.add_subplot(313)
                plt.yticks(range(0, 110, 10))
                plt.xticks(range(0, 25))
                plt.ylim(0, 100)
                plt.xlim(0, 24)
                plt.title('Used resources')
                plt.xlabel('Decimal time')
                plt.ylabel('%')
                plt.grid(True, which = 'major', color = 'grey')
                plt.grid(True, which = 'minor', color = 'lightgrey')
                iclr = 0
                keycount = 0
                for key in sensors.keys():
                    if key in sensorsList['resources']:
                        fig3.plot(sensors[key][0], sensors[key][1], color = cssColors[iclr], label = key, alpha = 0.7)
                        iclr += 1
                        keycount += 1
                        if iclr == len(cssColors):
                            iclr = 0
                if keycount:
                    fig3.legend()
                

                plt.savefig('{}\\{}.png'.format(self.pathData, self.name))
                self.chartSaved.emit('Chart saved to {}.png.'.format(self.name))
                fig1.cla()
                fig2.cla()
                fig3.cla()
                fig.clf()
                plt.close()
                del gc.garbage[:]

            except Exception as e:
                print(e)
                self.chartSaved.emit('Chart not saved!')
                #fig1.cla()
                #fig2.cla()
                #fig3.cla()
                #fig.clf()
                plt.close('all')
                del gc.garbage[:]
