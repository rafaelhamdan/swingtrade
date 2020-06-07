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
        calculator = Calculator()
        reportType = self.reportOptions.currentData()
        # Given the report type, generate it
        if (reportType == 'monthly'):
            reportData = calculator.getMonthlyReport(self.db.getOrdersInAscendingDate())
            if (len(reportData) == 0):
                QMessageBox.critical(self.ui, 'ERRO', 'Não há dados cadastrados para gerar o relatório mensal de lucros e prejuízos', QMessageBox.StandardButton.Abort)
                return
            self.report = Report()
            self.report.showMonthlyReport(reportData)
        else:
            assert(0)

    def getUi(self):
        return self.ui
