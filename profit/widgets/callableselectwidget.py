#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtGui import QFrame

from profit.widgets.ui_callableselect import Ui_CallableSelectWidget


class CallableSelectWidget(QFrame, Ui_CallableSelectWidget):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
