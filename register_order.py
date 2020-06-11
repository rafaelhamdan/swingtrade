import os
import sys
import platform

from process_order import ProcessOrder
from util import gui

from PySide2.QtWidgets import QWidget, QDialogButtonBox, QMessageBox, QFileDialog, QGridLayout, QPushButton, QVBoxLayout
from PySide2.QtCore import SIGNAL, Qt, QObject

class FileDialog(QFileDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup()
        self.setWindowFlags(Qt.Widget)
        if platform.system() == "Linux":
            self.setOption(QFileDialog.DontUseNativeDialog)
        self.show()
        self.hideButtons()
    
    def keyPressEvent(self, event):
        # Ignore key press events here
        pass

    def setup(self):
        self.setNameFilter('Extrato CEI Negociação de Ativos (*.xls)')

    def hideButtons(self):
        # Hide open and cancel buttons that may wipe the file dialog widget
        buttonBox = self.findChild(QDialogButtonBox)
        if (buttonBox):
            if (buttonBox.button(QDialogButtonBox.Open)):
                buttonBox.button(QDialogButtonBox.Open).hide()
            if (buttonBox.button(QDialogButtonBox.Cancel)):
                buttonBox.button(QDialogButtonBox.Cancel).hide()

class RegisterOrder:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/register_order.ui')
        self.db = db

        parent = self.ui.findChild(QWidget, 'Form')
        fileLayout = self.ui.findChild(QVBoxLayout, 'file_layout')
        self.fileDialog = FileDialog(parent)
        self.fileDialog.accepted.connect(self.processFiles)
        fileLayout.addWidget(self.fileDialog)

        self.processFilesButton = self.ui.findChild(QPushButton, 'process_files_button')
        self.processFilesButton.clicked.connect(self.processFiles)

        self.wipeOrdersButton = self.ui.findChild(QPushButton, 'wipe_orders_button')
        self.wipeOrdersButton.clicked.connect(self.wipeOrders)

        self.updateWindow()

    def updateWindow(self):
        None

    def confirmRequest(self, title):
        response = QMessageBox.question(self.ui, title,
                                        "Tem certeza que deseja continuar?\nIsso irá apagar todas as suas operações registradas nas datas presentes na planilha.",
                                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Abort)
        if (response != QMessageBox.StandardButton.Ok):
            return False
        return True

    def getSelectedFiles(self):
        files = self.fileDialog.selectedFiles()
        if (len(files) == 0 or not os.path.isfile(files[0])):
            QMessageBox.critical(self.ui, "ERRO", 'Por favor selecione um arquivo', QMessageBox.StandardButton.Abort)
            return []
        if (not self.confirmRequest("Importar operações")):
            return []
        return files

    def processFiles(self):
        self.fileDialog.show()
        files = self.getSelectedFiles()
        if (len(files) == 0):
            return

        orders = []
        for f in files:
            processor = ProcessOrder(f)
            ret = processor.processFile(f)
            if (not ret):
                errorMsg = processor.getErrorMessage()
                errorFieldMsg = processor.getErrorFieldMessage()
                if (len(errorFieldMsg) > 0):
                    errorMsg += ' (' + errorFieldMsg + ')'
                QMessageBox.critical(self.ui, "ERRO", errorMsg, QMessageBox.StandardButton.Abort)
                break
            orders.extend(ret)

        self.updateOrders(orders)

    def updateOrders(self, orders):
        if (len(orders) == 0):
            QMessageBox.critical(self.ui, "ERRO", "A planilha não contém nada a ser importado", QMessageBox.StandardButton.Abort)
            return
        # First erase orders within date-range
        dateRange = [order[0] for order in orders]
        dateRange.sort()
        numDeletedOrders = self.db.eraseOrdersWithinDateRange(dateRange[0], dateRange[-1])
        firstDateStr = dateRange[0].strftime('%d/%m/%Y')
        secondDateStr = dateRange[-1].strftime('%d/%m/%Y')
        QMessageBox.information(self.ui, "REMOÇÕES", "Removidas " + str(numDeletedOrders) + ' ordens entre ' + firstDateStr + ' e ' + secondDateStr + '!')
        # Finally insert all orders
        if (not self.db.updateOrders(orders)):
            QMessageBox.critical(self.ui, "ERRO", "Houve um erro ao atualizar o banco de dados. Todas ordens foram removidas.", QMessageBox.StandardButton.Abort)
            self.db.deleteOrders()
        else:
            QMessageBox.information(self.ui, "SUCESSO", "Planilha importada com sucesso!\nInseridas " + str(len(orders)) + " ordens!")

    def wipeOrders(self):
        if (not self.confirmRequest("Apagar operações")):
            return
        if (not self.db.deleteOrders()):
            QMessageBox.critical(self.ui, "ERRO", "Houve um erro ao limpar o banco de dados", QMessageBox.StandardButton.Abort)
        else:
            QMessageBox.information(self.ui, "SUCESSO", "Todas as ordens foram removidas!")

    def getUi(self):
        return self.ui
