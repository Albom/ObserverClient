# Original work Copyright © 2018 Stanislav Hnatiuk
# Modified work Copyright 2018-2019 Oleksandr Bogomaz

# !/usr/bin/env python3

from PyQt5 import QtCore
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.backends.backend_pdf import PdfPages
import os


class ThreadChart(QtCore.QThread):
    """Поток для рисования графика."""
    chartSaved = QtCore.pyqtSignal(str)

    def __init__(self):
        """Инициализация потока."""
        super().__init__()

        self.cssColors = ('#000000', '#0000AA', '#00AA00', '#00AAAA', '#AA0000',
             '#AA00AA', '#AA5500', '#555555', '#5555FF', '#55FF55',
             '#55FFFF', '#FF5555', '#FF55FF', '#FFFF55'
        )

    def set_path(self, pathData, currentDate):
        """Установка пути к файлу графика."""
        self.pathData = '{0}\\{1}\\{2}\\{3}'.format(
            pathData,
            currentDate.strftime('%Y'),
            currentDate.strftime('%m'),
            currentDate.strftime('%d'))
        self.name = currentDate.strftime('%Y.%m.%d')

    def run(self):
        """Основная функция потока."""

        # Считать адреса датчиков из файлов.
        sensorsList = dict()
        pathSensors = "config/sensors"
        if os.path.exists(pathSensors):
            fileList = os.listdir(pathSensors)
            for fileName in fileList:
                sensorsList[fileName] = list()
                with open(
                    '{}/{}'.format(pathSensors, fileName),
                    'r',
                    encoding="utf-8"
                ) as file:
                    for line in file:
                        line = line.replace('\n', '')
                        line = line.replace(' = ', '=')
                        temp = line.split('=')
                        sensorsList[fileName].append(temp[0])
                        if len(temp) > 1:
                            name = temp[1]
                            sensorsList[fileName].append(temp[1])

        sensors = {}

        # Считать данные датчиков из файла.
        path = '{}\\{}.csv'.format(self.pathData, self.name)
        if os.path.exists(path):
            try:
                with open(path, 'r') as file:
                    for line in file:
                        line = line.replace('\n', '')
                        temp = line.split(';')
                        if len(temp[1]) >= 4:
                            t = temp[0].split(':')
                            time = float(t[0]) + float(
                                int(t[1]) * 60 + int(t[2])
                            ) / 3600
                            if temp[2] != 'No name':
                                name = temp[2]
                                description = '{} ({})'.format(temp[2], temp[1][-4:])
                            else:
                                name = temp[1]
                                description = temp[1]
                            try:
                                value = float(temp[3])
                            except ValueError:
                                # Пропуск данных в случае ошибки.
                                value = float('Inf')
                            if name in sensors:
                                # Добавление пропуска если нет данных
                                # в течении пяти минут ().
                                if time - sensors[name][0][-1] > 5.0/60.0:
                                    sensors[name][0].append(time - 0.08)
                                    sensors[name][1].append(float('Inf'))
                                sensors[name][0].append(time)
                                sensors[name][1].append(value)
                            else:
                                sensors[name] = [[time], [value], description]

                with PdfPages('{}\\{}.pdf'.format(self.pathData, self.name)) as pdf:
                
                    fig = plt.figure(figsize=(10, 15), dpi=128)
                    # График температур
                    fig1 = fig.add_subplot(111)

                    fig1.set_title(self.name, loc='left')
                    fig1.set_title('Температура', fontsize=20)
                    fig1.set_xticks(range(0, 25))
                    fig1.set_xlim(0, 24)
                    fig1.set_xlabel('Время')
                    fig1.set_ylabel('°C')
                    fig1.grid(True, which='major', color='grey')
                    fig1.grid(True, which='minor', color='lightgrey')

                    # Отрисовка графика температур.
                    iclr = 0
                    keycount = 0
                    ymax = -100
                    ymin = 100
                    if 'temperature' in sensorsList:
                        keys = list(sensors.keys())
                        keys.sort()
                        for key in keys:
                            if key in sensorsList['temperature']:
                                fig1.plot(
                                    sensors[key][0],
                                    sensors[key][1],
                                    color=self.cssColors[iclr],
                                    label=sensors[key][2],
                                    alpha=1
                                )
                                t_max = max(sensors[key][1])
                                t_min = min(sensors[key][1])
                                if t_max > ymax:
                                    ymax = t_max
                                if t_min < ymin:
                                    ymin = t_min
                                iclr += 1
                                keycount += 1
                                if iclr == len(self.cssColors):
                                    iclr = 0
                        if keycount:
                            fig1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1))

                    plt.subplots_adjust(bottom=0.3)
                    pdf.savefig(fig)
                    plt.close()
                    
                    fig = plt.figure(figsize=(10, 15), dpi=128)
                    plt.subplots_adjust(hspace=0.6)

                    figs = [0]*6
                    for i in range(6):
                        figs[i] = fig.add_subplot(6, 1, i+1)

                        # Настройки фигуры для графика энергопотребления.
                        figs[i].set_title(self.name, loc='left')
                        figs[i].set_xticks(range(0, 25))
                        figs[i].set_xlim(0, 24)
                        figs[i].set_xlabel('Время')
                        figs[i].set_ylim(0, 2000)
                        figs[i].set_ylabel('Вт')
                        figs[i].grid(True, which='major', color='grey')
                        figs[i].grid(True, which='minor', color='lightgrey')

                        # Отрисовка графика энергопотребления.
                        iclr = 0
                        keycount = 0
                        if 'consumtion' in sensorsList:
                            keys = list(sensors.keys())
                            keys.sort()
                            for key in keys:
                                if key in sensorsList['consumtion']:
                                    if list(sensorsList['consumtion']).index(sensors[key][2].split('(')[0][:-1])//2 == i:
                                        figs[i].plot(
                                            sensors[key][0],
                                            sensors[key][1],
                                            color=self.cssColors[iclr],
                                            label=sensors[key][2],
                                            alpha=1
                                        )
                                        figs[i].set_title(sensors[key][2], fontsize=10)
                                        iclr += 1
                                        keycount += 1
                                        if iclr == len(self.cssColors):
                                            iclr = 0
                    plt.subplots_adjust()
                    pdf.savefig(fig)
                    plt.close()

                    fig = plt.figure(figsize=(10, 15), dpi=128)

                    fig3 = fig.add_subplot(111)

                    # Настройки фигуры для графика ресурсов компьютера.
                    fig3.set_title(self.name, loc='left')
                    fig3.set_title('Нагрузка', fontsize=20)
                    fig3.set_xticks(range(0, 25))
                    fig3.set_yticks(range(0, 110, 10))
                    fig3.set_xlim(0, 24)
                    fig3.set_ylim(0, 100)
                    fig3.set_xlabel('Время')
                    fig3.set_ylabel('%')
                    fig3.grid(True, which='major', color='grey')
                    fig3.grid(True, which='minor', color='lightgrey')
                    # Отрисовка графика ресурсов.
                    iclr = 0
                    keycount = 0
                    if 'resources' in sensorsList:
                        keys = list(sensors.keys())
                        keys.sort()
                        for key in keys:
                            if key in sensorsList['resources']:
                                fig3.plot(
                                    sensors[key][0],
                                    sensors[key][1],
                                    color=self.cssColors[iclr],
                                    label=sensors[key][2],
                                    alpha=1
                                )
                                iclr += 1
                                keycount += 1
                                if iclr == len(self.cssColors):
                                    iclr = 0
                        if keycount:
                            fig3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1))

                    plt.subplots_adjust(bottom=0.17)
                    pdf.savefig(fig)
                    plt.close()

                    self.chartSaved.emit('Chart is saved to {}.pdf'.format(self.name))

            except Exception as e:
                print(e)
                self.chartSaved.emit('Chart is not saved!')
