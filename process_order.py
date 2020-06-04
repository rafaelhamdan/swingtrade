import datetime
import sys
import xlrd

from enum import Enum
from xlrd.timemachine import xrange

class ErrorType(Enum):
    NO_ERROR = 0
    HEADER_NOT_FOUND = 1
    END_NOT_FOUND = 2
    INVALID_DATE = 3
    INVALID_TYPE = 4
    INVALID_MARKET_TYPE = 5
    INVALID_STOCK_AMOUNT = 6
    INVALID_STOCK_VALUE = 7

class ColumnsType():
    DATE = 1
    ORDER_TYPE = 3
    MARKET_TYPE = 4
    STOCK_CODE = 6
    STOCK_NAME = 7
    STOCK_AMOUNT = 8
    STOCK_VALUE = 9

class ProcessOrder:
    def __init__(self, file):
        self.file = file
        self.errorType = ErrorType.NO_ERROR
        self.errorField = None

    def getErrorType(self):
        return self.errorType

    def getErrorFieldMessage(self):
        if (not self.errorField):
            return ""
        return 'valor: "' + self.errorField[0] + '", linha: ' + str(self.errorField[1]) + ', coluna: ' + str(self.errorField[2])

    def getErrorMessage(self):
        if (self.errorType == ErrorType.NO_ERROR):
            assert(0)
            return "Nenhum erro"
        if (self.errorType == ErrorType.HEADER_NOT_FOUND):
            return "Não foi possível encontrar o cabeçalho da planilha da CEI"
        if (self.errorType == ErrorType.END_NOT_FOUND):
            return "Não foi possível encontrar o fim da lista de operações na planilha da CEI"
        if (self.errorType == ErrorType.INVALID_DATE):
            return "Campo de data inválido encontrado na planilha, esperado formado dd/mm/yy"
        if (self.errorType == ErrorType.INVALID_TYPE):
            return "Campo de tipo inválido encontrado na planilha, esperado C ou V"
        if (self.errorType == ErrorType.INVALID_MARKET_TYPE):
            return "Essa calculadora só suporta cálculo no mercado a vista"
        if (self.errorType == ErrorType.INVALID_STOCK_AMOUNT):
            return "Campo de quantidade de ações inválido"
        if (self.errorType == ErrorType.INVALID_STOCK_VALUE):
            return "Campo de preço da ação inválido"
        else:
            assert(0)
            return ""

    def processFile(self, f):
        orders = []

        xlsFile = xlrd.open_workbook(f)
        sheet = xlsFile.sheet_by_index(0)

        foundHeader = False
        foundEnd = False
        for rowNum in xrange(sheet.nrows):
            # TODO: Extract some methods here and fixed lines' contents
            rowValues = sheet.row_values(rowNum)
            if (rowValues == ['', 'Data Negócio', '', 'C/V', 'Mercado', 'Prazo', 'Código', 'Especificação do Ativo', 'Quantidade', 'Preço (R$)', 'Valor Total (R$)']):
                foundHeader = True
                continue
            elif (not foundHeader):
                continue
            elif (rowValues == ['', '', '', '', '', '', '', '', '', '', '']):
                foundEnd = True
                break

            # Extract values without spaces
            values = []
            for value in rowValues:
                if (isinstance(value, str)):
                    values.append(value.strip())
                else:
                    values.append(value)
            
            # Check market type
            if (values[ColumnsType.MARKET_TYPE] != 'Mercado a Vista'):
                self.errorType = ErrorType.INVALID_MARKET_TYPE
                self.errorField = [values[ColumnsType.MARKET_TYPE], rowNum + 1, ColumnsType.MARKET_TYPE + 1]
                return False

            # Extract date
            date = None
            try:
                date = datetime.datetime.strptime(values[ColumnsType.DATE], '%d/%m/%y')
            except:
                self.errorType = ErrorType.INVALID_DATE
                self.errorField = [values[ColumnsType.DATE], rowNum + 1, ColumnsType.DATE + 1]
                return False

            # Extract type
            stockType = values[ColumnsType.ORDER_TYPE]
            if (stockType != 'C' and stockType != 'V'):
                self.errorType = ErrorType.INVALID_TYPE
                self.errorField = [values[ColumnsType.ORDER_TYPE], rowNum + 1, ColumnsType.ORDER_TYPE + 1]
                return False

            # Extract code and name
            stockCode = values[ColumnsType.STOCK_CODE]
            stockName = values[ColumnsType.STOCK_NAME]

            # Extract stock value and amount
            stockAmount = values[ColumnsType.STOCK_AMOUNT]
            stockValue = values[ColumnsType.STOCK_VALUE]
            if (not isinstance(stockAmount, float)):
                self.errorType = ErrorType.INVALID_STOCK_AMOUNT
                self.errorField = [values[ColumnsType.STOCK_AMOUNT], rowNum + 1, ColumnsType.STOCK_AMOUNT + 1]
                return False
            if (not isinstance(stockValue, float)):
                self.errorType = ErrorType.INVALID_STOCK_VALUE
                self.errorField = [values[ColumnsType.STOCK_VALUE], rowNum + 1, ColumnsType.STOCK_VALUE + 1]
                return False

            orders.append([date, stockType, stockCode, stockName, stockAmount, stockValue])

        if (not foundHeader):
            self.errorType = ErrorType.HEADER_NOT_FOUND
            return False
        elif (not foundEnd):
            self.errorType = ErrorType.END_NOT_FOUND
            return False

        return orders
