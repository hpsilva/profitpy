#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from functools import partial
from time import ctime

from PyQt4.QtCore import QAbstractTableModel, QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QBrush, QColor, QColorDialog, QIcon, QFrame, QMenu
from PyQt4.QtGui import QPixmap, QSortFilterProxyModel

from ib.opt.message import registry

from profit.lib.core import Settings, Signals, Slots, nogc
from profit.lib.gui import colorIcon
from profit.widgets.ui_messagedisplay import Ui_MessageDisplay


def messageTypeNames():
    """ Builds set of message type names.

    @return set of all message type names as strings
    """
    return set([t.typeName for t in registry.values()])


def messageRow(index, mtuple, model):
    """ Extracts the row number from an index and its message.

    @param index QModelIndex instance
    @param mtuple two-tuple of (message time, message object)
    @return row number as integer
    """
    return model.messages.index(mtuple)


def messageTime(index, (mtime, message), model):
    """ Extracts the message time from an index and its message.

    @param index QModelIndex instance
    @param mtime message time as float
    @param message message instance
    @return mtime formatted with ctime call
    """
    return ctime(mtime)


def messageName(index, (mtime, message), model):
    """ Extracts the type name from an index and its message.

    @param index QModelIndex instance
    @param mtime message time as float
    @param message message instance
    @return type name of message as string
    """
    return message.typeName


def messageText(index, (mtime, message), model):
    """ Extracts the items from an index and its message.

    @param index QModelIndex instance
    @param mtime message time as float
    @param message message instance
    @return message string formatted with message key=value pairs
    """
    return str.join(', ', ['%s=%s' % (k, v) for k, v in message.items()])


class MessagesTableModel(QAbstractTableModel):
    """ Data model for session messages.

    """
    columnTitles = ['Index', 'Time', 'Type', 'Fields']
    dataExtractors = {0:messageRow, 1:messageTime,
                      2:messageName, 3:messageText}

    def __init__(self, session, brushes, parent=None):
        """ Constructor.

        @param session Session instance
        @param brushes mapping of typenames to foreground brushes
        @param parent ancestor object
        """
        QAbstractTableModel.__init__(self, parent)
        self.brushes = brushes
        self.setSession(session)

    def setSession(self, session):
        """ Saves reference to session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.messagesview = self.messages = session.messages
        self.messagetypes = []
        session.registerAll(self.on_sessionMessage) # , Signals.layoutChanged)

    def setPaused(self, paused):
        """ Pauses or resumes signals emitted from this model.

        @param paused if True, disconnects from session, otherwise reconnects
        @return None
        """
        session = self.session
        regcall = session.deregisterAll if paused else session.registerAll
        regcall(self.on_sessionMessage)

    def on_sessionMessage(self, message):
        """ Signal handler for incoming messages.

        @param message message instance
        @return None
        """
        if message.typeName in self.messagetypes:
            self.enableTypesFilter(self.messagetypes)
        self.emit(Signals.layoutChanged)

    def data(self, index, role):
        """ Framework hook to determine data stored at index for given role.

        @param index QModelIndex instance
        @param role Qt.DisplayRole flags
        @return QVariant instance
        """
        if not index.isValid():
            return QVariant()
        message = self.messagesview[index.row()]
        if role == Qt.ForegroundRole:
            return QVariant(self.brushes[message[1].typeName])
        if role != Qt.DisplayRole:
            return QVariant()
        try:
            val = self.dataExtractors[index.column()](index, message, self)
            val = QVariant(val)
        except (KeyError, ):
            val = QVariant()
        return val

    def headerData(self, section, orientation, role):
        """ Framework hook to determine header data.

        @param section integer specifying header (e.g., column number)
        @param orientation Qt.Orientation value
        @param role Qt.DisplayRole flags
        @return QVariant instance
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.columnTitles[section])
        return QVariant()

    def rowCount(self, parent=None):
        """ Framework hook to determine data model row count.

        @param parent ignored
        @return number of rows (message count)
        """
        return len(self.messagesview)

    def columnCount(self, parent=None):
        """ Framework hook to determine data model column count.

        @param parent ignored
        @return number of columns (see columnTitles)
        """
        return len(self.columnTitles)

    def enableTypesFilter(self, types):
        self.messagetypes = list(types)
        self.messagesview = list(
            m for m in self.messages if m[1].typeName in types)
        self.reset()

    def disableTypesFilter(self):
        self.messagetypes = []
        self.messagesview = self.messages
        self.reset()


class MessagesFilterModel(QSortFilterProxyModel):
    """ Filters messages from display.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QSortFilterProxyModel.__init__(self, parent)

    def __filterAcceptsRow(self, row, index):
        """ Framework hook to control row visibility

        @param row row number as integer
        @param index QModelIndex instance (ignored)
        @return True if message should be displayed, False if not
        """
        if self.stoprow and row > self.stoprow:
            return False
        msg = self.messages[row][1]
        return msg.typeName in self.types


class MessageDisplay(QFrame, Ui_MessageDisplay):
    """ Table view of session messages with nifty controls.

    """
    pauseButtonIcons = {
        True:':/images/icons/player_play.png',
        False:':/images/icons/player_pause.png',
    }

    pauseButtonText = {
        True:'Resume',
        False:'Pause',
    }

    def __init__(self, session, parent=None):
        """ Constructor.

        @param session instance of Session
        @param parent ancestor of this widget
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.messageTable.verticalHeader().hide()
        self.settings = settings = Settings()
        settings.beginGroup(settings.keys.messages)
        self.setupModel(session)
        self.setupColorButton()
        self.setupDisplayButton()
        session.registerAll(self.messageTable, Slots.scrollToBottom)

    def setupColorButton(self):
        """ Configures the color highlight button.

        @return None
        """
        self.colorPop = pop = QMenu(self.colorButton)
        self.colorButton.setMenu(pop)
        self.colorTypes = messageTypeNames()
        self.colorActions = actions = \
            [pop.addAction(v) for v in sorted(self.colorTypes)]
        getv = self.settings.value
        defc = QColor(0,0,0)
        for action in actions:
            actc = getv('%s/color' % action.text(), defc)
            action.color = color = QColor(actc)
            action.setIcon(colorIcon(color))
            self.connect(action, Signals.triggered, self.on_colorChange)
        self.brushMap.update(
            dict([(str(a.text()), QBrush(a.color)) for a in actions])
            )

    def setupDisplayButton(self):
        """ Configures the display types button.

        @return None
        """
        self.displayPop = pop = QMenu(self.displayButton)
        self.displayButton.setMenu(pop)
        self.displayActions = actions = []
        allAction = pop.addAction('All')
        actions.append(allAction)
        pop.addSeparator()
        actions.extend([pop.addAction(v) for v in sorted(self.displayTypes)])
        for action in actions:
            action.setCheckable(True)
            self.connect(action, Signals.triggered, self.on_displayChange)
        allAction.setChecked(True)

    def setupModel(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.messages = session.messages
        self.brushMap = brushes = {}
        self.model = MessagesTableModel(session, brushes, self)
        self.displayTypes = types = messageTypeNames()
        self.proxyModel = None
        self.messageTable.setModel(self.model)

    def on_colorChange(self):
        """ Signal handler for color change actions.

        @return None
        """
        action = self.sender()
        color = QColorDialog.getColor(action.color, self)
        if color.isValid():
            action.color = color
            action.setIcon(colorIcon(color))
            self.brushMap[str(action.text())] = QBrush(color)
            self.model.reset()
            self.settings.setValue('%s/color' % action.text(), color)

    def on_displayChange(self):
        """ Signal handler for display types actions.

        @return None
        """
        action = self.sender()
        index = self.displayActions.index(action)
        allAction = self.displayActions[0]
        allChecked = allAction.isChecked()
        actionChecked = action.isChecked()
        if allChecked and action is not allAction:
            allAction.setChecked(False)
            self.displayTypes.clear()
            self.displayTypes.add(str(action.text()))
            self.model.enableTypesFilter(self.displayTypes)
            ## add proxy and one regex
            if 0:
                self.proxyModel = MessagesFilterModel(self)
                self.proxyModel.setSourceModel(self.model)
                self.proxyModel.setFilterKeyColumn(2) # type
                self.proxyModel.setFilterRegExp(action.text())
                self.messageTable.setModel(self.proxyModel)

        elif allChecked and action is allAction:
            self.displayTypes.clear()
            self.displayTypes.update(messageTypeNames())
            for act in self.displayActions[1:]:
                act.setChecked(False)
            self.model.disableTypesFilter()
            if 0:
                self.messageTable.setModel(self.model)
                if self.proxyModel is not None:
                    proxyModel = self.proxyModel
                    proxyModel.deleteLater()
                    self.proxyModel = None

        elif not allChecked and action is not allAction:
            text = str(action.text())
            if actionChecked:
                self.displayTypes.add(text)
                self.model.enableTypesFilter(self.displayTypes)
                if 0:
                    ## add text to proxy regex
                    self.proxyModel.setFilterRegExp(
                        self.proxyModel.filterRegExp().pattern() + '|' + text
                        )
            else:
                self.displayTypes.discard(text)
                self.model.enableTypesFilter(self.displayTypes)
                ## remove text from proxy regex
                if 0:
                    pattern = self.proxyModel.filterRegExp().pattern()
                    pattern.remove(text + '|')
                    print '## pattern:', pattern
                    self.proxyModel.setFilterRegExp(pattern)

        self.model.reset()

    @pyqtSignature('bool')
    def on_pauseButton_clicked(self, checked=False):
        """ Signal handler for pause button.

        @param checked toggled state of button
        @return None
        """
        self.model.setPaused(checked)
        session = self.session
        if checked:
            session.deregisterAll(self.messageTable, Slots.scrollToBottom)
        else:
            session.registerAll(self.messageTable, Slots.scrollToBottom)
        self.pauseButton.setText(self.pauseButtonText[checked])
        self.pauseButton.setIcon(QIcon(self.pauseButtonIcons[checked]))
