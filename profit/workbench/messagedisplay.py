#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from time import ctime

from PyQt4.QtCore import Qt, QVariant, pyqtSignature
from PyQt4.QtGui import (QBrush, QColor, QColorDialog, QIcon, QFrame,
                         QMenu, QTableWidgetItem, QSortFilterProxyModel)


from ib.opt.message import messageTypeNames

from profit.lib import defaults
from profit.lib.core import SessionHandler, SettingsHandler, Signals, Slots
from profit.lib.gui import colorIcon
from profit.lib.models.messages import MessagesTableModel
from profit.workbench.widgets.ui_messagedisplay import Ui_MessageDisplay


class TypesFilter(QSortFilterProxyModel):
    def __init__(self, session, acceptTypes=[], parent=None):
        QSortFilterProxyModel.__init__(self, parent)
        self.messagesBare = session.messagesBare
        self.acceptTypes = acceptTypes

    def filterAcceptsRow(self, row, parent):
        msg = self.messagesBare[row]
        return msg.typeName in self.acceptTypes


class MessageDisplay(QFrame, Ui_MessageDisplay, SessionHandler,
                     SettingsHandler):
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

    def __init__(self, parent=None):
        """ Initializer.

        @param parent ancestor of this widget
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.brushMap = {}
        self.displayTypes = messageTypeNames()

        for widget in (self.messageTable, self.messageDetail):
            widget.verticalHeader().hide()
            widget.verticalHeader().hide()
        ## widget is the messageDetail widget
        horizHeader = widget.horizontalHeader()
        horizHeader.setResizeMode(horizHeader.ResizeToContents)

        settings = self.settings
        settings.beginGroup(settings.keys.messages)
        self.setupColors()
        self.splitter.restoreState(defaults.rightMainSplitterState())
        self.requestSession()

    @pyqtSignature('int')
    def on_allCheck_stateChanged(self, state):
        try:
            filterModel = self.filterModel
        except (AttributeError, ):
            # not initialized yet
            return
        if state:
            filterModel.acceptTypes = list(self.colorTypes)
        else:
            types = self.messageTypeDisplay.selectedTypes()
            filterModel.acceptTypes = types
        filterModel.reset()

    @pyqtSignature('')
    def on_checkNoneButton_clicked(self):
        self.filterModel.acceptTypes = []
        self.filterModel.reset()

    @pyqtSignature('')
    def on_checkAllButton_clicked(self):
        ## should swap out model
        self.filterModel.acceptTypes = list(self.colorTypes)
        self.filterModel.reset()

    def on_typesList_itemChanged(self, item):
        try:
            filterModel = self.filterModel
        except (AttributeError, ):
            # not initialized yet
            return
        text = str(item.text())
        types = filterModel.acceptTypes
        checked = item.checkState()
        if checked and text not in types:
            types.append(text)
            filterModel.reset()
        elif checked and (text in types):
            types.remove(text)
            filterModel.reset()

    def on_typesList_itemDoubleClicked(self, item):
        color = QColor(item.data(Qt.DecorationRole))
        color = QColorDialog.getColor(color, self)
        if color.isValid():
            item.setData(Qt.DecorationRole, QVariant(color))
            item.setIcon(colorIcon(color))
            self.brushMap[str(item.text())] = QBrush(color)
            self.model.reset()
            self.settings.setValue('%s/color' % item.text(), color)

    def setupColors(self):
        """ Configures the color highlight button.

        @return None
        """
        self.colorTypes = messageTypeNames()
        getValue = self.settings.value
        defaultColor = QColor(0,0,0)
        for name in self.colorTypes:
            self.brushMap[name] = getValue('%s/color' % name, defaultColor)
        items = self.messageTypeDisplay.listItems()
        for item in items:
            color = QColor(self.brushMap[str(item.text())])
            item.setData(Qt.DecorationRole, QVariant(color))
            item.setIcon(colorIcon(color))

    def setSession(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.messages = session.messages
        self.model = model = MessagesTableModel(session, self.brushMap, self)
        self.filterModel = TypesFilter(session, self.colorTypes, self)
        self.filterModel.setSourceModel(model)
        self.proxyModel = None
        self.messageTable.setModel(self.filterModel)
        if 0:
            session.registerAll(self.messageTable, Slots.scrollToBottom)

    def on_messageTable_clicked(self, index):
        row = index.row()
        mtime, msg = self.model.message(row) ## WRONG
        tbl = self.messageDetail
        tbl.clearContents()
        items = [('index', row),
                 ('message type', type(msg).__name__),
                 ('received time', ctime(mtime)), ]
        items += list(sorted(msg.items()))
        tbl.setRowCount(len(items))
        for idx, (name, value) in enumerate(items):
            tbl.setItem(idx, 0, QTableWidgetItem(name))
            tbl.setItem(idx, 1, QTableWidgetItem(str(value)))

    def on_pauseButton_clicked(self, checked=False):
        """ Signal handler for pause button.

        @param checked toggled state of button
        @return None
        """
        #self.model.setPaused(checked)
        session = self.session
        ## if checked:
        ##     session.deregisterAll(self.messageTable, Slots.scrollToBottom)
        ## else:
        ##     session.registerAll(self.messageTable, Slots.scrollToBottom)
        self.pauseButton.setText(self.pauseButtonText[checked])
        self.pauseButton.setIcon(QIcon(self.pauseButtonIcons[checked]))
