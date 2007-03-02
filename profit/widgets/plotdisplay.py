#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtGui import QFrame

from profit.lib import Signals
from profit.widgets.ui_plotdisplay import Ui_PlotDisplay


class PlotDisplay(QFrame, Ui_PlotDisplay):
    """ Combines two plot widgets into a single display.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.connect(self.upperPlot.plotSplitter,
                     Signals.splitterMoved,
                     self.lowerPlot.plotSplitter.moveSplitter)

    def setSession(self, session, tickerId, *args):
        """ Associate a session with this instance.

        @param session Session instance
        @param tickerId id of ticker as integer
        @param *indexes unused
        @return None
        """
        self.upperPlot.setSession(session, tickerId, *args)
        self.lowerPlot.setSession(session, tickerId, *args)
