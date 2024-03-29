import sys

from PySide2.QtSql import QSqlDatabase, QSqlQuery

class Database:
    def __init__(self):
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('database.db')
        self.opened = self.db.open()

    def isValid(self):
        # By default SQLite will create a new file, so opening should never fail...
        if (not self.opened):
            return False
        # That said, also check if database contains orders table
        # TODO: Check if database structure (tables) are as expected
        query = QSqlQuery()
        query.exec_('SELECT 1 FROM orders')
        return not query.lastError().isValid()

    def updateTaxValues(self, taxFee, taxRate, lossToDiscount):
        wipeQuery = QSqlQuery()
        wipeQuery.exec_('DELETE FROM config')

        insertData = "INSERT INTO config ('tax_fee', 'tax_rate', 'loss_to_discount') VALUES "
        insertData += "('" + str(taxFee) + "', '" + str(taxRate) + "', '" + str(lossToDiscount) + "');"
        insertQuery = QSqlQuery()
        insertQuery.exec_(insertData)

    def getTaxValues(self):
        query = QSqlQuery()
        query.exec_('SELECT * FROM config LIMIT 1')
        if (query.lastError().isValid()):
            return [0, 0, 0]
        
        result = query.result()
        while (result.fetchNext()):
            return [query.result().data(0), query.result().data(1), query.result().data(2)]
        return [0, 0, 0]

    def getNumOrders(self):
        query = QSqlQuery()
        query.exec_('SELECT COUNT(*) FROM orders')
        if (query.lastError().isValid()):
            return -1
        query.result().fetch(0)
        return query.result().data(0)
    
    def getYearsWithOrders(self):
        years = []
        query = QSqlQuery()
        query.exec_('SELECT DISTINCT strftime("%Y", date) FROM orders')
        if (query.lastError().isValid()):
            return []
        result = query.result()
        while (result.fetchNext()):
            years.append(result.data(0))
        return years

    def getOrdersFromResult(self, query):
        if (query.lastError().isValid()):
            return []
        data = []
        result = query.result()
        while (result.fetchNext()):
            data.append([result.data(0), result.data(1), result.data(2), result.data(3), result.data(4), result.data(5), result.data(6)])
        return data

    def getOrdersInAscendingDate(self):
        query = QSqlQuery()
        query.exec_('SELECT * FROM orders ORDER BY date(date) ASC')
        return self.getOrdersFromResult(query)

    def getOrdersInAscendingDateUpToYear(self, year):
        query = QSqlQuery()
        query.exec_('SELECT * FROM orders WHERE strftime("%Y", date) <= "' + str(year) + '" ORDER BY date(date) ASC')
        return self.getOrdersFromResult(query)

    def eraseOrdersWithinDateRange(self, firstDate, secondDate):
        query = QSqlQuery()
        firstDateStr = firstDate.strftime('%Y-%m-%d')
        secondDateStr = secondDate.strftime('%Y-%m-%d')
        query.exec_('DELETE FROM orders WHERE date >= "' + firstDateStr + '" AND date <= "' + secondDateStr + '"')
        return query.numRowsAffected()

    def eraseOrdersById(self, idsToErase):
        query = QSqlQuery()
        whereExpr = ''
        for idToErase in idsToErase:
            whereExpr += ' OR ' if len(whereExpr) > 0 else ''
            whereExpr += 'id = ' + str(idToErase)
        query.exec_('DELETE FROM orders WHERE ' + whereExpr)
        return query.numRowsAffected()

    def deleteOrders(self):
        wipeQuery = QSqlQuery()
        wipeQuery.exec_('DELETE FROM orders')
        return not wipeQuery.lastError().isValid()

    def addOrders(self, orders):
        insertData = "INSERT INTO orders ('date', 'type', 'code', 'name', 'amount', 'value') VALUES "
        for order in orders:
            insertData += "("
            insertData += "'" + order[0].strftime('%Y-%m-%d') + "',"
            insertData += "'" + order[1] + "',"
            insertData += "'" + order[2] + "',"
            insertData += "'" + order[3] + "',"
            insertData += "'" + str(order[4]) + "',"
            insertData += "'" + str(order[5]) + "'"
            insertData += "),"

        # Remove last comma
        insertData = insertData[:-1]
        insertData += ';'
        insertQuery = QSqlQuery()
        insertQuery.exec_(insertData)

        return not insertQuery.lastError().isValid()
