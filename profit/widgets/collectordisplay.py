#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import QAbstractTableModel, QSize, QVariant, Qt
from PyQt4.QtGui import QFrame, QStandardItemModel, QStandardItem

from profit.lib.core import SessionHandler, Signals, valueAlign
from profit.lib.gui import colorIcon, complementColor
from profit.series import Series
from profit.widgets.plot import PlotCurve, ControlTreeValueItem
from profit.widgets.ui_collectordisplay import Ui_CollectorDisplay




class CollectorDisplay(QFrame, Ui_CollectorDisplay, SessionHandler):
    """ View of a collector.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
