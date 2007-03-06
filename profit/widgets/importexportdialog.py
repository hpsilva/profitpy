#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import Qt, pyqtSignature
from PyQt4.QtGui import QApplication, QDialog

from ib.opt import message

from profit.widgets.ui_importexportdialog import Ui_ImportExportDialog


def setListItemCheckStateMethod(state):
    @pyqtSignature('')
    def method(self):
        for item in self.listItems():
            item.setCheckState(state)
    return method


class ImportExportDialog(QDialog, Ui_ImportExportDialog):
    def __init__(self, typeText, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setTypeText(typeText)
        self.populateTypeList()

    def populateTypeList(self):
        listWidget = self.typesList
        listWidget.clear()
        self.allTypeNames = [c.typeName for c in message.registry.values()]
        for row, typeName in enumerate(sorted(self.allTypeNames)):
            listWidget.addItem(typeName)
            item = listWidget.item(row)
            item.setCheckState(Qt.Checked)

    def listItems(self):
        listWidget = self.typesList
        return [listWidget.item(r) for r in range(listWidget.count())]

    def setTypeText(self, text):
        self.setWindowTitle(str(self.windowTitle()) % text)
        for widget in [self.promptText, self.allCheck, self.typesListText]:
            widget.setText(str(widget.text()) % text)

    def selectedTypes(self):
        if self.allCheck.checkState()==Qt.Checked:
            return self.allTypeNames
        return [str(i.text()) for i in self.listItems()
                if i.checkState()==Qt.Checked]

    on_checkAllButton_clicked = setListItemCheckStateMethod(Qt.Checked)
    on_checkNoneButton_clicked = setListItemCheckStateMethod(Qt.Unchecked)


if __name__ == '__main__':
    app = QApplication([])
    dlg = ImportExportDialog('Import')
    if dlg.exec_() == dlg.Accepted:
        print dlg.selectedTypes()

