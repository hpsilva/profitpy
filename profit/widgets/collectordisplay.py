#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2
from PyQt4.QtCore import QTime, QTimer, pyqtSignature
from PyQt4.QtGui import QFrame

from profit.lib.core import SessionHandler, Signals
from profit.widgets.ui_collectordisplay import Ui_CollectorDisplay


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
        self.checkTimer = QTimer(self)
        self.connect(self.checkTimer, Signals.timeout, self.checkTimerTime)
        self.checkTimer.start(1000)
        
        if True: # should be if collector settings and collector start time...
            ct = QTime.currentTime()
            ct.setHMS(ct.hour(), ct.minute()+1, 0, 0)
            self.startTime.setTime(ct)
            ct.setHMS(ct.hour(), ct.minute()+1, 0, 0)
            self.stopTime.setTime(ct)

    def checkTimerTime(self):
        print '## checkTimerTime tickle', str(QTime.currentTime())

    def setSession(self, session):
        """ setSession(s) -> overridden slot for receiving any new session objects

        We override the base SessionHandler implementation of this
        slot so that we can connect to the new session's signals.
        """
        SessionHandler.setSession(self, session)
        cthread = session.collectorThread
        self.connect(cthread, Signals.threadRunning, self.on_threadRun)
        self.connect(cthread, Signals.threadFinished, self.on_threadFinished)
        self.connect(self, Signals.collectorActivate, session, Signals.collectorActivate)

    def setStatusText(self, text):
        self.statusLabel.setText(text)

    def on_threadRun(self):
        self.setStatusText('Started')

    def on_threadFinished(self):
        self.setStatusText('Stopped.')


    @pyqtSignature('')
    def on_activeButton_clicked(self):
        if not self.session:
            return
        config = (self.startTime.time(),
                  self.stopTime.time(),
                  self.autoConnect.isChecked(),
                  )
        print '## col display emitting activation+config'
        self.emit(Signals.collectorActivate, config)


    @pyqtSignature('QTime')
    def on_startTime_timeChanged(self, time):
        self.resetProgress()
        self.stopTime.setMinimumTime(time)

    @pyqtSignature('QTime')
    def on_stopTime_timeChanged(self, time):
        self.resetProgress()
        
    def resetProgress(self):
        start = self.startTime.time()
        stop = self.stopTime.time()
        diff = start.secsTo(stop)
        if diff > 0:
            bar = self.timeProgress
            bar.setMaximum(diff)
            bar.update()

    def on_threadStarting(self):
        self.setStatusText('Starting...')

    def on_threadSave(self):
        self.setStatusText('Saving...')

    def on_threadDone(self):
        self.setStatusText('Done.')

    def on_threadWait(self, howLong):
        self.setStatusText('Waiting %s' % (howLong, ))

    def on_threadWrongConfig(self):
        self.setStatusText('Invalid configuration.')


if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication

    app = QApplication([])
    win = CollectorDisplay()
    win.show()
    app.exec_()
