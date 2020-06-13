import json
import sys

from util import gui

from jinja2 import Environment, FileSystemLoader, Template
from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PySide2.QtWidgets import QVBoxLayout

class Report:
    def __init__(self):
        self.ui = gui.load_ui('./windows/report.ui')
        self.ui.setWindowTitle('Extração de relatório')
        self.ui.resize(1000, 600)

        self.webView = QWebEngineView()
        self.env = Environment(loader=FileSystemLoader('html/'))

        layout = self.ui.findChild(QVBoxLayout, 'layout')
        layout.addWidget(self.webView)

    def showMonthlyReport(self, data):
        months = list(data.keys())
        sales = []
        profit = []
        for value in data.values():
            sales.append(round(value[0], 2))
            profit.append(round(value[1], 2))
        data = [{'name': 'Total de vendas', 'data': sales, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'blue'},
                {'name': 'Lucro/prejuízo', 'data': profit, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'green'}]
        self.webView.setHtml(self.env.get_template('report_monthly.html').render(chart_data=json.dumps(data), chart_months=json.dumps(months)))
        self.ui.show()

    def showYearlyFreeTaxesReport(self, data, year):
        xValues = list(data.keys())
        xValues.append('Total')
        sales = []
        profit = []
        total_sales = 0.0
        total_profit = 0.0
        for value in data.values():
            sales.append(round(value[0], 2))
            profit.append(round(value[1], 2))
            total_sales += value[0]
            total_profit += value[1]
        sales.append(round(total_sales, 2))
        profit.append(round(total_profit, 2))
        data = [{'name': 'Total de vendas', 'data': sales, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'blue'},
                {'name': 'Lucro/prejuízo', 'data': profit, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'green'}]
        self.webView.setHtml(self.env.get_template('report_taxes.html').render(chart_data=json.dumps(data),
                                                                               chart_months=json.dumps(xValues),
                                                                               chart_title='Relatório anual de lucros livres de impostos',
                                                                               chart_year='ANO ' + str(year)))
        self.ui.show()

    def showYearlyTaxesReport(self, data, year):
        months = list(data.keys())
        sales = []
        lossToDiscount = []
        discountedLoss = []
        profit = []
        taxToPay = []
        for value in data.values():
            sales.append(round(value[0], 2))
            lossToDiscount.append(round(value[1], 2))
            discountedLoss.append(round(value[2], 2))
            profit.append(round(value[3], 2))
            taxToPay.append(round(value[4], 2))
        data = [{'name': 'Total de vendas', 'data': sales, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'blue'},
                {'name': 'Lucro/prejuízo', 'data': profit, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'green'},
                {'name': 'Prejuizo acumulado', 'data': lossToDiscount, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'red'},
                {'name': 'Prejuizo abatido', 'data': discountedLoss, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'orange'},
                {'name': 'Imposto', 'data': taxToPay, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'black'}]
        self.webView.setHtml(self.env.get_template('report_taxes.html').render(chart_data=json.dumps(data),
                                                                               chart_months=json.dumps(months),
                                                                               chart_title='Relatório anual de impostos a serem pagos',
                                                                               chart_year='ANO ' + str(year)))
        self.ui.show()
