#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import QWidget

from profit.lib.core import Signals
from profit.lib.widgets.ui_searchbar import Ui_SearchBar


class SearchBar(QWidget, Ui_SearchBar):
    """ Widget with search line edit and clear button.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor of this widget
        """
        QWidget.__init__(self, parent)
        self.setupUi(self)

    @pyqtSignature('')
    def on_clearButton_clicked(self):
        """ signal handler called when clear button is pressed

        @return None
        """
        self.searchEdit.clear()
        self.searchEdit.emit(Signals.editingFinished)

    def on_searchEdit_textChanged(self, text):
        """ signal handler called when line edit text changed

        @param text current value of line edit as QString instance
        @return None
        """
