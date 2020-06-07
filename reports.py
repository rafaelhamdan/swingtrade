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

        self.button = self.ui.findChild(QPushButton, 'report_button')
        self.button.clicked.connect(self.generateReport)

        self.updateAvailableReports()

    def getAvailableReports(self):
        return {'': 'Selecione um relatório', 'monthly' : 'Relatório mensal de lucros e prejuízos'}

    def updateWindow(self):
        pass

    def updateAvailableReports(self):
        for k,v in self.getAvailableReports().items():
            self.reportOptions.addItem(v, k)

    def generateReport(self):
        if (not self.reportOptions.currentData()):
            QMessageBox.critical(self.ui, 'ERRO', 'Por favor selecione um tipo de relatório', QMessageBox.StandardButton.Abort)
            return
        reportType = self.reportOptions.currentData()
        calculator = Calculator()
        report = []
        # Given the report type, generate it
        if (reportType == 'monthly'):
            report = calculator.getMonthlyReport(self.db.getOrdersInAscendingDate())
        else:
            assert(0)
        if (len(report) == 0):
            QMessageBox.critical(self.ui, 'ERRO', 'Você não possui ordens cadastradas para gerar esse relatório', QMessageBox.StandardButton.Abort)
            return

        self.showReport(report)

    def showReport(self, data):
        self.report = Report()
        self.report.showMonthlyReport(data)

    def getUi(self):
        return self.ui
