from PySide2 import QtCore
from PySide2.QtWidgets import QTableWidgetItem

class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        return (self.data(QtCore.Qt.UserRole) < other.data(QtCore.Qt.UserRole))

def formatFloatToMoney(value):
    return ('%.2f' % value).replace('.', ',')
