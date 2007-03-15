#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import QPoint, QSettings, QSize, QVariant, Qt, SIGNAL, SLOT


class Signals:
    """ Contains SIGNAL attributes for easy and consistent reference.

    """
    activated = SIGNAL('activated(QSystemTrayIcon::ActivationReason)')
    clicked = SIGNAL('clicked()')
    connectedTWS = SIGNAL('connectedTWS')
    createdSeries = SIGNAL('createdSeries')
    createdTicker = SIGNAL('createdTicker')
    currentChanged = SIGNAL('currentChanged(int)')
    currentIndexChanged = SIGNAL('currentIndexChanged(int)')
    customContextMenuRequested = \
        SIGNAL('customContextMenuRequested(const QPoint &)')
    dataChanged = \
        SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)')
    disconnectedTWS = SIGNAL('disconnectedTWS')
    doubleValueChanged = SIGNAL('valueChanged(double)')
    finished = SIGNAL('finished()')
    intValueChanged = SIGNAL('valueChanged(int)')
    itemDoubleClicked = SIGNAL('itemDoubleClicked(QTreeWidgetItem *, int)')
    lastWindowClosed = SIGNAL('lastWindowClosed()')
    layoutChanged = SIGNAL('layoutChanged()')
    modelDoubleClicked = SIGNAL('doubleClicked (const QModelIndex &)')
    modelReset = SIGNAL('modelReset()')
    sessionCreated = SIGNAL('sessionCreated(PyQt_PyObject)')
    settingsChanged = SIGNAL('settingsChanged')
    splitterMoved = SIGNAL('splitterMoved(int, int)')
    standardItemChanged = SIGNAL('itemChanged(QStandardItem *)')
    statusMessage = SIGNAL('statusMessage')
    terminated = SIGNAL('terminated()')
    textChanged = SIGNAL('textChanged(const QString &)')
    tickerClicked = SIGNAL('tickerClicked')
    timeout = SIGNAL('timeout()')
    triggered = SIGNAL('triggered()')
    zoomed = SIGNAL('zoomed(const QwtDoubleRect &)')


class Slots:
    """ Contains SLOT attributes for easy and consistent reference.

    """
    scrollToBottom = SLOT('scrollToBottom()')
    expandItem = SLOT('expandItem(const QTreeWidgetItem *)')


class Settings(QSettings):
    """ Convenient replacement for QSettings.

    """
    class keys:
        """ Attributes are setting keys.

        """
        account = 'Account'
        app = 'Profit Device'
        appearance = 'Appearance'
        connection = 'Connection'
        designer = 'TickerDesigner'
        main = 'MainWindow'
        maximized = 'Maximized'
        messages = 'Messages'
        org = 'ProfitPy'
        plots = 'Plots'
        position = 'Position'
        session = 'Session'
        size = 'Size'
        splitstate  = 'SplitterState'
        strategy = 'Strategy'
        winstate = 'State'

    defaultSize = QSize(720, 560)
    defaultPosition = QPoint(200, 200)

    def __init__(self):
        """ Constructor.

        """
        QSettings.__init__(self, self.keys.org, self.keys.app)

    def setValue(self, key, value):
        """ Sets value of setting

        @param key setting key as string
        @param value anything supported by QVariant constructor
        @return None
        """
        QSettings.setValue(self, key, QVariant(value))

    def value(self, key, default=None):
        """ Returns value for key, or default if key doesn't exist.

        @param key setting key as string
        @param default value returned if key does not exist
        @return value of key or default
        """
        if default is None:
            default = QVariant()
        else:
            default = QVariant(default)
        return QSettings.value(self, key, default)




##
tickerIdRole = Qt.UserRole + 32


##
valueAlign = Qt.AlignRight | Qt.AlignVCenter


##
# Set for the nogc function/function decorator.
extra_references = set()


def nogc(obj):
    """ Prevents garbage collection. Usable as a decorator.

    @param obj any object
    @return obj
    """
    extra_references.add(obj)
    return obj


def disabledUpdates(name):
    """ Creates decorator to wrap table access with setUpdatesEnabled calls.

    @param name name of table attribute
    @return decorator function
    """
    def disableDeco(meth):
        """ Wraps method with table update disable-enable calls.

        @param meth method to wrap
        @return replacement method
        """
        def method(self, *a, **b):
            table = getattr(self, name)
            table.setUpdatesEnabled(False)
            try:
                meth(self, *a, **b)
            finally:
                table.setUpdatesEnabled(True)
        return method
    return disableDeco


def nameIn(*names):
    def check(obj):
        try:
            return obj.typeName in names
        except (AttributeError, ):
            return False
    return check

