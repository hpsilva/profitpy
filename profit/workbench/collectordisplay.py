#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2
from PyQt4.QtCore import QTime, QTimer, pyqtSignature
from PyQt4.QtGui import QFrame

from profit.lib.core import SessionHandler, Signals
from profit.workbench.widgets.ui_collectordisplay import Ui_CollectorDisplay


class CollectorDisplay(QFrame, Ui_CollectorDisplay, SessionHandler):
    """ View of the collector settings and collector thread.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.requestSession()

    def setSession(self, session):
        """ setSession(s) -> overridden slot for receiving any new session objects

        We override the base SessionHandler implementation of this
        slot so that we can connect to the new session's signals.
        """
        SessionHandler.setSession(self, session)



if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    win = CollectorDisplay()
    win.show()
    app.exec_()
