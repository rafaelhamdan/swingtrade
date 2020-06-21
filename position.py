import datetime
import sys
import time

from calculator import Calculator
from util import gui
from util.table import NumericItem, formatFloatToMoney

from PySide2.QtGui import QColor, QBrush
from PySide2.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem
from PySide2.QtCore import QThread, Signal, Slot, Qt, QObject, QTimer
import yfinance as yf

class FetchPriceWorker(QObject):
    INTERVAL_TO_FETCH_IN_SECONDS = 10
    INTERVAL_RETRY_NO_DATA_IN_SECONDS = 1
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
        try:
            # Append .SA (Sociedade Anomima) for brazilian stocks
            stockData = yf.download(" ".join([x + ".SA" for x in self.codes]), period="minute", progress=False)
            if stockData.shape[0]:
                closeData = stockData.iloc[0]['Close']
                # Assemble dictionary with stock name and price in the right order.
                data = dict(zip([x[:-3] for x in list(closeData.index)], list(closeData)))
        except:
            # Avoid threading dying due to no internet connection
            pass

        if data:
            self.fetchingFinished.emit(data)
            interval = __class__.INTERVAL_TO_FETCH_IN_SECONDS
        else:
            interval = __class__.INTERVAL_RETRY_NO_DATA_IN_SECONDS

        QTimer.singleShot(interval * 1000, self.fetch)

class FetchPriceController(QObject):
    fetchingFinished = Signal(dict)
    THREAD_SYNC_TIMEOUT_SECONDS = 5

    _codesUpdated = Signal(dict)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.shouldExit = False
        self.thread = QThread()

        self.worker = FetchPriceWorker()
        self.worker.moveToThread(self.thread)
        self.worker.fetchingFinished.connect(self.fetchingFinished)
        self._codesUpdated.connect(self.worker.setCodes)

        self.thread.started.connect(self.worker.fetch)
        self.thread.finished.connect(self.thread.deleteLater)

    def updateCodes(self, codes):
        self._codesUpdated.emit(codes)

    @Slot()
    def quit(self):
        self.thread.quit()
        if not self.thread.wait(self.THREAD_SYNC_TIMEOUT_SECONDS * 1000):
            self.thread.terminate()


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

        self.initTable()
        self.updateWindow()

        self.fetchPriceController.thread.start()

    def updateCurrentPrices(self, data):
        self.currentValues = data
        self.updateWindow()

    def stopThreads(self):
        self.fetchPriceController.quit()

    def updateWindow(self):
        self.updateTable()

    def initTable(self):
        self.stockTable.setRowCount(0)
        self.stockTable.setColumnCount(5)
        self.stockTable.setHorizontalHeaderLabels(['Código', 'Qnt.', 'Valor médio (R$)', 'Valor atual (R$)', 'Lucro/prejuízo (R$)'])
        self.stockTable.setColumnWidth(2, self.stockTable.parent().width()*0.25)
        self.stockTable.setColumnWidth(3, self.stockTable.parent().width()*0.25)
        self.stockTable.setColumnWidth(4, self.stockTable.parent().width()*0.25)
        self.stockTable.setSelectionBehavior(QAbstractItemView.SelectRows)

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
            calculator = Calculator(self.db)
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
        calculator = Calculator(self.db)
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
