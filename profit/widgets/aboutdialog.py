#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from os.path import join, split
from PyQt4.QtGui import QDialog

import profit
from profit.widgets.ui_aboutdialog import Ui_AboutDialog


class AboutDialog(QDialog, Ui_AboutDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.licenseText.setText(
            open(join(split(profit.__file__)[0], 'LICENSE')).read())
