import sys

from util import gui
from calculator import Calculator
from util.table import NumericItem, formatFloatToMoney

from PySide2.QtWidgets import QAbstractItemView, QCalendarWidget, QComboBox, QDialogButtonBox, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem
from PySide2.QtCore import SIGNAL, QObject
from PySide2 import QtCore

class ListOrder:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/list_order.ui')
        self.db = db

        self.orderTable = self.ui.findChild(QTableWidget, 'order_table')
        self.filterText = self.ui.findChild(QLineEdit, 'filter_text')
        self.filterText.textChanged.connect(self.applyFilter)

        self.eraseOrders = self.ui.findChild(QPushButton, 'erase_orders')
        self.eraseOrders.clicked.connect(self.eraseSelectedOrders)

        self.addOrderButton = self.ui.findChild(QPushButton, 'add_order')
        self.addOrderButton.clicked.connect(self.openAddOrderDialog)

        self.initTable()
        self.updateWindow()

    def initTable(self):
        self.orderTable.setRowCount(0)
        self.orderTable.setColumnCount(7)
        self.orderTable.setHorizontalHeaderLabels(['Data', 'Tipo', 'Código', 'Qnt.', 'Valor (R$)', 'Total (R$)', 'ID'])
        self.orderTable.setColumnHidden(6, True)
        self.orderTable.setSelectionBehavior(QAbstractItemView.SelectRows)

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
            # We are not using company name since it appears in only some spreadsheets
            del order[4]
            # Is it a sell or buy operation?
            isSell = order[2] == 'V'
            # TODO: Extract columns' indexes to variables
            for i in range(1,6):
                # Column 2 comes as C or V from database
                if i == 2:
                    item = QTableWidgetItem('Venda' if isSell else 'Compra')
                # Column 4 and 5 are amount and value, respectively
                # Should be sotred as numeric and value formatted to 2 decimal fields
                elif i == 4:
                    item = NumericItem(str(order[i]))
                    item.setData(QtCore.Qt.UserRole, order[i])
                elif i == 5:
                    item = NumericItem(formatFloatToMoney(order[i]))
                    item.setData(QtCore.Qt.UserRole, order[i])
                else:
                    item = QTableWidgetItem(str(order[i]))
                self.orderTable.setItem(row, i-1, item)
            # Add total includig taxes
            calculator = Calculator()
            totalValue = calculator.getTransactionValueWithTaxes(order[4], order[5], isSell)
            totalItem = NumericItem(formatFloatToMoney(totalValue))
            totalItem.setData(QtCore.Qt.UserRole, totalValue)
            self.orderTable.setItem(row, 5, totalItem)
            # Hidden ID column
            idItem = QTableWidgetItem('')
            idItem.setData(QtCore.Qt.UserRole, order[0])
            self.orderTable.setItem(row, 6, idItem)
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

    def eraseSelectedOrders(self):
        # Check if any row selected
        selectedRows = self.orderTable.selectionModel().selectedRows()
        if (len(selectedRows) == 0):
            QMessageBox.critical(self.ui, 'ERRO', 'Selecione uma ou mais ordens para apagar', QMessageBox.StandardButton.Abort)
            return
        # Confirm request...
        response = QMessageBox.question(self.ui, 'Apagar ordens', 
                                        'Tem certeza que deseja apagar as ' + str(len(selectedRows)) + ' ordens selecionadas?',
                                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Abort)
        if (response != QMessageBox.StandardButton.Ok):
            return False
        # Erase them!!
        idsToErase = []
        for row in selectedRows:
            idsToErase.append(self.orderTable.item(row.row(), 6).data(QtCore.Qt.UserRole))
        self.db.eraseOrdersById(idsToErase)
        self.updateTable()

    def openAddOrderDialog(self):
        self.addOrderUi = gui.load_ui('./windows/dialog_add_order.ui')
        self.addOrderUiAddButon = self.addOrderUi.findChild(QPushButton, 'add')
        self.addOrderUiAddButon.clicked.connect(self.addOrder)
        self.addOrderUiCancelButon = self.addOrderUi.findChild(QPushButton, 'cancel')
        self.addOrderUiCancelButon.clicked.connect(self.addOrderUi.close)
        self.addOrderUi.show()

    def addOrder(self):
        # These are well behaved, no need to do any checking
        orderDate = self.addOrderUi.findChild(QCalendarWidget, 'date').selectedDate().toPython()
        orderType = self.addOrderUi.findChild(QComboBox, 'type').currentText()
        # Check code
        orderCode = self.addOrderUi.findChild(QLineEdit, 'code').text()
        if (len(orderCode) < 4):
            QMessageBox.critical(self.addOrderUi, 'ERRO', 'Preencha o código do papel (ao menos 4 dígitos)', QMessageBox.StandardButton.Abort)
            return
        # Check amount
        orderAmount = 0
        try:
            orderAmount = int(self.addOrderUi.findChild(QLineEdit, 'amount').text())
        except:
            QMessageBox.critical(self.addOrderUi, 'ERRO', 'Preencha a quantidade com um valor numérico', QMessageBox.StandardButton.Abort)
            return
        # Check value (comma-separated)
        orderValue = 0.0
        try:
            orderValue = float(self.addOrderUi.findChild(QLineEdit, 'value').text().replace(',', '.'))
        except:
            QMessageBox.critical(self.addOrderUi, 'ERRO', 'Preencha o valor corretamente (separe apenas os centavos com . ou ,)', QMessageBox.StandardButton.Abort)
            return
        self.db.addOrders([[orderDate, 'C' if orderType == 'Compra' else 'V', orderCode, '', orderAmount, orderValue]])
        self.updateTable()
        self.addOrderUi.close()

    def getUi(self):
        return self.ui
