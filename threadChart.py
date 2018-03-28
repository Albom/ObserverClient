#!/usr/bin/python3
from PyQt5 import QtCore
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
import os

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
        sensors2 = {'Opened' : [[1, 2, 3], [2.0, 2.4, 2.2]], 'Closed' : [[1, 2, 3], [1.9, 2.1, 2.0]]}
        sensors = {}

        # 24 хорошо различимых css цветов. TODO: Добавить до 40 
        cssColors = {'aquamarine', 'blue', 'blueviolet', 'brown', 'cadetblue', 'chocolate', 'coral', 'cornflowerblue', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgreen', 'goldenrod', 'green', 'indigo', 'lime', 'magenta', 'navy',
                     'orange', 'red', 'sienna', 'teal', 'yellow'}
        path = '{}\\{}.csv'.format(self.pathData, self.name)
        if os.path.exists(path):
            try:
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
                plt.figure(figsize = (10, 10), dpi = 64) # 10x10 inch, 640x640: dpi = 64; 12x12 inch, 1280x1280: dpi = 106.67;

                plt.suptitle(self.name, fontsize = 24)
                # График температур
                plt.subplot(211)
                plt.yticks(range(-35, 45, 5))
                plt.xticks(range(0, 25))
                plt.ylim(-35, 40)
                plt.xlim(0, 24)
                plt.title('Temperature')
                plt.xlabel('Decimal time')
                plt.ylabel('°C')
                plt.grid(True, which = 'major', color = 'grey')
                plt.grid(True, which = 'minor', color = 'lightgrey')
                for key, clr in zip(sensors.keys(), cssColors):
                    plt.plot(sensors[key][0], sensors[key][1], color = clr, label = key)
                plt.legend()

                # График энергопотребления
                plt.subplot(212)
                plt.yticks([0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
                plt.xticks(range(0, 25))
                plt.ylim(0, 5)
                plt.xlim(0, 24)
                plt.title('Power consumption')
                plt.xlabel('Decimal time')
                plt.ylabel('kWh')
                plt.grid(True, which = 'major', color = 'grey')
                plt.grid(True, which = 'minor', color = 'lightgrey')
                for key, clr in zip(sensors2.keys(), cssColors):
                    plt.plot(sensors2[key][0], sensors2[key][1], color = clr, label = clr)
                plt.legend()

                plt.savefig('{}\\{}.png'.format(self.pathData, self.name))
                self.chartSaved.emit('Chart saved to {}.png.'.format(self.name))
            except Exception as e:
                print(e)
                self.chartSaved.emit('Chart not saved!')



