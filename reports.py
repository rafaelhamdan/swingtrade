import sys

from calculator import Calculator
from report import Report
from util import gui

from PySide2.QtWidgets import QComboBox, QMessageBox, QPushButton

class Reports:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/reports.ui')
        self.db = db

        self.reportOptions = self.ui.findChild(QComboBox, 'report_options')
        self.reportOptions.currentIndexChanged.connect(self.reportTypeChanged)

        self.button = self.ui.findChild(QPushButton, 'report_button')
        self.button.clicked.connect(self.generateReport)

        self.year = self.ui.findChild(QComboBox, 'year')
        self.year.hide()

        self.updateAvailableReports()

    def getAvailableReports(self):
        return {'': 'Selecione um relatório',
                'monthly' : 'Relatório mensal de lucros e prejuízos',
                'yearly_free_taxes': 'Relatório por ano de lucros livres de impostos',
                'yearly_taxes': 'Relatório por ano de lucros com impostos a serem pagos'}

    def updateWindow(self):
        self.updateAvailableYears()

    def updateAvailableYears(self):
        # Update years according to what's in database
        self.year.clear()
        self.year.addItem('SELECIONE UM ANO', None)
        availableYears = self.db.getYearsWithOrders()
        for year in availableYears:
            self.year.addItem(year, int(year))

    def updateAvailableReports(self):
        for k,v in self.getAvailableReports().items():
            self.reportOptions.addItem(v, k)

    def reportTypeChanged(self, index):
        reportType = self.reportOptions.currentData()
        # Show the year for the reports that demand selecting one
        if (reportType == 'yearly_free_taxes' or reportType == 'yearly_taxes'):
            self.year.show()
        else:
            self.year.hide()

    def generateReport(self):
        if (not self.reportOptions.currentData()):
            QMessageBox.critical(self.ui, 'ERRO', 'Por favor selecione um tipo de relatório', QMessageBox.StandardButton.Abort)
            return
        calculator = Calculator()
        reportType = self.reportOptions.currentData()

        # Given the report type, generate it
        reportData = {}
        year = self.year.currentData()
        if (reportType == 'monthly'):
            reportData = calculator.getMonthlyReport(self.db.getOrdersInAscendingDate())
        elif (reportType == 'yearly_free_taxes' or reportType == 'yearly_taxes'):
            if not year:
                QMessageBox.critical(self.ui, 'ERRO', 'Selecione um ano', QMessageBox.StandardButton.Abort)
                return
            if (reportType == 'yearly_free_taxes'):
                reportData = calculator.getFreeTaxesReport(self.db.getOrdersInAscendingDate(), year)
            else:
                reportData = calculator.getPayingTaxesReport(self.db.getOrdersInAscendingDate(), year)
        else:
            assert(0)

        if (len(reportData) == 0):
            QMessageBox.critical(self.ui, 'ERRO', 'Não há dados cadastrados para gerar o relatório mensal de lucros e prejuízos', QMessageBox.StandardButton.Abort)
            return

        self.showReport(reportType, reportData, year)

    def showReport(self, reportType, reportData, year):
        self.report = Report()
        if (reportType == 'monthly'):
            self.report.showMonthlyReport(reportData)
        elif (reportType == 'yearly_free_taxes'):
            self.report.showYearlyFreeTaxesReport(reportData, year)
        elif (reportType == 'yearly_taxes'):
            self.report.showYearlyTaxesReport(reportData, year)

    def getUi(self):
        return self.ui
