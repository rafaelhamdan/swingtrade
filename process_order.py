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
    DAY_TRADE_FOUND = 8

class SupportedSpreadsheets(Enum):
    NONE = 0
    EXTRACT = 1
    BM_FBOVESPA = 2

class ColumnsTypeExtract():
    # FORMAT: ['Data Negócio', 'C/V', 'Mercado', 'Prazo', 'Código', 'Especificação do Ativo',
    #          'Quantidade', 'Preço (R$)', 'Valor Total (R$)']
    # Column 'prazo' is usually empty for Mercado a Vista, which is the only supported
    NONE = -1
    DATE = 0
    ORDER_TYPE = 1
    MARKET_TYPE = 2
    STOCK_CODE = 3
    STOCK_NAME = 4
    STOCK_AMOUNT = 5
    STOCK_VALUE = 6

class ColumnsTypeBovespa():
    # FORMAT: ['Cód', 'Data Negócio', 'Qtde.Compra', 'Qtd.Venda', 'Preço Médio Compra', 
    #          'Preço Médio Venda', 'Qtde. Liquida', 'Posição']
    NONE = -1
    STOCK_CODE = 0
    DATE = 1
    STOCK_AMOUNT_BUY = 2
    STOCK_AMOUNT_SELL = 3
    STOCK_VALUE_BUY = 4
    STOCK_VALUE_SELL = 5

def getFloatFromStr(strValue):
    return float(strValue.replace('.', '').replace(',', '.'))

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
        return 'valor: "' + str(self.errorField[0]) + '", linha: ' + str(self.errorField[1]) + ', coluna: ' + str(self.errorField[2])

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
        if (self.errorType == ErrorType.DAY_TRADE_FOUND):
            return "Essa calculadora não suporta day trade, que foi identificado na planilha"
        else:
            assert(0)
            return ""

    def processFile(self, f):
        orders = []

        self.xlsFile = xlrd.open_workbook(f)
        self.sheet = self.xlsFile.sheet_by_index(0)

        self.headerType = SupportedSpreadsheets.NONE
        foundEnd = False
        for rowNum in xrange(self.sheet.nrows):
            # TODO: Extract some methods here and fixed lines' contents
            rowValues = list(filter(None, self.sheet.row_values(rowNum)))
            order = False
            if (self.headerType != SupportedSpreadsheets.NONE):
                # If empty line, we reached the end
                if (len(rowValues) == 0):
                    foundEnd = True
                    break
                # Process this row and get an order from it
                order = self.processRow(rowNum, rowValues)
                if (not order):
                    return False
                orders.append(order)
            elif (rowValues == ['Data Negócio', 'C/V', 'Mercado', 'Prazo', 'Código', 'Especificação do Ativo',
                                'Quantidade', 'Preço (R$)', 'Valor Total (R$)']):
                self.headerType = SupportedSpreadsheets.EXTRACT
                continue
            elif (rowValues == ['Cód', 'Data Negócio', 'Qtde.Compra', 'Qtd.Venda', 'Preço Médio Compra', 
                                'Preço Médio Venda', 'Qtde. Liquida', 'Posição']):
                self.headerType = SupportedSpreadsheets.BM_FBOVESPA
                continue

        if (self.headerType == SupportedSpreadsheets.NONE):
            self.errorType = ErrorType.HEADER_NOT_FOUND
            return False
        elif (not foundEnd):
            self.errorType = ErrorType.END_NOT_FOUND
            return False

        return orders

    def processRow(self, rowNum, rowValues):
        # Extract values without spaces
        values = []
        for value in rowValues:
            if (isinstance(value, str)):
                values.append(value.strip())
            else:
                values.append(value)
        # Forward row to the respective processor
        if (self.headerType == SupportedSpreadsheets.EXTRACT):
            return self.processExtractRow(rowNum, values)
        elif (self.headerType == SupportedSpreadsheets.BM_FBOVESPA):
            return self.proccessBovespaRow(rowNum, values)
        return False

    def proccessBovespaRow(self, rowNum, values):
        # Extract date
        date = None
        try:
            date = datetime.datetime(*xlrd.xldate_as_tuple(values[ColumnsTypeBovespa.DATE], self.xlsFile.datemode))
        except:
            self.errorType = ErrorType.INVALID_DATE
            self.errorField = [values[ColumnsTypeBovespa.DATE], rowNum + 1, ColumnsTypeBovespa.DATE + 1]
            return False

        # Extrat code and type
        stockCode = values[ColumnsTypeBovespa.STOCK_CODE]

        # Extract amount of buy
        stockAmountBuy = getFloatFromStr(values[ColumnsTypeBovespa.STOCK_AMOUNT_BUY])
        stockValueBuy = getFloatFromStr(values[ColumnsTypeBovespa.STOCK_VALUE_BUY])
        stockAmountSell = getFloatFromStr(values[ColumnsTypeBovespa.STOCK_AMOUNT_SELL])
        stockValueSell = getFloatFromStr(values[ColumnsTypeBovespa.STOCK_VALUE_SELL])
        if (stockAmountBuy == 0 and stockAmountSell == 0):
            self.errorType = ErrorType.INVALID_STOCK_AMOUNT
            self.errorField = [values[ColumnsTypeBovespa.STOCK_AMOUNT_SELL], rowNum + 1, ColumnsTypeBovespa.STOCK_AMOUNT_SELL + 1]
            return False
        elif (stockValueBuy == 0 and stockValueSell == 0):
            self.errorType = ErrorType.INVALID_STOCK_VALUE
            self.errorField = [values[ColumnsTypeBovespa.STOCK_VALUE_SELL], rowNum + 1, ColumnsTypeBovespa.STOCK_VALUE_SELL + 1]
            return False

        # Check for day-trade (no support)
        if (stockAmountBuy > 0 and stockAmountSell > 0):
            self.errorType = ErrorType.DAY_TRADE_FOUND
            return False

        # Get stock type, stock amount, stock value
        stockType = 'V' if stockAmountSell > 0 else 'C'
        stockAmount = stockAmountSell if stockAmountSell > 0 else stockAmountBuy
        stockValue = stockValueSell if stockValueSell > 0 else stockValueBuy

        return [date, stockType, stockCode, '', stockAmount, stockValue]

    def processExtractRow(self, rowNum, values):
        # Check market type
        if (values[ColumnsTypeExtract.MARKET_TYPE] != 'Mercado a Vista' and values[ColumnsTypeExtract.MARKET_TYPE] != 'Merc. Fracionário'):
            self.errorType = ErrorType.INVALID_MARKET_TYPE
            self.errorField = [values[ColumnsTypeExtract.MARKET_TYPE], rowNum + 1, ColumnsTypeExtract.MARKET_TYPE + 1]
            return False

        # Extract date
        date = None
        try:
            date = datetime.datetime.strptime(values[ColumnsTypeExtract.DATE], '%d/%m/%y')
        except:
            self.errorType = ErrorType.INVALID_DATE
            self.errorField = [values[ColumnsTypeExtract.DATE], rowNum + 1, ColumnsTypeExtract.DATE + 1]
            return False

        # Extract type
        stockType = values[ColumnsTypeExtract.ORDER_TYPE]
        if (stockType != 'C' and stockType != 'V'):
            self.errorType = ErrorType.INVALID_TYPE
            self.errorField = [values[ColumnsTypeExtract.ORDER_TYPE], rowNum + 1, ColumnsTypeExtract.ORDER_TYPE + 1]
            return False

        # Extract code and name
        stockCode = values[ColumnsTypeExtract.STOCK_CODE]
        stockName = values[ColumnsTypeExtract.STOCK_NAME]

        # Extract stock value and amount
        stockAmount = values[ColumnsTypeExtract.STOCK_AMOUNT]
        stockValue = values[ColumnsTypeExtract.STOCK_VALUE]
        if (not isinstance(stockAmount, float)):
            self.errorType = ErrorType.INVALID_STOCK_AMOUNT
            self.errorField = [values[ColumnsTypeExtract.STOCK_AMOUNT], rowNum + 1, ColumnsTypeExtract.STOCK_AMOUNT + 1]
            return False
        elif (not isinstance(stockValue, float)):
            self.errorType = ErrorType.INVALID_STOCK_VALUE
            self.errorField = [values[ColumnsTypeExtract.STOCK_VALUE], rowNum + 1, ColumnsTypeExtract.STOCK_VALUE + 1]
            return False

        return [date, stockType, stockCode, stockName, stockAmount, stockValue]
