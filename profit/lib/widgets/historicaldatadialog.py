#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase, Yichun Wei
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtGui import QDialog

from ib.ext.Contract import Contract
from profit.lib.widgets.ui_historicaldatadialog import Ui_HistoricalDataDialog


def nextTickerId():
    ## TODO:  make this a session value and increment it
    from random import randint
    return randint(1000, 2000)


class HistoricalDataDialog(QDialog, Ui_HistoricalDataDialog):
    dateTypeMap = {
        'Strings':1,
        'Integers':2,
    }

    rthMap = {
        True:1,
        False:0,
    }

    keywords = [
        'tickerId',
        'contract',
        'endDateTime',
        'durationStr',
        'barSizeSetting',
        'whatToShow',
        'useRTH',
        'formatDate',
    ]

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        assert hasattr(self, 'useRTH')

    def keywordParams(self):
        params = dict.fromkeys(self.keywords, '')
        for name in self.keywords:
            params[name] = getattr(self, name)
        return params

    @property
    def tickerId(self):
        tid = self.tickId.value()
        if tid == -1:
            tid = nextTickerId()
        return tid

    @property
    def contract(self):
        symbol = self.symbolName.text()
        security = self.secType.currentText()
        exchange = self.exchangeName.currentText()
        contract = Contract()
        contract.m_symbol = str(symbol)
        contract.m_secType = str(security)
        contract.m_exchange = str(exchange)
        return contract

    @property
    def endDateTime(self):
        ## wtf to do with tz ??
        value = self.startDate.dateTime().toPyDateTime().strftime("%Y%m%d %H:%M:%S EST")
        return value

    @property
    def durationStr(self):
        dvalue = self.durationValue.value()
        dtype = str(self.durationType.currentText())[0]
        return '%s %s' % (dvalue, dtype, )

    @property
    def barSizeSetting(self):
        return str(self.barSize.currentText())

    @property
    def whatToShow(self):
        return str(self.showType.currentText()).upper()

    @property
    def useRTH(self):
        return self.rthMap[bool(self.rthYes.isChecked())]

    @property
    def formatDate(self):
        return self.dateTypeMap[str(self.dateType.currentText())]
