import datetime
import sys
import time

from calculator import Calculator
from util import gui
from util.table import NumericItem, formatFloatToMoney

from PySide2.QtGui import QColor, QBrush
from PySide2.QtWidgets import QTableWidget, QTableWidgetItem
from PySide2.QtCore import QThread, Signal, Qt, QObject, QMutex
import yfinance as yf

class FetchingPriceFinished(QObject):
    signal = Signal(dict)

class FetchPriceThread(QThread):
    INTERVAL_TO_FETCH_IN_SECONDS = 10

    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.signal = FetchingPriceFinished()
        self.mutex = QMutex()
        self.codesToFetch = []

    def setCodesToFetch(self, codes):
        self.mutex.lock()
        self.codesToFetch = codes
        self.mutex.unlock()

    def run(self):
        while True:
            # Copy codes.. is this working? Is python really copying this?
            self.mutex.lock()
            codes = list(self.codesToFetch)
            self.mutex.unlock()
            # Fetch price for each code
            data = {}
            for code in codes:
                # Append .SA (Sociedade Anomima) for brazilian stocks
                stock = yf.Ticker(code + '.SA')
                prices = stock.history(period="minute")
                data[code] = prices['Close'][0]
            self.signal.signal.emit(data)
            time.sleep(self.INTERVAL_TO_FETCH_IN_SECONDS)

class Position:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/position.ui')
        self.db = db

        self.stockTable = self.ui.findChild(QTableWidget, 'stock_table')
        self.currentValues = {}
        
        self.fetchingPriceThread = FetchPriceThread()

        self.initTableHeaders()
        self.updateWindow()

        self.fetchingPriceThread.start()
        self.fetchingPriceThread.signal.signal.connect(self.updateCurrentPrices)

    def updateCurrentPrices(self, data):
        self.currentValues = data
        self.updateWindow()

    def stopThreads(self):
        self.fetchingPriceThread.terminate()

    def updateWindow(self):
        self.updateTable()

    def initTableHeaders(self):
        self.stockTable.setRowCount(0)
        self.stockTable.setColumnCount(5)
        self.stockTable.setHorizontalHeaderLabels(['Código', 'Qnt.', 'Valor médio (R$)', 'Valor atual (R$)', 'Lucro/prejuízo (R$)'])
        self.stockTable.setColumnWidth(2, self.stockTable.parent().width()*0.25)
        self.stockTable.setColumnWidth(3, self.stockTable.parent().width()*0.25)
        self.stockTable.setColumnWidth(4, self.stockTable.parent().width()*0.25)

    def updateTable(self):
        self.stockTable.setSortingEnabled(False)
        currentDate = datetime.datetime.now()
        self.fillTable(currentDate.year)
        self.stockTable.setSortingEnabled(True)

    def getBackgroundColor(self, value):
        if (value < 0):
            return QColor('red')
        elif (value > 0):
            return QColor('green')
        else:
            return QColor('white')

    def setCurrentValue(self, row, column, code):
        # Get current value
        currentValue = 0.0
        if (code in self.currentValues):
            currentValue = self.currentValues[code]
        # Set data on row
        currentValueItem = NumericItem(formatFloatToMoney(currentValue))
        currentValueItem.setData(Qt.UserRole, currentValue)
        self.stockTable.setItem(row, column, currentValueItem)
        return currentValue

    def setProfitValue(self, row, column, amount, currentValue, avgValue):
        # Get profit value
        profit = 0.0
        if (currentValue > 0):
            calculator = Calculator()
            totalSellingValue = calculator.getTransactionValueWithTaxes(amount, currentValue, True)
            profit = totalSellingValue - (amount*avgValue)
        # Set data on row
        profitItem = NumericItem(formatFloatToMoney(profit))
        profitItem.setData(Qt.UserRole, profit)
        self.stockTable.setItem(row, column, profitItem)
        self.stockTable.item(row, column).setBackground(self.getBackgroundColor(profit))

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
        codesToFetch = []
        for row in rows:
            codesToFetch.append(row[0])
            # TODO: Extract columns' indexes to variables
            for i in range(0, 3):
                if i == 0:
                    item = QTableWidgetItem(row[0])
                # Column 1 and 2 are amount and value, respectively, use numerical
                elif i == 1:
                    item = NumericItem(str(row[i]))
                    item.setData(Qt.UserRole, row[i])
                elif i == 2:
                    item = NumericItem(formatFloatToMoney(row[i]))
                    item.setData(Qt.UserRole, row[i])
                self.stockTable.setItem(rowIndex, i, item)
            # Set current value and profit
            currentValue = self.setCurrentValue(rowIndex, 3, row[0])
            self.setProfitValue(rowIndex, 4, row[1], currentValue, row[2])
            rowIndex = rowIndex + 1
        self.fetchingPriceThread.setCodesToFetch(codesToFetch)

    def getUi(self):
        return self.ui
