#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import QObject, QCoreApplication

from profit.lib import logging
from profit.lib.core import Settings, Signals


class StrategyInstance(object):
    def __init__(self, type, location, source):
        self.type = type
        self.location = location
        self.source = source

    @classmethod
    def fromProgram(cls):
        ## execute an external command and use what it writes to
        ## stdout as a strategy (sequence of schema types).
        pass

    @classmethod
    def fromObject(cls):
        pass

    @classmethod
    def fromSource(cls):
        pass

    @classmethod
    def fromFile(cls):
        ## read a pickled strategy schema from a file
        return cls(m)




class Strategy(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.isActive = self.loadMessage = False
        self.threads = []
        self.tickers = []
        app = QCoreApplication.instance()
        self.connect(
            app, Signals.strategyFileUpdated, self.externalFileUpdated)

    def externalFileUpdated(self, filename):
        print '## strategy external file updated'

    def getActive(self):
        return self.isActive

    def setActive(self, enable):
        self.isActive = enable
        if not enable and self.isActive:
            self.deactivate()
        else:
            self.activate()
        self.emit(Signals.strategyActivated, enable)

    active = property(getActive, setActive)


    def load(self, params):
        origintype = params.get('type', '') or 'empty'
        try:
            call = getattr(self, 'from%s' % origintype.title())
            okay, message = call(**params)
            self.loadMessage = message
            signal = Signals.strategyLoaded if okay else \
                     Signals.strategyLoadFailed
            self.emit(signal, message)
            if okay and params.get('reload', False):
                self.emit(signal, 'Strategy reloaded')
        except (Exception, ), ex:
            self.emit(Signals.strategyLoadFailed, str(ex))

    def fromEmpty(self, **kwds):
        return (False, 'Cannot create strategy with empty origin type')

    def fromExternal(self, location='', **kwds):
        return (True, 'Load strategy from external command: %s' % location)

    def fromFile(self, location='', **kwds):
        return (True, 'Load strategy from file: %s' % location)

    def fromSource(self, location='', source='', **kwds):
        return (True, 'Load strategy from source: %s' % location)

    def fromObject(self, location='', **kwds):
        return (True, 'Load strategy from object: %s' % location)

    def unload(self):
        self.emit(Signals.strategyLoaded, False)

    def deactivate(self):
        pass

    def activate(self):
        pass


## questionable

    @classmethod
    def fromSchema(cls, schema):
        tickers = tickers(schema)
        singleshots = singleshots(schema)
        instance = cls()
        return instance

    def build(self, session):
        tickers = ifitler(self.schema.immediateChildren,
                          lambda x:hasattr(x, 'tickerId'))
        for ticker in tickers:
            ticker.build()
            self.tickers[ticker.tickerId] = ticker

    def execute(self, session):
        """

        It's important to note that runners are called only once:
        after this call is complete, the strategy is running.
        """
        runners = [c for c in self.schema.immediateChildren
                    if hasattr(c, 'exectype')]
        singles = ifilter(runners, lambda x:x.exectype=='singleshot')
        threads = ifilter(runners, lambda x:x.exectype=='periodic')
        handlers = ifilter(runners, lambda x:x.exectype=='messagehandler')

    threadinterval = 1000

    def start_threads(self, callables):
        """
        executes external program, callable object, or callable factory
        callables and factories can access strategy instance
        location inspected for argument names once only at thread start
        location executed on schedule
        """
        for child in self.chidren:
            thread = StrategyThread(child)
            thread.start()
            self.threads.append(thread)

    def execute_singles(self, callables):
        """
        executes external program or callable object once, in instance order
        executes callable factory and factory results once
        callable objects and factories inspected for argument names
        callables and factories can access strategy instance
        """
        for call in callables:
            execute_object_shell_or_factory(call)

    def associate_message_handlers(self):
        """
        callable object or callable factory (never external program)
        location arguments inspected only once when created
        callable object given message to process
        callable factory result object given message to process
        factories (but not callables) can access strategy instance
        """
        for call in self.callables:
            register_callable_for_its_message_types(call)

