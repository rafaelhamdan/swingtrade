from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile


def load_ui(file_name, where=None):
    loader = QUiLoader()

    ui_file = QFile(file_name)
    ui_file.open(QFile.ReadOnly)
    ui = loader.load(ui_file, where)
    ui_file.close()

    return ui
