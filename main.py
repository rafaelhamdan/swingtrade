import sys

from database import *
from extract import *
from list_order import *
from profit import *
from register_order import *
from util import gui

from PySide2.QtWidgets import QApplication, QMessageBox, QTabWidget, QVBoxLayout

class Main:
    def __init__(self):
        # Create the Qt Application
        app = QApplication(sys.argv)

        # Create and show the form
        self.mainWindow = gui.load_ui('./windows/main.ui')
        self.db = Database()

        # Windows for tabs
        self.tabWindow = self.mainWindow.findChild(QTabWidget, 'tab_widget')

        registerOrderLayout = self.mainWindow.findChild(QVBoxLayout, 'register_order_layout')
        self.registerOrder = RegisterOrder(self.db)
        registerOrderLayout.addWidget(self.registerOrder.getUi())

        listOrderLayout = self.mainWindow.findChild(QVBoxLayout, 'list_order_layout')
        self.listOrder = ListOrder(self.db)
        listOrderLayout.addWidget(self.listOrder.getUi())

        self.extract = Extract(self.db)
        self.tabWindow.addTab(self.extract.getUi(), 'Extratos anuais')

        self.profit = Profit(self.db)
        self.tabWindow.addTab(self.profit.getUi(), 'Lucros e Prejuízos')

        # Update windows once tab changes
        self.tabWindow.currentChanged.connect(self.updateWindow)

        # Check database is valid
        if (not self.db.isValid()):
            QMessageBox.critical(self.mainWindow, 'ERRO', 'Impossível encontrar arquivo de banco de dados', QMessageBox.StandardButton.Abort)
            exit(-1)

        self.mainWindow.show()
        sys.exit(app.exec_())

    def updateWindow(self, index):
        # Once the tab has gone to list the orders, update it
        # TODO: Only update/re-render if the database has changed since we started
        if (index == 0):
            window = self.listOrder
        elif (index == 1):
            window = self.registerOrder
        elif (index == 2):
            window = self.extract
        elif (index == 3):
            window = self.profit
        window.updateWindow()

if __name__ == '__main__':
    main = Main()
