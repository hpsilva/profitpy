#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase, Yichun Wei
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>


## WTF?  this module is broken.


from cPickle import PicklingError, dump
from PyQt4.QtCore import QThread, QTimer, SLOT
from profit.lib.core import Signals


class CollectorThread(QThread):
    def __init__(self, mutex, parent=None):
        QThread.__init__(self, parent)
        self.mutex = mutex
        self.subTimer = self.startTime = self.stopTime = self.autoConnect = None

    def updateConfig(self, (startTime, stopTime, autoConnect)):
        print '#col thread has new config:', startTime.secsTo(stopTime)
        self.startTime = startTime
        self.stopTime = stopTime
        self.autoConnect = autoConnect

    def serializeSession(self):
        pass

    def run(self):
        while True:
            #if self.subTimer and self.subTimer.isActive():
            #    self.sleep(1)
            #    continue
            self.mutex.lock() # wait for it...
            print 'unlocked collector thread'
            self.emit(Signals.threadRunning)
            secs = self.startTime.secsTo(self.stopTime)
            print '###', secs
            self.serializeSession()
            #print 'a', timer.setInterval(secs)
            #print 'b', timer.setSingleShot(True)
            #print 'c', timer.start()
            while True:
                self.sleep(1)
        return
        status = False
        session = self.parent()
        try:
            handle = open(self.filename, 'wb')
        except (IOError, ):
            pass
        else:
            last = len(session.messages)
            messages = session.messages[0:last]
            types = self.types
            if types:
                def messageFilter((mtime, message)):
                    return message.typeName in types
                messages = filter(messageFilter, messages)
                last = len(messages)
            try:
                dump(messages, handle, protocol=-1)
                self.writeCount = last
                status = True
            except (PicklingError, ):
                pass
            finally:
                handle.close()
        self.status = status

if 0:
    class CollectorSignals:
        starting = SIGNAL('collectorStarting')
        started = SIGNAL('collectorStarted')
        stopped = SIGNAL('collectorStopped')
        saved = SIGNAL('collectorSaved')
        done = SIGNAL('collectorFinished')
        wait = SIGNAL('collectorWaiting(PyQt_PyObject)')
        wrong = SIGNAL('collectorWrongConfig')

class ___CollectorDisplayThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        print '##', parent

    def run(self):
        parent = self.parent()
        startTime = parent.startTime.time
        stopTime = parent.stopTime.time
        currentTime = QTime.currentTime

        while True:
            self.sleep(1)
            current = currentTime()
            start = startTime()
            stop = stopTime()
            diff = start.secsTo(stop)
            if (diff <= 0):
                self.emit(CollectorSignals.wrong)
            elif  (current < start):
                self.emit(CollectorSignals.wait, current.secsTo(start))
            else:
                if current > start:
                    self.emit(CollectorSignals.wait)
                    self.sleep(3)
                    self.emit(CollectorSignals.started)
