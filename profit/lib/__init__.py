#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

import logging
import sys
from cPickle import dumps, loads
from PyQt4.QtCore import (QCoreApplication, QPoint, QSettings, QSize,
                          QVariant, Qt, SIGNAL, SLOT)


## this module is generally the first to get imported by one of the
## gui apps, so we execute our ugly hack here.  this brings the
## resources into the client program, but it does not bring in
## PyQt4.QtGui.
if 'profit_rc' not in sys.modules:
    from profit.lib.widgets import profit_rc
    sys.modules['profit_rc'] = profit_rc
    del(profit_rc)
## now back to our regularly scheduled programming.


valueAlign = Qt.AlignRight | Qt.AlignVCenter
instance = QCoreApplication.instance
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')


def makeCheckNames(*names):
    def checkNames(obj):
        try:
            return obj.typeName in names
        except (AttributeError, ):
            return False
    return checkNames


def importName(name, reloaded=False):
    """ import and return a module by name in dotted form

    Copied from the Python lib docs.

    @param name module name as string
    @return module object
    """
    mod = __import__(name)
    if reloaded:
        reload(mod)
    for comp in name.split('.')[1:]:
        mod = getattr(mod, comp)
        if reloaded:
            reload(mod)
    return mod


def importItem(name, reloaded=False):
    """ import an item from a module by dotted name

    @param name module and attribute string, i.e., foo.bar.baz
    @return value of name from module
    """
    names = name.split('.')
    modname, itemname = names[0:-1], names[-1]
    mod = importName(str.join('.', modname), reloaded=reloaded)
    return getattr(mod, itemname)


class Signals:
    """ Contains SIGNAL attributes for easy and consistent reference.

    """
    clicked = SIGNAL('clicked()')
    createdAccountData = SIGNAL('createdAccountData')
    createdSeries = SIGNAL('createdSeries')
    createdTicker = SIGNAL('createdTicker')
    currentIndexChanged = SIGNAL('currentIndexChanged(int)')
    dataChanged = SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)')
    dialogFinished = SIGNAL('finished(int)')
    doubleValueChanged = SIGNAL('valueChanged(double)')
    editingFinished = SIGNAL('editingFinished()')
    enableCurve = SIGNAL('enableCurve')
    highlightSelections = SIGNAL('highlightSelections')
    finished = SIGNAL('finished()')
    headerDataChanged = SIGNAL('headerDataChanged(Qt::Orientation, int, int)')
    intValueChanged = SIGNAL('valueChanged(int)')
    itemActivated = SIGNAL('itemActivated (const QModelIndex &)')
    itemChanged = SIGNAL('itemChanged(QStandardItem *)')
    itemDoubleClicked = SIGNAL('itemDoubleClicked(QTreeWidgetItem *, int)')
    itemSelected = SIGNAL('itemSelected (const QModelIndex &)')
    lastWindowClosed = SIGNAL('lastWindowClosed()')
    layoutChanged = SIGNAL('layoutChanged()')
    loadFinished = SIGNAL('loadFinished(bool)')
    modelClicked = SIGNAL('activated (const QModelIndex &)')
    modelDoubleClicked = SIGNAL('doubleClicked (const QModelIndex &)')
    modelReset = SIGNAL('modelReset()')
    modified = SIGNAL('modified')
    openUrl = SIGNAL('openUrl(PyQt_PyObject)')
    rowsInserted = SIGNAL('rowsInserted(const QModelIndex &, int, int)')
    selectionChanged = SIGNAL('selectionChanged(const QItemSelection &, const QItemSelection &)')
    settingsChanged = SIGNAL('settingsChanged')
    splitterMoved = SIGNAL('splitterMoved(int, int)')
    standardItemChanged = SIGNAL('itemChanged(QStandardItem *)')
    terminated = SIGNAL('terminated()')
    textChanged = SIGNAL('textChanged(const QString &)')
    textChangedEditor = SIGNAL('textChanged()')
    tickerClicked = SIGNAL('tickerClicked')
    timeout = SIGNAL('timeout()')
    toggled = SIGNAL('toggled(bool)')
    trayIconActivated = SIGNAL('activated(QSystemTrayIcon::ActivationReason)')
    triggered = SIGNAL('triggered()')
    triggeredBool = SIGNAL('triggered(bool)')
    zoomed = SIGNAL('zoomed(const QwtDoubleRect &)')

    class contract:
        added = SIGNAL('contractAdded(int, PyQt_PyObject)')

    class histdata:
        start = SIGNAL('historicalDataStart')
        finish = SIGNAL('historicalDataFinish')

    class session:
        created = SIGNAL('sessionCreated(PyQt_PyObject)')
        reference = SIGNAL('sessionReference(PyQt_PyObject)')
        request = SIGNAL('sessionRequest')
        status = SIGNAL('sessionStatus')

    class strategy:
        loaded = SIGNAL('strategyLoaded(PyQt_PyObject)')
        loadFailed = SIGNAL('strategyLoadFaield(PyQt_PyObject)')
        fileUpdated = SIGNAL('strategyFileUpdated(PyQt_PyObject)')
        requestActivate = SIGNAL('strategyActivated(PyQt_PyObject, bool)')

    class tws:
        connected = SIGNAL('connectedTWS')
        disconnected = SIGNAL('disconnectedTWS')


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
        app = 'Profit Workbench'
        appearance = 'Appearance'
        connection = 'Connection'
        designer = 'StrategyDesigner'
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
        tickerurls = 'TickerUrls'
        urls = 'Urls'
        strategy = 'Strategy'
        winstate = 'State'
        ctabstate = 'CentralTabState'
        externalbrowser = 'ExternalBrowser'
        tickerdisplay = 'TickerDisplay'

    def __init__(self):
        """ Initializer.

        """
        QSettings.__init__(self, self.keys.org, self.keys.app)

    def setValue(self, key, value):
        """ Sets value of setting

        @param key setting key as string
        @param value anything supported by QVariant constructor
        @return None
        """
        QSettings.setValue(self, key, QVariant(value))

    def setValueDump(self, key, value):
        self.setValue(key, dumps(value))

    def valueLoad(self, key, default=None):
        v = self.value(key, default=default)
        if v:
            try:
                v = loads(str(v.toString()))
            except (Exception, ), exc:
                logging.debug('Exception valueLoad: %s, %r', exc, exc)
                v = default
        return v

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


def generateUserRoles():
    i = Qt.UserRole
    while True:
        yield i
        i += 1
nextUserRole = generateUserRoles().next


class DataRoles:
    tickerId = nextUserRole()
    tickerSymbol = nextUserRole()
    histDataReqId = nextUserRole()
    url = nextUserRole()
    urlTitle = nextUserRole()
    strategyName = nextUserRole()
    displayImportName = nextUserRole()
    tickerField = nextUserRole()


class SessionHandler(object):
    """ Mixin to provide Qt objects and widgets basic session handling.

    Clients of this class should include it as a base class, then call
    'requestSession' to retrieve an existing session and connect to
    the 'sessionCreated' signal.
    """
    sessionRef = None

    def sessionGetter(self):
        return self.sessionRef

    def sessionSetter(self, value):
        session = self.sessionRef
        if session:
            for child in self.children() + [self, ]:
                session.deregisterMeta(child)
                try:
                    child.unsetSession()
                except (AttributeError, ):
                    pass
        logging.debug('Session set for %s to %s' % (self.objectName(), value))
        self.sessionRef = value

    session = property(sessionGetter, sessionSetter)

    def existingSession(self, session):
        """ Connects this object to an existing session instance.

        This method is provided so classes that mix in SessionHandler
        do not have to call the base class implementation of
        setSession.

        @param session Session instance
        @return None
        """
        self.disconnect(
            instance(), Signals.session.reference, self.existingSession)
        if session is not self.session:
            self.setSession(session)

    def requestSession(self):
        """ Sends request for existing session.

        @return None
        """
        app = instance()
        connect = self.connect
        connect(app, Signals.session.created, self.setSession)
        connect(app, Signals.session.reference, self.existingSession)
        connect(self, Signals.session.request, app, Signals.session.request)
        self.emit(Signals.session.request)

    def setSession(self, session):
        """ Default implementation sets session as attribute.

        Subclasses should reimplement this method.
        """
        self.session = session


class SettingsHandler(object):
    """ Provies late and automatic access to 'settings' attribute.

    """
    settingsRef = None

    def settingsGetter(self):
         settingsRef = self.settingsRef
         if not settingsRef:
             self.settingsRef = settingsRef = Settings()
         return settingsRef

    def settingsSetter(self, value):
        self.settingsRef = value

    settings = property(settingsGetter, settingsSetter)


class BasicHandler(SessionHandler, SettingsHandler):
    pass
