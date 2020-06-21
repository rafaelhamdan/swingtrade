import sys

from util import gui
from calculator import Calculator
from util.table import NumericItem, formatFloatToMoney

from PySide2.QtGui import QColor, QBrush
from PySide2.QtWidgets import QAbstractItemView, QLabel, QLineEdit, QTableWidget, QTableWidgetItem
from PySide2.QtCore import SIGNAL, QObject
from PySide2 import QtCore

class Profit:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/profit.ui')
        self.db = db

        self.orderTable = self.ui.findChild(QTableWidget, 'order_table')
        self.filterText = self.ui.findChild(QLineEdit, 'filter_text')
        self.filterText.textChanged.connect(self.applyFilter)

        self.totalSales = self.ui.findChild(QLabel, 'total_sales')
        self.totalProfit = self.ui.findChild(QLabel, 'total_profit')

        self.initTable()
        self.updateWindow()

    def initTable(self):
        self.orderTable.setRowCount(0)
        self.orderTable.setColumnCount(6)
        self.orderTable.setHorizontalHeaderLabels(['Data', 'Código', 'Valor médio de compra (R$)', 'Qnt.', 'Valor de venda (R$)', 'Lucro/prejuízo (R$)'])
        self.orderTable.setColumnWidth(1, self.orderTable.parent().width()*0.15)
        self.orderTable.setColumnWidth(2, self.orderTable.parent().width()*0.30)
        self.orderTable.setColumnWidth(3, self.orderTable.parent().width()*0.10)
        self.orderTable.setColumnWidth(4, self.orderTable.parent().width()*0.25)
        self.orderTable.setColumnWidth(5, self.orderTable.parent().width()*0.25)
        self.orderTable.setSelectionBehavior(QAbstractItemView.SelectRows)

    def getBackgroundColor(self, value):
        if (value < 0):
            return QColor('red')
        elif (value > 0):
            return QColor('green')
        else:
            return QColor('white')

    def getColor(self, value):
        if (value < 0):
            return 'red'
        elif (value > 0):
            return 'green'
        else:
            return 'black'

    def updateWindow(self):
        self.updateTable()

    def updateTable(self):
        self.orderTable.setSortingEnabled(False)
        self.fillTable()
        self.orderTable.setSortingEnabled(True)

    def fillTable(self):
        # Calculate profits and losses per sell operation
        calculator = Calculator(self.db)
        orders = self.db.getOrdersInAscendingDate()
        rows = calculator.getProfitsAndLosses(orders)
        # Print data
        self.orderTable.setRowCount(len(rows))
        rowIndex = 0
        for row in rows:
            # TODO: Extract columns' indexes to variables
            for i in range(0, 6):
                if i == 0 or i == 1:
                    item = QTableWidgetItem(row[i])
                # Column 3 is amount, numeric item
                elif i == 3:
                    item = NumericItem(str(row[i]))
                    item.setData(QtCore.Qt.UserRole, row[i])
                # Columns 2, 4 and 5 are values
                else:
                    item = NumericItem(formatFloatToMoney(row[i]))
                    item.setData(QtCore.Qt.UserRole, row[i])
                self.orderTable.setItem(rowIndex, i, item)
            self.orderTable.item(rowIndex, 5).setBackground(self.getBackgroundColor(row[5]))
            rowIndex = rowIndex + 1
        # Apply filter and update total values text
        self.applyFilter(self.filterText.text())

    def applyFilter(self, text):
        for i in range(0, self.orderTable.rowCount()):
            match = len(text) == 0
            for j in range(0, self.orderTable.columnCount()):
                if (match):
                    break
                item = self.orderTable.item(i, j)
                if (text.lower() in item.text().lower()):
                    match = True
            self.orderTable.setRowHidden(i, not match)
        self.setTotalValues()

    def setTotalValues(self):
        # Go through values in column summing up
        sales = 0
        profit = 0
        for i in range(0, self.orderTable.rowCount()):
            if (self.orderTable.isRowHidden(i)):
                continue
            sales += self.orderTable.item(i, 3).data(QtCore.Qt.UserRole) * self.orderTable.item(i, 4).data(QtCore.Qt.UserRole)
            profit += self.orderTable.item(i, 5).data(QtCore.Qt.UserRole)
        self.totalSales.setText(formatFloatToMoney(sales))
        self.totalProfit.setText(formatFloatToMoney(profit))
        self.totalProfit.setStyleSheet('QLabel { color: ' + self.getColor(profit) + ' } ')

    def getUi(self):
        return self.ui
