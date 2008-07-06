#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtGui import QDialog
from profit.widgets.ui_collectordialog import Ui_CollectorDialog


class CollectorDialog(QDialog, Ui_CollectorDialog):
    """ Dialog for selecting message types for import or export.

    """
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

    def selectedTypes(self):
        """ Delegate lookup of selected message types to the display widget.

        """
        return self.messageTypeDisplay.selectedTypes()

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    dlg = CollectorDialog()
    if dlg.exec_() == dlg.Accepted:
        print dlg.selectedTypes()

