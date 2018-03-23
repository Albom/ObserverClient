#!/usr/bin/python3
from PyQt5 import QtCore
import requests
from datetime import datetime
import matplotlib.pyplot as plt


class ThreadChart(QtCore.QThread):
    """class ThreadChart"""
    
    def __init__(self):
        """__init__()"""
        super().__init__()


    def run(self):
        """run() - основная функция потока."""
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
        plt.figure(figsize = (16, 9), dpi = 80) #hd: dpi = 80; fullhd: dpi = 120; 4k: dpi = 240
        plt.yticks(range(-30, 40, 5), )
        plt.xticks(range(0, 24))
        plt.plot(x, y, color = 'red', label = 'Opened')
        plt.plot([0, 24], [0, 0], color = 'black')
        plt.ylim(-35, 40)
        plt.xlim(0, 24)
        plt.title('Temperature')
        plt.xlabel('Decimal time')
        plt.legend()
        plt.ylabel('°C')
        plt.grid(True, which = 'major', color = 'grey')
        plt.grid(True, which = 'minor', color = 'lightgrey')
        plt.minorticks_on()
        plt.savefig('{}.{}'.format('Opened', 'png'))




