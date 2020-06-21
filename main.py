import sys

from database import *
from extract import *
from init import *
from list_order import *
from position import *
from profit import *
from register_order import *
from reports import *
from util import gui

from PySide2.QtWidgets import QApplication, QMessageBox, QTabWidget, QVBoxLayout

class Main:
    def __init__(self):
        # Create the Qt Application
        self.app = QApplication(sys.argv)

        # Create and show the form
        self.mainWindow = gui.load_ui('./windows/main.ui')
        self.db = Database()

        # Setup tab widgets
        self.setupTabWidgets()

        # Check database is valid
        if (not self.db.isValid()):
            QMessageBox.critical(self.mainWindow, 'ERRO', 'Impossível encontrar arquivo de banco de dados', QMessageBox.StandardButton.Abort)
            exit(-1)

        self.mainWindow.resize(1024, 768)
        self.mainWindow.show()
        sys.exit(self.app.exec_())

    def setupTabWidgets(self):
        self.tabWindow = self.mainWindow.findChild(QTabWidget, 'tab_widget')

        initLayout = self.mainWindow.findChild(QVBoxLayout, 'init_layout')
        self.init = Init(self.db)
        initLayout.addWidget(self.init.getUi())

        listOrderLayout = self.mainWindow.findChild(QVBoxLayout, 'list_order_layout')
        self.listOrder = ListOrder(self.db)
        listOrderLayout.addWidget(self.listOrder.getUi())

        self.registerOrder = RegisterOrder(self.db)
        self.tabWindow.addTab(self.registerOrder.getUi(), 'Importar ordens')

        self.extract = Extract(self.db)
        self.tabWindow.addTab(self.extract.getUi(), 'Extratos anuais')

        self.profit = Profit(self.db)
        self.tabWindow.addTab(self.profit.getUi(), 'Lucros/Prejuízos')
        
        self.reports = Reports(self.db)
        self.tabWindow.addTab(self.reports.getUi(), 'Relatórios')

        self.position = Position(self.app, self.db)
        self.tabWindow.addTab(self.position.getUi(), 'Posição')
        self.app.aboutToQuit.connect(self.position.stopThreads)

        # Update windows once tab changes
        self.tabWindow.currentChanged.connect(self.updateWindow)

    def updateWindow(self, index):
        # Once the tab has gone to list the orders, update it
        # TODO: Only update/re-render if the database has changed since we started
        if (index == 0):
            self.init.updateWindow()
        elif (index == 1):
            self.listOrder.updateWindow()
        elif (index == 2):
            self.registerOrder.updateWindow()
        elif (index == 3):
            self.extract.updateWindow()
        elif (index == 4):
            self.profit.updateWindow()
        elif (index == 5):
            self.reports.updateWindow()
        elif (index == 6):
            self.position.updateWindow()
        else:
            assert(0)

if __name__ == '__main__':
    main = Main()
