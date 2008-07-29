#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from re import split as rxsplit

from PyQt4.QtCore import Qt, QVariant, pyqtSignature
from PyQt4.QtGui import QFrame, QStandardItem

from ib.ext.TickType import TickType
from profit.lib import DataRoles
from profit.lib.widgets.ui_tickfieldselect import Ui_TickFieldSelect


def itemTickField(item):
    """ Returns the tick field from the item's data

    """
    return item.data(DataRoles.tickerField).toInt()[0]


def setItemTickField(item, field):
    """ Sets the tick field role on the item.

    """
    item.setData(DataRoles.tickerField, QVariant(field))


def fieldIds():
    """ Generates sequence of tick field identifiers.  Refer to the
    TickType class for concrete list.

    """
    for field in fieldSpecs():
        yield field['value']


def fieldSpecs():
    """ Yields one description dict for every TickType field.

    """
    values = [getattr(TickType, k) for k in dir(TickType)]
    for value in [v for v in values if isinstance(v, int)]:
        name = TickType.getField(value)
        title = tickFieldTitle(name)
        yield dict(sort=value, value=value, name=name, title=title)


def tickFieldTitle(name):
    """ Make title from name, aka UnCapCase.

    """
    words = rxsplit('([A-Z0-9][a-z]+)', name)
    ## my rx fu isn't great enough.  special case for when the split
    ## does not work, e.g., bidEFP.
    if len(words) == 1:
        words = rxsplit('([a-z]+)', name)
    ## title case each word in the word list if the word isn't already
    ## all upper case.
    words = [(word.title() if not word.upper()==word else word)
         for word in words if word]
    return str.join(' ', words)


def extraFieldSpecs():
    yield dict(sort=-4, value=-4, name='id', title='Id')
    yield dict(sort=-3, value=-3, name='symbol', title='Symbol')
    yield dict(sort=-2, value=-2, name='position', title='Position')
    yield dict(sort=-1, value=-1, name='value', title='Value')


class TickFieldSelect(QFrame, Ui_TickFieldSelect):
    """ TickFieldSelect -> widget for selecting various tick fields.

    """
    def __init__(self, parent=None):
        """ Initializer.

        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.setupFieldsList()

    def setupFieldsList(self):
        """ Clears and fills the fields list.

        """
        fieldsList = self.fieldsList
        fieldsList.clear()
        allFields = sorted(list(extraFieldSpecs()) + list(fieldSpecs()),
                           key=lambda d:d['sort'])
        self.allTickFields = allFields

        for rowId, fieldDesc in enumerate(allFields):
            fieldsList.addItem(fieldDesc['title'])
            item = fieldsList.item(rowId)
            setItemTickField(item, fieldDesc['value'])
            item.setCheckState(Qt.Unchecked)

    def setCheckedFields(self, fields):
        """

        """
        for item in self.listItems():
            field = itemTickField(item)
            if field in fields:
                item.setCheckState(Qt.Checked)

    def listItems(self):
        """ Returns the QStandardItems in the fields list.

        """
        listWidget = self.fieldsList
        return [listWidget.item(r) for r in range(listWidget.count())]

    def checkedItems(self):
        """ Returns list of seleected fields names (as strings)

        """
        return [i for i in self.listItems() if i.checkState()==Qt.Checked]


    @pyqtSignature('')
    def on_checkNoneButton_clicked(self):
        """ Unchecks every item in the fields list.

        """
        for item in self.listItems():
            item.setCheckState(Qt.Unchecked)

    @pyqtSignature('')
    def on_checkAllButton_clicked(self):
        """ Checks every item in the fields list.

        """
        for item in self.listItems():
            item.setCheckState(Qt.Checked)



