import os
import sys

from process_order import ProcessOrder
from util import gui

from PySide2.QtWidgets import QDialogButtonBox, QMessageBox, QFileDialog, QGridLayout, QPushButton, QVBoxLayout
from PySide2.QtCore import SIGNAL, QObject

class RegisterOrder:
    def __init__(self, db):
        self.ui = gui.load_ui('./windows/register_order.ui')
        self.db = db

        fileLayout = self.ui.findChild(QVBoxLayout, 'file_layout')
        self.fileDialog = QFileDialog()
        self.fileDialog.setNameFilter('Extrato CEI Negociação de Ativos (*.xls)')
        fileLayout.addWidget(self.fileDialog)

        self.processFilesButton = self.ui.findChild(QPushButton, 'process_files_button')
        self.processFilesButton.clicked.connect(self.processFiles)

        self.wipeOrdersButton = self.ui.findChild(QPushButton, 'wipe_orders_button')
        self.wipeOrdersButton.clicked.connect(self.wipeOrders)

        self.updateWindow()

    def confirmRequest(self, title):
        response = QMessageBox.question(self.ui, title, "Tem certeza que deseja continuar?\nIsso irá apagar todas as suas operações registradas.",
                                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Abort)
        if (response != QMessageBox.StandardButton.Ok):
            return False
        return True

    def updateWindow(self):
        None

    def processFiles(self):
        files = self.fileDialog.selectedFiles()
        if (len(files) == 0 or not os.path.isfile(files[0])):
            QMessageBox.critical(self.ui, "ERRO", 'Por favor selecione um arquivo', QMessageBox.StandardButton.Abort)
            return

        if (not self.confirmRequest("Importar operações")):
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

        if (not self.db.updateOrders(orders)):
            QMessageBox.critical(self.ui, "ERRO", "Houve um erro ao atualizar o banco de dados", QMessageBox.StandardButton.Abort)
            self.db.updateOrders([])
        else:
            QMessageBox.information(self.ui, "SUCESSO", "Planilha importada com sucesso!\nInseridas " + str(self.db.getNumOrders()) + " ordens!")

    def wipeOrders(self):
        if (not self.confirmRequest("Apagar operações")):
            return
        if (not self.db.updateOrders([])):
            QMessageBox.critical(self.ui, "ERRO", "Houve um erro ao limpar o banco de dados", QMessageBox.StandardButton.Abort)
        else:
            QMessageBox.information(self.ui, "SUCESSO", "Todas as ordens foram removidas!")

    def getUi(self):
        return self.ui
