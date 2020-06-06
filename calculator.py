import datetime
import sys

class Calculator:
    def __init__(self):
        # This is a map of "Stock code" to "Average price" and "Amount"
        # The map will be updated as we iterate on each order
        self.stocks = {}

    def getTransactionValueWithTaxes(self, amount, unitValue, isSell):
        # Taxes for sales and emoluments
        taxes = (0.0275 + 0.004105) / 100
        totalWithoutTaxes = amount * unitValue
        taxRate = (1 - taxes) if isSell else (1 + taxes)
        return totalWithoutTaxes * taxRate

    def updateAverageValue(self, oldAmount, oldValue, addingAmount, addingValue):
        # Buying a stock requires updating amount and value (weighted-average)
        return (oldAmount * oldValue + self.getTransactionValueWithTaxes(addingAmount, addingValue, False)) / (oldAmount + addingAmount)

    def updateStockAverageValueAndAmount(self, order):
        if (not order[3] in self.stocks):
            self.stocks[order[3]] = [0, 0]
        amount = self.stocks[order[3]][0]
        value = self.stocks[order[3]][1]
        if (order[2] == 'V'):
            # Selling a stock won't change its average value
            amount -= order[5]
        else:
            value = self.updateAverageValue(amount, value, order[5], order[6])
            amount += order[5]
        self.stocks[order[3]][0] = amount
        self.stocks[order[3]][1] = value

    def getYearExtract(self, ordersUpToYear):
        for order in ordersUpToYear:
            self.updateStockAverageValueAndAmount(order)
        return self.stocks

    def getProfitsAndLosses(self, ordersInAscendingDate):
        ret = []
        for order in ordersInAscendingDate:
            self.updateStockAverageValueAndAmount(order)
            # After updating stock average value and amount, check if
            # that's a selling operation and calculate profit/loss
            if (order[2] != 'V'):
                continue
            totalSellingValue = self.getTransactionValueWithTaxes(order[5], order[6], True)
            averageBuyingValue = self.stocks[order[3]][1]
            totalBuyingValue = averageBuyingValue * order[5]
            profit = totalSellingValue - totalBuyingValue
            ret.append([order[1], order[3], averageBuyingValue, order[5], order[6], profit])
        return ret

    def getMonthlyReport(self, ordersInAscendingDate):
        ret = {}
        for order in ordersInAscendingDate:
            self.updateStockAverageValueAndAmount(order)
            # After updating stock average value and amount, check if
            # that's a selling operation and calculate profit/loss
            if (order[2] != 'V'):
                continue
            # Calculate total selling value, profits, etc.
            totalSellingValue = self.getTransactionValueWithTaxes(order[5], order[6], True)
            totalSellingValueWithoutTaxes = order[5] * order[6]
            averageBuyingValue = self.stocks[order[3]][1]
            totalBuyingValue = averageBuyingValue * order[5]
            profit = totalSellingValue - totalBuyingValue
            # Update corresponding month with variables calculated
            date = datetime.datetime.strptime(order[1], '%Y-%m-%d')
            dateString = date.strftime('%b %y')
            if dateString not in ret:
                ret[dateString] = [0, 0]
            ret[dateString][0] += totalSellingValueWithoutTaxes
            ret[dateString][1] += profit
        return ret
