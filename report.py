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
        self.ui.resize(800, 600)

        self.webView = QWebEngineView()
        self.env = Environment(loader=FileSystemLoader('html/'))

        layout = self.ui.findChild(QVBoxLayout, 'layout')
        layout.addWidget(self.webView)

    def showMonthlyReport(self, data):
        # Extract months from data
        months = list(data.keys())
        # Extract both total value and profit value
        total_sales = []
        total_profit = []
        for value in data.values():
            total_sales.append(round(value[0], 2))
            total_profit.append(round(value[1], 2))
        data = [{'name': 'Total de vendas', 'data': total_sales, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'blue'},
                {'name': 'Lucro/prejuízo', 'data': total_profit, 'tooltip': {'valuePrefix': 'R$'}, 'color': 'green'}]
        self.webView.setHtml(self.env.get_template('report_monthly.html').render(chart_data=json.dumps(data), chart_months=json.dumps(months)))
        self.ui.show()
