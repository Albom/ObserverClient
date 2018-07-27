# Copyright © 2018 Stanislav Hnatiuk.  All rights reserved.

# !/usr/bin/env python3

from PyQt5 import QtCore
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
import os
import gc


class ThreadChart(QtCore.QThread):
    """Поток для рисования графика."""
    chartSaved = QtCore.pyqtSignal(str)

    def __init__(self):
        """Инициализация потока."""
        super().__init__()

        # Настройка изображения
        self.fig = plt.figure(figsize=(16, 24), dpi=120)    # (10, 15), 128
        # График температур
        self.fig1 = self.fig.add_subplot(311)

        # График энергопотребления
        self.fig2 = self.fig.add_subplot(312)

        # График ресурсов
        self.fig3 = self.fig.add_subplot(313)

        self.cssColors = (
            'red', 'green', 'blue', 'brown', 'cyan', 'violet', 'darkred',
            'darkgreen', 'darkblue', 'darkorange', 'darkgoldenrod', 'darkcyan',
            'darkviolet', 'lightcoral', 'lightgreen', 'lightblue',
            'lightsalmon', 'lightcyan', 'darkslategray', 'yellow',
            'aquamarine', 'blueviolet', 'cadetblue', 'chocolate', 'coral',
            'cornflowerblue', 'crimson', 'indigo', 'lime', 'magenta', 'navy',
            'orange', 'sienna', 'teal')

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
        # gc.collect()

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
                # gc.collect()
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
                            else:
                                name = temp[1]
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
                                sensors[name] = [[time], [value]]

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
                for key in sensors.keys():
                    if key in sensorsList['temperature']:
                        self.fig1.plot(
                            sensors[key][0],
                            sensors[key][1],
                            color=self.cssColors[iclr],
                            label=key,
                            alpha=0.7
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
                    self.fig1.legend()

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
                for key in sensors.keys():
                    if key in sensorsList['consumtion']:
                        self.fig2.plot(
                            sensors[key][0],
                            sensors[key][1],
                            color=self.cssColors[iclr],
                            label=key,
                            alpha=0.7
                        )
                        iclr += 1
                        keycount += 1
                        if iclr == len(self.cssColors):
                            iclr = 0
                if keycount:
                    self.fig2.legend()

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
                for key in sensors.keys():
                    if key in sensorsList['resources']:
                        self.fig3.plot(
                            sensors[key][0],
                            sensors[key][1],
                            color=self.cssColors[iclr],
                            label=key,
                            alpha=0.7
                        )
                        iclr += 1
                        keycount += 1
                        if iclr == len(self.cssColors):
                            iclr = 0
                if keycount:
                    self.fig3.legend()

                # Обрезка и сохранение в файл.
                self.fig.tight_layout()
                self.fig.savefig('{}\\{}.png'.format(self.pathData, self.name))
                
                # Очистка фигур.
                self.fig1.clear()
                self.fig2.clear()
                self.fig3.clear()
                # sensors.clear()
                # sensorsList.clear()
                # del gc.garbage[:]
                self.chartSaved.emit('Chart saved to {}.png'.format(self.name))

            except Exception as e:
                print(e)
                self.fig1.clear()
                self.fig2.clear()
                self.fig3.clear()
                # del gc.garbage[:]
                self.chartSaved.emit('Chart not saved!')
        # del gc.garbage[:]
