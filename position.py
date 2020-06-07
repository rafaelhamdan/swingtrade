import datetime
import sys
import time

from calculator import Calculator
from util import gui
from util.table import NumericItem, formatFloatToMoney

from PySide2.QtGui import QColor, QBrush
from PySide2.QtWidgets import QTableWidget, QTableWidgetItem
from PySide2.QtCore import QThread, Signal, Slot, Qt, QObject, QTimer
import yfinance as yf

class FetchPriceWorker(QObject):
    fetchingFinished = Signal(dict)

    def __init__(self):
        super().__init__()
        self.codes = dict()

    @Slot(dict)
    def setCodes(self, codes):
        self.codes = codes

    @Slot()
    def fetch(self):
        ## Fetch price for each code
        data = {}
        for code in self.codes:
            try:
                # Append .SA (Sociedade Anomima) for brazilian stocks
                stock = yf.Ticker(code + '.SA')
                prices = stock.history(period="minute")
                # Safe guard in case we don't find the stock due to any issue in yfinance
                if (len(prices['Close']) > 0):
                    data[code] = prices['Close'][0]
            except:
                # Avoid threading dying due to no internet connection
                pass
        self.fetchingFinished.emit(data)

class FetchPriceController(QObject):
    INTERVAL_TO_FETCH_IN_SECONDS = 1
    fetchingFinished = Signal(dict)

    _stopTimer = Signal()
    _codesUpdated = Signal(dict)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.shouldExit = False
        self.thread= QThread()

        self.worker = FetchPriceWorker()
        self.worker.moveToThread(self.thread)
        self.worker.fetchingFinished.connect(self.fetchingFinished)
        self._codesUpdated.connect(self.worker.setCodes)

        # A timer will trigger price fetch on a specified interval.
        # Though this should probably be run on the thread, doing makes
        # QThread.wait block if we don't specify a timeout.
        self.fetchTimer = QTimer(self)
        self.fetchTimer.setInterval(self.INTERVAL_TO_FETCH_IN_SECONDS * 1000)
        self.fetchTimer.timeout.connect(self.worker.fetch)
        self._stopTimer.connect(self.fetchTimer.stop)

        self.thread.started.connect(self.fetchTimer.start)
        self.thread.started.connect(self.worker.fetch)

    def updateCodes(self, codes):
        self._codesUpdated.emit(codes)

    @Slot()
    def quit(self):
        self._stopTimer.emit()
        self.thread.quit()
        self.thread.wait(5000)


class Position(QObject):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.ui = gui.load_ui('./windows/position.ui')
        self.db = db

        self.stockTable = self.ui.findChild(QTableWidget, 'stock_table')
        self.currentValues = {}
        
        # Create thread to fetch prices
        self.fetchPriceController = FetchPriceController(self)
        self.fetchPriceController.fetchingFinished.connect(self.updateCurrentPrices)

        self.initTableHeaders()
        self.updateWindow()

        self.fetchPriceController.thread.start()

    def updateCurrentPrices(self, data):
        self.currentValues = data
        self.updateWindow()

    def stopThreads(self):
        self.fetchPriceController.quit()

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
        self.fetchPriceController.updateCodes(codesToFetch)

    def getUi(self):
        return self.ui
