import datetime
import sys

class Calculator:
    NO_TAXES_SELLING_PER_YEAR_LIMIT = 20000.00
    TAX_PAY_PERCENTAGE = 15.0
    TAX_SALES_PERCENTAGE = 0.0275
    TAX_EMOLUMENTS_PERCENTAGE = 0.004105
    TAX_IR_PERCENTAGE = 0.005

    def __init__(self, db):
        # This is a map of "Stock code" to "Average price" and "Amount"
        # The map will be updated as we iterate on each order
        self.stocks = {}
        self.db = db
        self.taxValues = self.db.getTaxValues()

    def getCustomTaxFee(self):
        return self.taxValues[0]

    def getCustomTaxRate(self):
        return self.taxValues[1]

    def getInitLossToDiscount(self):
        return self.taxValues[2]

    def getTransactionValueWithTaxes(self, amount, unitValue, isSell):
        # Taxes for sales and emoluments
        taxes = (self.TAX_SALES_PERCENTAGE + self.TAX_EMOLUMENTS_PERCENTAGE + self.TAX_IR_PERCENTAGE + self.getCustomTaxRate()) / 100
        totalWithoutTaxes = amount * unitValue
        taxRate = (1 - taxes) if isSell else (1 + taxes)
        taxFee = -self.getCustomTaxFee() if isSell else self.getCustomTaxFee()
        return (totalWithoutTaxes * taxRate) + taxFee

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

    def getFreeTaxesReport(self, ordersInAscendingDate, year):
        profits = self.getMonthlyReport(ordersInAscendingDate)
        # Return {month: [totalSales, realProfit]}
        ret = {}
        for key, value in profits.items():
            # Ignore months outside asked year
            date = datetime.datetime.strptime(key, '%b %y')
            if date.year != year:
                continue
            # Ignore months with value bigger than tax limit or that gave losses
            if value[0] > self.NO_TAXES_SELLING_PER_YEAR_LIMIT or value[1] < 0:
                continue
            ret[key] = value
        return ret

    def getPayingTaxesReport(self, ordersInAscendingDate, year):
        profits = self.getMonthlyReport(ordersInAscendingDate)
        # Return {month: [totalSales, lossToDiscount, discountedLoss, profit, taxToPay]}
        ret = {}
        lossToDiscount = self.getInitLossToDiscount()
        for key, value in profits.items():
            date = datetime.datetime.strptime(key, '%b %y')
            # If that gave a prejudice, let's accumulate it
            if (value[1] <= 0):
                lossToDiscount += -value[1]
                # This month is to be reported, show discounted loss until now
                if date.year == year:
                    ret[key] = [value[0], lossToDiscount, 0, value[1], 0]
                continue
            # Ignore months with value sold smaller than when we pay taxes
            if value[0] <= self.NO_TAXES_SELLING_PER_YEAR_LIMIT:
                continue
            # Remove from loss to discount as we had profits..
            oldLossToDiscount = lossToDiscount
            lossToDiscount -= value[1]
            if (lossToDiscount < 0):
                lossToDiscount = 0
            # Ignore months outside asked year
            if date.year != year:
                continue
            discountedLoss = oldLossToDiscount - lossToDiscount
            realProfitAfterDiscountedLosses = value[1] - discountedLoss
            if (realProfitAfterDiscountedLosses < 0):
                realProfitAfterDiscountedLosses = 0
            ret[key] = [value[0], lossToDiscount, discountedLoss, value[1], realProfitAfterDiscountedLosses*(self.TAX_PAY_PERCENTAGE/100)]
        return ret
