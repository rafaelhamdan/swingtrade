import sys

from util import gui
from calculator import Calculator
from util.table import NumericItem, formatFloatToMoney

from PySide2.QtWidgets import QLineEdit, QTableWidget, QTableWidgetItem
from PySide2.QtCore import SIGNAL, QObject
from PySide2 import QtCore

class ListOrder:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/list_order.ui')
        self.db = db

        self.orderTable = self.ui.findChild(QTableWidget, 'order_table')
        self.filterText = self.ui.findChild(QLineEdit, 'filter_text')
        self.filterText.textChanged.connect(self.applyFilter)

        self.initTableHeaders()
        self.updateWindow()

    def initTableHeaders(self):
        self.orderTable.setRowCount(0)
        self.orderTable.setColumnCount(7)
        self.orderTable.setHorizontalHeaderLabels(['Data', 'Tipo', 'Código', 'Empresa', 'Qnt.', 'Valor (R$)', 'Total (R$)'])

    def updateWindow(self):
        self.updateTable()

    def updateTable(self):
        self.orderTable.setSortingEnabled(False)
        self.fillTable()
        self.orderTable.setSortingEnabled(True)

    def fillTable(self):
        # Get orders from database
        orders = self.db.getOrdersInAscendingDate()
        # Now let's print data into table effectively
        self.orderTable.setRowCount(len(orders))
        row = 0
        for order in orders:
            isSell = order[2] == 'V'
            # TODO: Extract columns' indexes to variables
            for i in range(1,7):
                # Column 2 comes as C or V from database
                if i == 2:
                    item = QTableWidgetItem('Venda' if isSell else 'Compra')
                # Column 5 and 6 are amount and value, respectively
                # Should be sotred as numeric and value formatted to 2 decimal fields
                elif i == 5:
                    item = NumericItem(str(order[i]))
                    item.setData(QtCore.Qt.UserRole, order[i])
                elif i == 6:
                    item = NumericItem(formatFloatToMoney(order[i]))
                    item.setData(QtCore.Qt.UserRole, order[i])
                else:
                    item = QTableWidgetItem(str(order[i]))
                self.orderTable.setItem(row, i-1, item)
            # Add total includig taxes
            calculator = Calculator()
            totalValue = calculator.getTransactionValueWithTaxes(order[5], order[6], isSell)
            totalItem = NumericItem(formatFloatToMoney(totalValue))
            totalItem.setData(QtCore.Qt.UserRole, totalValue)
            self.orderTable.setItem(row, 6, totalItem)
            row = row + 1
        # Re-apply filter
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

    def getUi(self):
        return self.ui
