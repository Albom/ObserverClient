#!/usr/bin/python3
import sys
from PyQt5.QtWidgets import (QMainWindow, QApplication)
import mainWindow
import observer



if __name__ == '__main__':
    app = QApplication(sys.argv)
    core = observer.Observer()
    #app.setStyle(QStyleFactory.create("Fusion"));
    ex = mainWindow.MainWindow(core)
    sys.exit(app.exec_())