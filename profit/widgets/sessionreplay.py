#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from itertools import tee

from PyQt4.QtCore import QTimer
from PyQt4.QtGui import QDialog

from profit.lib.core import Signals
from profit.widgets.ui_sessionreplay import Ui_SessionReplayWidget


class SessionReplay(QDialog, Ui_SessionReplayWidget):
    def __init__(self, interval=50, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.interval = interval
        self.session = self.filename = self.types = self.loader = self.importer = None
        self.timer = QTimer()

    def on_restartButton_clicked(self):
        if self.importer:
            self.loader = self.importer()

    def on_timer_timeout(self):
        if self.session and not self.loader:
            self.importSession(self.session, self.filename, self.types)
        if self.loader:
            setr = self.importProgress.setValue
            msgid = -1
            try:
                msgid = self.loader.next()
            except (StopIteration, ):
                pass
            else:
                setr(msgid)
                if msgid == self.last:
                    msg = 'Imported %s messages from file "%s".'
                    msg %= (self.count, self.filename)
                    print '##', msg

    def setImport(self, session, filename, types):
        self.session = session
        self.filename = filename
        self.types = types

    def importSession(self, session, filename, types):
        importer = session.importMessages(str(filename), types)
        loader = importer()
        try:
            self.count = loader.next()
            self.last = self.count - 1
            if not self.count:
                raise StopIteration()
        except (StopIteration, ):
            self.loader = self.count = self.last = None
            print 'Warning messages not imported from "%s"' % filename
        else:
            self.importProgress.setMaximum(self.last)
            self.importer = importer
            self.loader = loader

    def exec_(self):
        c = self.connect
        c(self.timerSlider, Signals.intValueChanged, self.timer.setInterval)
        c(self.timerSpin, Signals.intValueChanged, self.timer.setInterval)
        c(self.timer, Signals.timeout, self.on_timer_timeout)
        self.timer.start(self.interval)
        return QDialog.exec_(self)
