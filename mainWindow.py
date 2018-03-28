#!/usr/bin/python3
import sys
import os
from PyQt5.QtWidgets import (QWidget, QInputDialog, QFileDialog, QMessageBox, QAction, QLabel, QLineEdit, QPushButton,
    QTextEdit, QGridLayout, QCheckBox, QMainWindow, QApplication, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import (Qt, QBasicTimer)
from PyQt5.QtGui import QIntValidator



class MainWindow(QMainWindow):
    """MainWindow(QMainWindow)"""
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.core.logged.connect(self.onLogged)
        self.initUI()



    def initUI(self):
        """initUI(self)"""
        self.textEdit = QTextEdit()

        self.actionFileStart = QAction('&Start', self)
        self.actionFileStart.triggered.connect(self.onActionFileStartTriggered)
        self.actionFileStop = QAction('&Stop', self)
        self.actionFileStop.triggered.connect(self.onActionFileStopTriggered)
        self.actionFileStop.setDisabled(True)

        actionFileSave = QAction('&Save config', self)
        actionFileSave.triggered.connect(self.core.save)
        actionFileDraw = QAction('&Save chart', self)
        actionFileDraw.triggered.connect(self.core.draw)

        actionFileLogClear = QAction('&Clear', self)
        actionFileLogClear.triggered.connect(self.textEdit.clear)

        actionFileExit = QAction('&Exit', self)
        actionFileExit.triggered.connect(self.close)

        self.actionViewInfo = QAction('&Extended', self)
        self.actionViewInfo.setCheckable(True)
        self.actionViewInfo.setChecked(True)
        self.actionViewInfo.changed.connect(self.changeRow)

        actionConfigPeriod = QAction('&Period...', self)
        actionConfigPeriod.triggered.connect(self.actionConfigPeriodTriggered)

        actionConfigSensorsAdd = QAction('&Add...', self)
        actionConfigSensorsAdd.triggered.connect(self.actionConfigSensorsAddTriggered)
        actionConfigSensorsDel = QAction('&Delete...', self)
        actionConfigSensorsDel.triggered.connect(self.actionConfigSensorsDelTriggered)
        
        actionConfigPathAddresses = QAction('&Adressess...', self)
        actionConfigPathAddresses.triggered.connect(self.actionConfigPathAddressesTriggered)
        actionConfigPathSensors = QAction('&Sensors...', self)
        actionConfigPathSensors.triggered.connect(self.actionConfigPathSensorsTriggered)
        actionConfigPathData = QAction('&Data...', self)
        actionConfigPathData.triggered.connect(self.actionConfigPathDataTriggered)

        actionHelpHelp = QAction('&Help...', self)
        actionHelpHelp.triggered.connect(self.actionHelpHelpTriggered)
        actionHelpAbout = QAction('&About...', self)
        actionHelpAbout.triggered.connect(self.onAbout)

        menuFile = self.menuBar().addMenu('&File')
        menuFile.addAction(self.actionFileStart)
        menuFile.addAction(self.actionFileStop)
        menuFile.addSeparator()

        menuFileOpen = menuFile.addMenu('&Open')
        menuFileSave = menuFile.addMenu('&Save')
        menuFileSave.addAction(actionFileSave)
        menuFileSave.addAction(actionFileDraw)
        menuFile.addSeparator()

        menuFile.addAction(actionFileLogClear)
        menuFile.addSeparator()

        menuFile.addAction(actionFileExit)

        menuView = self.menuBar().addMenu('&View')
        menuView.addAction(self.actionViewInfo)

        menuConfig = self.menuBar().addMenu('&Settings')
        menuConfig.addAction(actionConfigPeriod)
        menuConfigSensors = menuConfig.addMenu('&Sensors')
        menuConfigSensors.addAction(actionConfigSensorsAdd)
        menuConfigSensors.addAction(actionConfigSensorsDel)
        menuConfigPath = menuConfig.addMenu('&Path')
        menuConfigPath.addAction(actionConfigPathAddresses)
        menuConfigPath.addAction(actionConfigPathSensors)
        menuConfigPath.addAction(actionConfigPathData)

        menuHelp = self.menuBar().addMenu('&Help')
        menuHelp.addAction(actionHelpHelp)
        menuHelp.addAction(actionHelpAbout)
        
        self.textEdit.setVerticalScrollBarPolicy(2)
        self.textEdit.setToolTip("Action log.")

        self.isItemSave = False
        self.table = QTableWidget(0, 3)
        self.table.setToolTip("Temperature sensors.")
        #self.table.setFixedSize(262, 325)
        self.table.setFixedWidth(262)
        self.table.setVerticalScrollBarPolicy(1)
        self.table.setHorizontalScrollBarPolicy(1)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 110)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setHorizontalHeaderLabels(['Val', 'Name', 'Address'])
        self.table.verticalHeader().setFixedWidth(20)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignRight)
        self.table.itemClicked.connect(self.checkItemSave)
        self.table.itemChanged.connect(self.itemSave)
        
        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setContentsMargins(3, 3, 3, 3)
        grid.addWidget(self.textEdit, 0, 0, 1, 1)
        grid.addWidget(self.table, 0, 1, 1, 1)
        widget = QWidget()
        widget.setLayout(grid)
        self.setCentralWidget(widget)

        self.setGeometry(300, 200, 500, 400)
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
        self.statusBar().setSizeGripEnabled(False)
        self.setWindowTitle('Observer')
        self.show()
        self.core.dataAdded.connect(self.onDataAdded)
        self.statusBar().showMessage('Application is runnig.')

        if len(sys.argv) > 1:
            if sys.argv[1] == '-s':
                if len(sys.argv) > 2:
                    if sys.argv[2].isdigit():
                        self.periodEdit.setText(sys.argv[2])
                self.actionFileStart.trigger()
                self.btnStartStop.click()  
        


    def closeEvent(self, event):
        self.core.stop()
        super().closeEvent(event)



    def onActionFileStartTriggered(self):
        """"""
        self.actionFileStop.setEnabled(True)
        self.actionFileStart.setDisabled(True)
        self.core.start()



    def onActionFileStopTriggered(self):
        """"""
        self.actionFileStart.setEnabled(True)
        self.actionFileStop.setDisabled(True)
        self.core.stop()



    def actionConfigSensorsAddTriggered(self):
        """"""
        if os.path.exists(self.core.pathSensors):
            answer = QMessageBox.question(self, 'Add sensors', 'Open file "{}/{}" to add sensors in external editor?'.format(self.core.pathSensors, 'temperature'))
            if answer == QMessageBox.Yes:
                try:
                    #fileList = os.listdir(self.core.pathSensors)
                    #for fileName in fileList:
                    os.startfile('{}\\{}'.format(self.core.pathSensors, 'temperature'))
                except Exception:
                    QMessageBox.warning(self, 'Add sensors', 'File "{}/{}" don`t open!'.format(self.core.pathSensors, 'temperature'))
        else:
            QMessageBox.warning(self, 'Add sensors', '"{}" path does not exist'.format(self.core.pathSensors))



    def actionConfigSensorsDelTriggered(self):
        """"""
        if os.path.exists(self.core.pathSensors):
            answer = QMessageBox.question(self, 'Delete sensors', 'Open file "{}/{}" to delete sensors in external editor?'.format(self.core.pathSensors, 'temperature'))
            if answer == QMessageBox.Yes:
                try:
                    #fileList = os.listdir(self.core.pathSensors)
                    #for fileName in fileList:
                    os.startfile('{}\\{}'.format(self.core.pathSensors, 'temperature'))
                except Exception:
                    QMessageBox.warning(self, 'Delete sensors', 'File "{}/{}" don`t open!'.format(self.core.pathSensors, 'temperature'))
        else:
            QMessageBox.warning(self, 'Delete sensors', '"{}" path does not exist'.format(self.core.pathSensors))



    def actionConfigPeriodTriggered(self):
        """"""
        period, ok = QInputDialog.getInt(self, 'Request period', 'Enter request period:', int(self.core.period), 10, 3600)
        if ok:
            self.core.period = str(period)
            self.core.configSave()



    def actionConfigPathAddressesTriggered(self):
        """"""
        path = QFileDialog.getOpenFileName(self, 'Addresses path', self.core.pathAddresses, '')
        if path[0] != '':
            self.core.pathAddresses = path[0]
            self.core.configSave()



    def actionConfigPathSensorsTriggered(self):
        """"""
        path = QFileDialog.getExistingDirectory(self, 'Sensors directory', self.core.pathSensors)
        if path != '':
            self.core.pathSensors = path
            self.core.configSave()



    def actionConfigPathDataTriggered(self):
        """"""
        path = QFileDialog.getExistingDirectory(self, 'Data directory', self.core.pathData)
        if path != '':
            self.core.pathData = path
            self.core.configSave()



    def changeRow(self):
        """changeRow(state) - изменение отображения всей информации в колонках"""
        if self.actionViewInfo.isChecked():
            self.table.setColumnHidden(1, False)
            self.table.setColumnHidden(2, False)
            self.table.setFixedWidth(self.table.width() + 210)
            self.setFixedWidth(self.width() + 210)
        else:
            self.table.setColumnHidden(1, True)
            self.table.setColumnHidden(2, True)
            self.table.setFixedWidth(self.table.width() - 210)
            self.setFixedWidth(self.width() - 210)
    


    def checkItemSave(self, item):
        """checkItemSave(item) - проверка изменения ячейки имени датчика"""
        if item.column() == 1:
            self.isItemSave = True
        else:
            self.isItemSave = False



    def itemSave(self, item):
        """itemSave(item) - сохранение имени в списке"""
        if self.isItemSave:
            if item.column() == 1:
                if item.tableWidget() == self.table:
                    self.isItemSave = False
                    self.statusBar().showMessage(item.text() + " save")
                    temp = self.table.item(item.row(), 2)
                    key = temp.text()
                    self.core.sensors[key].name = item.text()
        self.table.clearSelection()
                


    def onLogged(self, log, modes):
        """onLogged(log, modes)"""
        if 'l' in modes:
            if len(self.textEdit.toPlainText()) > 100000:
                self.textEdit.setPlainText(self.textEdit.toPlainText()[20000:])
            self.textEdit.append(log)

        if 's' in modes:
            self.statusBar().showMessage(log)

        if 'f' in modes:
            directory = '{0}\\{1}\\{2}\\{3}'.format(self.core.pathData, self.core.currentDate.strftime('%Y'), self.core.currentDate.strftime('%m'), self.core.currentDate.strftime('%d'))
            os.makedirs(directory, 0o777, True)
            with open('{0}\\{1}.log'.format(directory, self.core.currentDate.strftime('%Y.%m.%d')), 'a') as file:
                file.write(log + '\n')
                file.close()
         


    def onDataAdded(self):
        """onDataAdded()"""
        self.table.setRowCount(len(self.core.sensors))
        if self.table.rowCount() <= 20:
            self.table.setMinimumHeight(25 + self.table.rowCount() * 23)
        i = 0
        for key in self.core.sensors.keys():
            if self.core.sensors[key].value != None:
                self.table.setRowHeight(i, 23)
                self.table.setItem(i, 0, QTableWidgetItem(self.core.sensors[key].value))
                self.table.setItem(i, 1, QTableWidgetItem(self.core.sensors[key].name))
                self.table.setItem(i, 2, QTableWidgetItem(key))
                i += 1
        self.table.setRowCount(i)
        self.table.sortItems(1)



    def onAbout(self):
        """"""
        text = '<h2>{0}</h2>'\
               '<p>Client program for monitoring the condition<br>'\
               'of the premises of the Kharkov Radar.<br>'\
               'Source code is available on <a href="https://github.com/StanislavMain/ObserverClient">GitHub</a>.</p>'\
               '<p><b>Stanislav Hnatiuk</b><br>'\
               'Institute of Ionosphere\n<br>Ukraine, Kharkiv.<br><br>'\
               'Contacts with me:<br>'\
               '<a href="https://t.me/stanmain">Telegram</a><br>'\
               '<a href="https://github.com/StanislavMain">GitHub</a><br>'\
               '<br><b>All rights reserved.</b></p>'.format(self.windowTitle())
               #'<a href="mailto:stanislavmain@gmail.com?subject=Program {0}">Email</a><br>'\
        QMessageBox.about(self, 'About the program', text)



    def actionHelpHelpTriggered(self):
        """"""
        text = '<p><b>Console parametrs</b><br>'\
               'usage: main [options]<br>'\
               'where options have next key:<br>'\
               '-s [seconds] : start monitoring with a period of [seconds]</p>'\
               '<p><b>Code and name</b><br>'\
               'Write your addresses and sensors in the appropriate files:<br>'\
               '{}<br>{}/*</p>'\
               '<p><b>Data</b><br>'\
               'Data is located in "{}"<br>'\
               '"/Year/Month/Day/Y.M.D.csv" : data file<br>'\
               '"/Year/Month/Day/Y.M.D.png" : chart file<br>'\
               '"/Year/Month/Day/Y.M.D.log" : log file<br>'\
               '</p>'.format(self.core.pathAddresses, self.core.pathSensors, self.core.pathData)
        QMessageBox.information(self, 'Help', text)