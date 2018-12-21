# Original work Copyright © 2018 Stanislav Hnatiuk
# Modified work Copyright 2018 Oleksandr Bogomaz

# !/usr/bin/env python3

from PyQt5 import QtCore
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
import os


class ThreadChart(QtCore.QThread):
    """Поток для рисования графика."""
    chartSaved = QtCore.pyqtSignal(str)

    def __init__(self):
        """Инициализация потока."""
        super().__init__()

        # Настройка изображения
        self.fig = plt.figure(figsize=(10, 15), dpi=128)
        # График температур
        self.fig1 = self.fig.add_subplot(311)

        box = self.fig1.get_position()
        self.fig1.set_position([box.x0, box.y0, box.width * 0.8, box.height])
		
        # График энергопотребления
        self.fig2 = self.fig.add_subplot(312)
        box = self.fig2.get_position()
        self.fig2.set_position([box.x0, box.y0, box.width * 0.8, box.height])
		
        # График ресурсов
        self.fig3 = self.fig.add_subplot(313)
        box = self.fig3.get_position()
        self.fig3.set_position([box.x0, box.y0, box.width * 0.8, box.height])

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
                                if time - sensors[name][0][-1] > 0.08333333334:
                                    sensors[name][0].append(time - 0.08)
                                    sensors[name][1].append(float('Inf'))
                                sensors[name][0].append(time)
                                sensors[name][1].append(value)
                            else:
                                sensors[name] = [[time], [value], description]

                # Настрйоки фигуры для графика температур.
                self.fig1.set_title(self.name, loc='left')
                self.fig1.set_title('Температура', fontsize=20)
                self.fig1.set_xticks(range(0, 25))
                self.fig1.set_xlim(0, 24)
                self.fig1.set_xlabel('Время')
                self.fig1.set_ylabel('°C')
                self.fig1.grid(True, which='major', color='grey')
                self.fig1.grid(True, which='minor', color='lightgrey')
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
                            self.fig1.plot(
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
                        self.fig1.legend(loc='center left', bbox_to_anchor=(1, 0.5))

                # Настрйоки фигуры для графика энергопотребления.
                self.fig2.set_title(self.name, loc='left')
                self.fig2.set_title('Энергопотребление', fontsize=20)
                self.fig2.set_xticks(range(0, 25))
                self.fig2.set_xlim(0, 24)
                self.fig2.set_xlabel('Время')
                self.fig2.set_ylabel('Вт')
                self.fig2.grid(True, which='major', color='grey')
                self.fig2.grid(True, which='minor', color='lightgrey')

                # Отрисовка графика температур.
                iclr = 0
                keycount = 0
                if 'consumtion' in sensorsList:
                    keys = list(sensors.keys())
                    keys.sort()
                    for key in keys:
                        if key in sensorsList['consumtion']:
                            self.fig2.plot(
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
                        #box = self.fig2.get_position()
                        #self.fig2.set_position([box.x0, box.y0, box.width * 0.8, box.height])
                        self.fig2.legend(loc='center left', bbox_to_anchor=(1, 0.5))

                # Настрйоки фигуры для графика ресурсов компьютера.
                self.fig3.set_title(self.name, loc='left')
                self.fig3.set_title('Нагрузка', fontsize=20)
                self.fig3.set_xticks(range(0, 25))
                self.fig3.set_yticks(range(0, 110, 10))
                self.fig3.set_xlim(0, 24)
                self.fig3.set_ylim(0, 100)
                self.fig3.set_xlabel('Время')
                self.fig3.set_ylabel('%')
                self.fig3.grid(True, which='major', color='grey')
                self.fig3.grid(True, which='minor', color='lightgrey')
                # Отрисовка графика ресурсов.
                iclr = 0
                keycount = 0
                if 'resources' in sensorsList:
                    keys = list(sensors.keys())
                    keys.sort()
                    for key in keys:
                        if key in sensorsList['resources']:
                            self.fig3.plot(
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
                        #box = self.fig3.get_position()
                        #self.fig3.set_position([box.x0, box.y0, box.width * 0.8, box.height])
                        self.fig3.legend(loc='center left', bbox_to_anchor=(1, 0.5))


                # Сохранение в файл.
                self.fig.savefig('{}\\{}.pdf'.format(self.pathData, self.name))

                # Очистка фигур.
                self.fig1.clear()
                self.fig2.clear()
                self.fig3.clear()
                self.chartSaved.emit('Chart is saved to {}.pdf'.format(self.name))

            except Exception as e:
                print(e)
                self.fig1.clear()
                self.fig2.clear()
                self.fig3.clear()
                self.chartSaved.emit('Chart is not saved!')
