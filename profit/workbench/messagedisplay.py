#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from time import ctime

from PyQt4.QtCore import pyqtSignature
from PyQt4.QtGui import (QBrush, QColor, QColorDialog, QIcon, QFrame,
                         QMenu, QTableWidgetItem, )

from ib.opt.message import messageTypeNames

from profit.lib import defaults
from profit.lib.core import SessionHandler, SettingsHandler, Signals, Slots
from profit.lib.gui import colorIcon
from profit.lib.models.messages import MessagesTableModel
from profit.workbench.widgets.ui_messagedisplay import Ui_MessageDisplay


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
        """ Constructor.

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
        self.setupColorButton()
        self.setupDisplayButton()
        self.splitter.restoreState(defaults.rightMainSplitterState())
        self.requestSession()

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

    def setSession(self, session):
        """ Configures this instance for a session.

        @param session Session instance
        @return None
        """
        self.session = session
        self.messages = session.messages
        self.model = model = MessagesTableModel(session, self.brushMap, self)
        self.proxyModel = None
        self.messageTable.setModel(model)
        #session.registerAll(self.messageTable, Slots.scrollToBottom)

    def on_messageTable_clicked(self, index):
        row = index.row()
        mtime, msg = index.model().message(row)
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
            #self.model.enableTypesFilter(self.displayTypes)
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
                #self.model.enableTypesFilter(self.displayTypes)
                if 0:
                    ## add text to proxy regex
                    self.proxyModel.setFilterRegExp(
                        self.proxyModel.filterRegExp().pattern() + '|' + text
                        )
            else:
                self.displayTypes.discard(text)
                #self.model.enableTypesFilter(self.displayTypes)
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
        #self.model.setPaused(checked)
        session = self.session
        ## if checked:
        ##     session.deregisterAll(self.messageTable, Slots.scrollToBottom)
        ## else:
        ##     session.registerAll(self.messageTable, Slots.scrollToBottom)
        self.pauseButton.setText(self.pauseButtonText[checked])
        self.pauseButton.setIcon(QIcon(self.pauseButtonIcons[checked]))

