import sys

from calculator import Calculator
from util import gui
from util.table import NumericItem, formatFloatToMoney

from PySide2.QtWidgets import QComboBox, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem
from PySide2.QtCore import SIGNAL, QObject
from PySide2 import QtCore

class Extract:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/extract.ui')
        self.db = db

        self.year = self.ui.findChild(QComboBox, 'extract_year')

        self.button = self.ui.findChild(QPushButton, 'extract_button')
        self.button.clicked.connect(self.checkYearAndUpdateTable)

        self.stockTable = self.ui.findChild(QTableWidget, 'stock_table')

        self.initTableHeaders()
        self.updateWindow()

    def updateWindow(self):
        self.updateAvailableYears()
        self.updateTable()

    def updateAvailableYears(self):
        # Hold year currently selected in window
        prevYearSelected = self.year.currentData()
        # Update years according to what's in database
        self.year.clear()
        self.year.addItem('ANO', None)
        availableYears = self.db.getYearsWithOrders()
        index = 1
        for year in availableYears:
            self.year.addItem(year, int(year))
            if (int(year) == prevYearSelected):
                self.year.setCurrentIndex(index)
            index = index + 1

    def initTableHeaders(self):
        self.stockTable.setRowCount(0)
        self.stockTable.setColumnCount(4)
        self.stockTable.setHorizontalHeaderLabels(['Código', 'Qnt.', 'Valor médio (R$)', 'Total (R$)'])

    def checkYearAndUpdateTable(self):
        if (not self.year.currentData()):
            QMessageBox.critical(self.ui, 'ERRO', 'Por favor selecione um ano', QMessageBox.StandardButton.Abort)
            return
        self.updateTable()

    def updateTable(self):
        self.stockTable.setSortingEnabled(False)
        year = self.year.currentData()
        self.fillTable(year)
        self.stockTable.setSortingEnabled(True)

    def fillTable(self, year):
        if (not year):
            return
        ordersUpToYear = self.db.getOrdersInAscendingDateUpToYear(year)
        calculator = Calculator()
        ret = calculator.getYearExtract(ordersUpToYear)
        # Now extract from return the 
        # TODO: Error out if we have negative number of stocks
        rows = []
        for k, v in ret.items():
            amount = v[0]
            avgValue = v[1]
            if (amount > 0):
                rows.append([k, amount, avgValue])
        self.stockTable.setRowCount(len(rows))
        rowIndex = 0
        for row in rows:
            # TODO: Extract columns' indexes to variables
            for i in range(0, 3):
                if i == 0:
                    item = QTableWidgetItem(row[0])
                # Column 1 and 2 are amount and value, respectively, use numerical
                elif i == 1:
                    item = NumericItem(str(row[i]))
                    item.setData(QtCore.Qt.UserRole, row[i])
                elif i == 2:
                    item = NumericItem(formatFloatToMoney(row[i]))
                    item.setData(QtCore.Qt.UserRole, row[i])
                self.stockTable.setItem(rowIndex, i, item)
            # Add total includig taxes
            totalValue = row[1]*row[2]
            totalItem = NumericItem(formatFloatToMoney(totalValue))
            totalItem.setData(QtCore.Qt.UserRole, totalValue)
            self.stockTable.setItem(rowIndex, 3, totalItem)
            rowIndex = rowIndex + 1

    def getUi(self):
        return self.ui
