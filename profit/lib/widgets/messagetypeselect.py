#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import Qt, pyqtSignature
from PyQt4.QtCore import QAbstractTableModel, QSize, QVariant, Qt
from PyQt4.QtGui import QApplication, QFrame, QStandardItemModel, QStandardItem

from profit.lib.core import SessionHandler, Signals, valueAlign
from profit.lib.gui import colorIcon, complementColor
from profit.lib.series import Series
from profit.lib.widgets.plot import PlotCurve, ControlTreeValueItem


from profit.lib.widgets.ui_messagetypeselect import Ui_MessageTypeSelect
from ib.opt import message


class MessageTypeSelect(QFrame, Ui_MessageTypeSelect):
    """ Widget for selecting various IB message types.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.populateTypeList()

    def listItems(self):
        listWidget = self.typesList
        return [listWidget.item(r) for r in range(listWidget.count())]

    def populateTypeList(self):
        listWidget = self.typesList
        listWidget.clear()
        self.allTypeNames = [c.typeName for c in message.registry.values()]
        for row, typeName in enumerate(sorted(self.allTypeNames)):
            listWidget.addItem(typeName)
            item = listWidget.item(row)
            item.setCheckState(Qt.Checked)

    def selectedTypes(self):
        if self.allCheck.checkState()==Qt.Checked:
            return self.allTypeNames
        return [str(i.text()) for i in self.listItems()
                if i.checkState()==Qt.Checked]

    @pyqtSignature('')
    def on_checkNoneButton_clicked(self):
        for item in self.listItems():
            item.setCheckState(Qt.Unchecked)

    @pyqtSignature('')
    def on_checkAllButton_clicked(self):
        for item in self.listItems():
            item.setCheckState(Qt.Checked)


if __name__ == '__main__':
    import sys
    app = QApplication([])
    win = MessageTypeSelect()
    win.show()
    sys.exit(app.exec_())
