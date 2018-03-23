#!/usr/bin/python3
import sys

from PyQt5.QtWidgets import (QWidget, QAction, QLabel, QLineEdit, QPushButton,
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
        actionFileSave = QAction('&Save', self)
        actionFileSave.triggered.connect(self.core.save)
        actionFileDraw = QAction('&Draw', self)
        actionFileDraw.triggered.connect(self.core.draw)
        actionSensorsAdd = QAction('&Add', self)
        actionSensorsDel = QAction('&Delete', self)
        actionAbout = QAction('&About', self)

        menuFile = self.menuBar().addMenu('&File')
        menuFile.addAction(actionFileSave)
        menuFile.addAction(actionFileDraw)
        menuView = self.menuBar().addMenu('&View')
        menuSensors = self.menuBar().addMenu('&Sensors')
        menuSensors.addAction(actionSensorsAdd)
        menuSensors.addAction(actionSensorsDel)
        self.menuBar().addAction(actionAbout)

        self.statusBar().showMessage('Приложение запущено.')

        self.periodLabel = QLabel('Период опроса, сек.:')
        self.periodEdit = QLineEdit(self.core.period)
        self.periodEdit.setValidator(QIntValidator())
        
        self.checkBox = QCheckBox('Имена и значения')
        self.checkBox.toggle()
        self.checkBox.stateChanged.connect(self.changeRow)

        self.textEdit = QTextEdit()
        self.textEdit.setVerticalScrollBarPolicy(2)
        self.textEdit.setToolTip("Action log.")

        self.btnStartStop = QPushButton('Start', self)
        self.btnStartStop.clicked.connect(self.onStartStop)
        self.btnStartStop.setCheckable(True)

        self.btnClear = QPushButton('Clear', self)
        self.btnClear.clicked.connect(self.textEdit.clear)

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
        grid.addWidget(self.periodLabel, 0, 1)
        grid.addWidget(self.periodEdit, 0, 2)
        grid.addWidget(self.checkBox, 1, 1, 1, 2)
        grid.addWidget(self.btnStartStop, 0, 0)
        grid.addWidget(self.btnClear, 1, 0)
        grid.addWidget(self.textEdit, 2, 0, 1, 3)
        grid.addWidget(self.table, 0, 3, 3, 1)
        widget = QWidget()
        widget.setLayout(grid)
        self.setCentralWidget(widget)

        self.setGeometry(300, 200, 500, 400)
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
        self.statusBar().setSizeGripEnabled(False)
        self.setWindowTitle('Observer')
        self.show()
        self.core.dataAdded.connect(self.onDataAdded)

        if len(sys.argv) > 1:
            if sys.argv[1] == '-s':
                if len(sys.argv) > 2:
                    if sys.argv[2].isdigit():
                        self.periodEdit.setText(sys.argv[2])
                self.btnStartStop.click()  
        


    def onStartStop(self):
        """onStartStop()"""
        if self.core.timer.isActive():
            self.core.stop()
            self.periodEdit.setEnabled(True)
            self.btnStartStop.setText('Start')
            self.statusBar().showMessage('Остановлено.')     
        else:
            self.core.period = self.periodEdit.text()
            self.periodEdit.setEnabled(False)
            self.btnStartStop.setText('Stop')
            self.statusBar().showMessage('Запущено...')
            self.table.clearContents()
            self.core.start()



    def changeRow(self, state):
        """changeRow(state) - изменение отображения всей информации в колонках"""
        if state == Qt.Checked:
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
                    self.core.sensors[key][0] = item.text()
                    #self.core.save()
                    print(key)
        self.table.clearSelection()
                
    def onLogged(self, log):
        """onLogged(log, mode)"""
        self.textEdit.append(log)
        #for mode in modes:
        #    if mode == 'l':
        #        self.textEdit.append(log)
        #    elif mode == 's':
        #        self.statusBar().showMessage(log)
        #    elif mode == 'f':
        #        os.makedirs(directory, 0o777, True)
        #        with open('{0}\\{1}.csv'.format(directory, date.strftime('%Y.%m.%d')), 'a') as file:
         


    def onDataAdded(self):
        """onDataAdded()"""

        self.table.setRowCount(len(self.core.sensors))
        if self.table.rowCount() <= 20:
            self.table.setMinimumHeight(25 + self.table.rowCount() * 23)
        i = 0
        for key in self.core.sensors.keys():
            if self.core.sensors[key][1] != '':
                self.table.setRowHeight(i, 23)
                self.table.setItem(i, 0, QTableWidgetItem(self.core.sensors[key][1]))
                self.table.setItem(i, 1, QTableWidgetItem(self.core.sensors[key][0]))
                self.table.setItem(i, 2, QTableWidgetItem(key))
                #self.table.item(i, 1).setBackground(Qt.red)
                i += 1
        self.table.setRowCount(i)
        self.table.sortItems(1)