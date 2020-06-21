import sys

from util import gui
from util.table import formatFloatToMoney
from PySide2.QtWidgets import QLineEdit, QMessageBox

class Init:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/init.ui')
        self.db = db
        
        self.taxFee = self.ui.findChild(QLineEdit, 'tax_fee')
        self.taxRate = self.ui.findChild(QLineEdit, 'tax_rate')
        self.lossToDiscount = self.ui.findChild(QLineEdit, 'loss_to_discount')

        self.taxFee.editingFinished.connect(self.updateValues)
        self.taxRate.editingFinished.connect(self.updateValues)
        self.lossToDiscount.editingFinished.connect(self.updateValues)

        self.updateWindow()

    def showError(self):
        QMessageBox.critical(self.ui, 'ERRO', 'O valor preenchido deve ser um número válido', QMessageBox.StandardButton.Abort)

    def updateValues(self):
        taxFee = self.taxFee.text().replace(',', '.')
        taxRate = self.taxRate.text().replace(',', '.')
        lossToDiscount = self.lossToDiscount.text().replace(',', '.')

        try:
            taxFee = float(taxFee)
            taxRate = float(taxRate)
            lossToDiscount = float(lossToDiscount)
        except:
            self.showError()
            return

        self.db.updateTaxValues(taxFee, taxRate, lossToDiscount)
        self.updateWindow()

    def updateWindow(self):
        taxValues = self.db.getTaxValues()
        self.taxFee.setText(formatFloatToMoney(taxValues[0]))
        self.taxRate.setText(formatFloatToMoney(taxValues[1]))
        self.lossToDiscount.setText(formatFloatToMoney(taxValues[2]))

    def getUi(self):
        return self.ui
