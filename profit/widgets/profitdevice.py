#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

# TODO: complete strategy display; integrate strategy designer

from functools import partial
try:
    from os import P_NOWAIT, getpgrp, killpg, popen, spawnvp
    from signal import SIGQUIT
except (ImportError, ):
    pass
from os.path import abspath, basename
from subprocess import Popen
from sys import argv, executable

from PyQt4.QtCore import QUrl, QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QAction, QApplication, QColor, QMainWindow
from PyQt4.QtGui import QFileDialog, QMessageBox, QProgressDialog, QMenu
from PyQt4.QtGui import QSystemTrayIcon, QToolBar
from PyQt4.QtGui import QIcon, QDesktopServices

from profit.lib.core import Signals, Settings
from profit.lib.gui import ValueColorItem, warningBox
from profit.session import Session
from profit.widgets import profit_rc
from profit.widgets.dock import Dock
from profit.widgets.output import OutputWidget
from profit.widgets.sessionreplay import SessionReplay
from profit.widgets.sessiontree import SessionTree
from profit.widgets.shell import PythonShell
from profit.widgets.ui_profitdevice import Ui_ProfitDeviceWindow


applicationName = QApplication.applicationName
instance = QApplication.instance
processEvents = QApplication.processEvents


class ProfitDeviceWindow(QMainWindow, Ui_ProfitDeviceWindow):
    documentationUrl = \
        'http://code.google.com/p/profitpy/w/list?q=label:Documentation'
    iconName = ':images/icons/blockdevice.png'
    maxRecentSessions = 5

    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.setupDockWidgets()
        self.setupMenus()
        self.setupMainIcon()
        self.setupRecentSessions()
        self.setupSysTray()
        self.setupColors()
        self.readSettings()
        self.setWindowTitle('%s (0.2 alpha)' % applicationName())
        connect = self.connect
        connect(self, Signals.settingsChanged, self.setupColors)
        connect(self, Signals.settingsChanged, self.setupSysTray)
        connect(self, Signals.sessionRequest, self.sessionRequested)
        connect(instance(), Signals.lastWindowClosed, self.writeSettings)
        self.createSession()
        if len(argv) > 1:
            self.on_actionOpenSession_triggered(filename=argv[1])

    def checkClose(self):
        check = True
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        confirm = settings.value('confirmCloseWhenModified', QVariant(1))
        confirm = confirm.toInt()[0]
        if self.session.isModified and confirm:
            buttons = QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel
            text = 'This session has been modified'
            if self.session.isConnected:
                text += ' and is connected and receiving messages.'
            else:
                text += '.'
            text += '\nDo you want to save your changes?'
            msg = QMessageBox.question(
                self, applicationName(), text, buttons, QMessageBox.Save)
            if msg == QMessageBox.Discard:
                pass
            elif msg == QMessageBox.Cancel:
                check = False
            elif msg == QMessageBox.Save:
                self.actionSaveSession.trigger()
        return check

    def closeEvent(self, event):
        if self.checkClose():
            try:
                self.trayIcon.deleteLater()
            except (AttributeError, ):
                pass
            event.accept()
        else:
            event.ignore()

    def closeProcessGroup(self):
        self.writeSettings()
        try:
            killpg(getpgrp(), SIGQUIT)
        except (NameError, ):
            self.close()

    def createSession(self):
        ## lookup builder and pass instance here
        self.session = Session()
        self.emit(Signals.sessionCreated, self.session)
        self.connect(self.session, Signals.statusMessage,
                     self.statusBar().showMessage)

    @pyqtSignature('')
    def on_actionAboutProfitDevice_triggered(self):
        from profit.widgets.aboutdialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec_()

    @pyqtSignature('')
    def on_actionAboutQt_triggered(self):
        QMessageBox.aboutQt(self, 'About Qt')

    @pyqtSignature('bool')
    def on_actionClearRecentMenu_triggered(self, checked=False):
        for action in self.recentSessionsActions:
            action.setVisible(False)
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        settings.remove('recentSessions')

    @pyqtSignature('')
    def on_actionCloseSession_triggered(self):
        if self.checkClose():
            self.close()

    @pyqtSignature('')
    def on_actionDocumentation_triggered(self):
        QDesktopServices.openUrl(QUrl(self.documentationUrl))

    @pyqtSignature('')
    def on_actionExportSession_triggered(self, filename=None):
        from profit.widgets.importexportdialog import ImportExportDialog
        if not filename:
            filename = QFileDialog.getSaveFileName(
                self, 'Export Session To File')
        if filename:
            if self.session.exportInProgress:
                warningBox('Export in Progress',
                           'Session export already in progress.')
            else:
                dlg = ImportExportDialog('Export', self)
                if dlg.exec_() != dlg.Accepted:
                    return
                types = dlg.selectedTypes()
                if not types:
                    return
                self.session.exportMessages(filename, types)
                def lookup():
                    return not self.session.exportInProgress
                dlg = WaitMessageBox(lookup, self)
                dlg.setText('Export in Progress...')
                dlg.setWindowTitle('Profit Device Session Export')
                dlg.show()

    @pyqtSignature('')
    def on_actionImportSession_triggered(self, filename=None):
        from profit.widgets.importexportdialog import ImportExportDialog
        if not filename:
            filename = QFileDialog.getOpenFileName(
                self, 'Import Session From File')
        if filename:
            dlg = ImportExportDialog('Import', self)
            if dlg.exec_() != dlg.Accepted:
                return
            types = dlg.selectedTypes()
            if not types:
                return
            if not self.warningOpenTabs():
                return
            dlg = SessionReplay()
            dlg.setWindowTitle('Reading session file.')
            dlg.setWindowModality(Qt.WindowModal)
            dlg.setImport(self.session, filename, types)
            dlg.exec_()

            #self.statusBar().showMessage(msg, 5000)

    @pyqtSignature('bool')
    def on_actionNewSession_triggered(self, checked=False):
        try:
            if len(argv) > 1:
                argv.remove(argv[1])
            pid = spawnvp(P_NOWAIT, argv[0], argv)
        except (NameError, ):
            Popen('"%s" "%s"' % (executable, argv[0], ))

    @pyqtSignature('')
    def on_actionOpenSession_triggered(self, filename=None):
        if not filename:
            filename = QFileDialog.getOpenFileName(self, 'Open Session')
        if filename:
            if self.session.messages:
                args = argv[:]
                if len(args) > 1:
                    args[1] = filename
                else:
                    args.append(abspath(str(filename)))
                try:
                    pid = spawnvp(P_NOWAIT, args[0], args)
                except (NameError, ):
                    Popen('"%s" "%s" "%s"' % (executable, args[0], args[1]))
                return
            if not self.warningOpenTabs():
                return
            dlg = QProgressDialog(self)
            dlg.setLabelText('Reading session file.')
            dlg.setCancelButtonText('Abort')
            dlg.setWindowModality(Qt.WindowModal)
            dlg.setWindowTitle('Reading...')
            self.show()
            processEvents()
            dlg.show()
            processEvents()
            try:
                loadit = self.session.load(str(filename))
                count = loadit.next()
                last = count - 1
            except (StopIteration, ):
                msg = 'Warning session not loaded from "%s"' % filename
                dlg.close()
            else:
                dlg.setLabelText('Loading session messages.')
                dlg.setWindowTitle('Loading...')
                dlg.setMaximum(last)
                msgid = -1
                for msgid in loadit:
                    processEvents()
                    dlg.setValue(msgid)
                    if dlg.wasCanceled():
                        dlg.close()
                        break
                if msgid == last:
                    msg = 'Loaded all %s messages from file "%s".'
                    msg %= (count, filename)
                    self.setCurrentSession(filename)
                else:
                    msg = 'Load aborted; loaded %s messages of %s.'
                    msg %= (msgid+1, count)
            self.statusBar().showMessage(msg, 5000)

    @pyqtSignature('')
    def on_actionQuit_triggered(self):
        if self.checkClose():
            self.closeProcessGroup()

    @pyqtSignature('')
    def on_actionSaveSession_triggered(self):
        if self.session.filename is None:
            self.actionSaveSessionAs.trigger()
        else:
            if self.session.saveInProgress:
                warningBox('Save in Progress',
                           'Session save already in progress.')
            else:
                self.session.save()
                def lookup():
                    return not self.session.saveInProgress
                dlg = WaitMessageBox(lookup, self)
                dlg.setText('Save in Progress...')
                dlg.setWindowTitle('Profit Device Session Save')
                dlg.show()

    @pyqtSignature('')
    def on_actionSaveSessionAs_triggered(self):
        filename = QFileDialog.getSaveFileName(self, 'Save Session As')
        if filename:
            self.session.filename = str(filename)
            self.actionSaveSession.trigger()

    @pyqtSignature('')
    def on_actionSettings_triggered(self):
        from profit.widgets.settingsdialog import SettingsDialog
        dlg = SettingsDialog()
        dlg.readSettings(Settings())
        if dlg.exec_() == dlg.Accepted:
            self.emit(Signals.settingsChanged)

    @pyqtSignature('')
    def on_actionStrategyDesigner_triggered(self):
        from profit.widgets.strategydesigner import StrategyDesigner
        settings = Settings()
        settings.beginGroup(settings.keys.strategy)
        if settings.value('type', '').toString()=='file':
            filename = settings.value('location', '').toString()
        else:
            filename = None
        win = StrategyDesigner(filename=filename, parent=self)
        win.show()

    def on_trayIcon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.setVisible(not self.isVisible())
        elif reason == QSystemTrayIcon.MiddleClick:
            if self.session and self.session.isConnected:
                msg = 'Connected'
            else:
                msg = 'Not Connected'
            self.trayIcon.showMessage('Connection Status:', msg)

    @pyqtSignature('')
    def openRecentSession(self):
        filename = str(self.sender().data().toString())
        self.on_actionOpenSession_triggered(filename)

    def readSettings(self):
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        size = settings.value(settings.keys.size,
                              settings.defaultSize).toSize()
        pos = settings.value(settings.keys.position,
                             settings.defaultPosition).toPoint()
        maxed = settings.value(settings.keys.maximized, False).toBool()
        self.resize(size)
        self.move(pos)
        if maxed:
            self.showMaximized()
        state = settings.value(settings.keys.winstate, QVariant())
        self.restoreState(state.toByteArray())
        settings.endGroup()

    def setupColors(self):
        settings = Settings()
        settings.beginGroup(settings.keys.appearance)
        cls = ValueColorItem
        keys = ['increaseColor', 'neutralColor', 'decreaseColor']
        attrs = [k.replace('Color', '') for k in keys]
        values = [QColor(settings.value(key, getattr(cls, attr)))
                     for key, attr in zip(keys, attrs)]
        cls.setColors(*values)

    def setCurrentSession(self, filename):
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        files = settings.value('recentSessions').toStringList()
        files.removeAll(filename)
        files.prepend(filename)
        files = files[:self.maxRecentSessions]
        settings.setValue('recentSessions', files)
        self.updateRecentSessions()

    def setupDockWidgets(self):
        self.sessionDock = Dock('Session', self, SessionTree)
        area = Qt.BottomDockWidgetArea
        self.stdoutDock = Dock('Standard Output', self, OutputWidget, area)
        self.stderrDock = Dock('Standard Error', self, OutputWidget, area)
        makeShell = partial(PythonShell,
                            stdout=self.stdoutDock.widget(),
                            stderr=self.stderrDock.widget())
        self.shellDock = Dock('Python Shell', self, makeShell, area)
        self.tabifyDockWidget(self.shellDock, self.stdoutDock)
        self.tabifyDockWidget(self.stdoutDock, self.stderrDock)

    def setupMainIcon(self):
        icon = QIcon(self.iconName)
        self.setWindowIcon(icon)

    def setupMenus(self):
        self.menuView.addAction(self.sessionDock.toggleViewAction())
        self.menuView.addAction(self.shellDock.toggleViewAction())
        self.menuView.addAction(self.stdoutDock.toggleViewAction())
        self.menuView.addAction(self.stderrDock.toggleViewAction())
        self.menuView.addSeparator()
        self.menuView.addAction(self.actionStatusBar)
        self.menuView.addMenu(self.menuToolbars)
        for toolbar in self.findChildren(QToolBar):
            self.menuToolbars.addAction(toolbar.toggleViewAction())

    def setupRecentSessions(self):
        self.recentSessionsActions = actions = \
            [QAction(self) for i in range(self.maxRecentSessions)]
        for action in actions:
            action.setVisible(False)
            self.connect(action, Signals.triggered, self.openRecentSession)
        menu = self.menuRecentSessions
        menu.clear()
        for action in actions:
            menu.addAction(action)
        self.recentSeparator = menu.addSeparator()
        menu.addAction(self.actionClearRecentMenu)
        self.updateRecentSessions()

    def setupSysTray(self):
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        if settings.value('useSystemTrayIcon', QVariant(1)).toInt()[0]:
            icon = self.windowIcon()
            try:
                trayIcon = self.trayIcon
            except (AttributeError, ):
                self.trayIcon = trayIcon = QSystemTrayIcon(self)
                self.trayMenu = trayMenu = QMenu()
                trayIcon.setIcon(icon)
                trayMenu.addAction(icon, applicationName())
                trayMenu.addSeparator()
                for action in self.menuFile.actions():
                    trayMenu.addAction(action)
                    trayIcon.setContextMenu(trayMenu)
                self.connect(trayIcon, Signals.activated,
                             self.on_trayIcon_activated)
            trayIcon.show()
        else:
            try:
                trayIcon = self.trayIcon
            except (AttributeError, ):
                pass
            else:
                trayIcon.hide()

    def updateRecentSessions(self):
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        files = settings.value('recentSessions').toStringList()
        files = set([abspath(str(s)) for s in files])
        files = list(files)
        count = min(len(files), self.maxRecentSessions)
        for i in range(count):
            text = files[i]
            action = self.recentSessionsActions[i]
            action.setText(basename(str(text)))
            action.setData(QVariant(text))
            action.setVisible(True)
        for i in range(count, self.maxRecentSessions):
            action = self.recentSessionsActions[i]
            action.setVisible(False)
        self.recentSeparator.setVisible(count > 0)

    def warningOpenTabs(self):
        if self.centralTabs.count():
            button = QMessageBox.warning(self, 'Warning',
                         'Session loading is very slow with open tabs.\n'
                         'Close all tabs for fastest possible loading.',
                          QMessageBox.Ignore|QMessageBox.Abort)
            return button == QMessageBox.Ignore
        return True

    def writeSettings(self):
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        settings.setValue(settings.keys.size, self.size())
        settings.setValue(settings.keys.position, self.pos())
        settings.setValue(settings.keys.maximized, self.isMaximized())
        settings.setValue(settings.keys.winstate, self.saveState())
        settings.endGroup()

    def sessionRequested(self):
        self.emit(Signals.sessionReference, self.session)


class WaitMessageBox(QMessageBox):
    def __init__(self, callback, parent):
        QMessageBox.__init__(self, parent)
        self.callback = callback
        self.setIcon(self.Information)
        self.addButton(self.Abort)
        self.setWindowModality(Qt.NonModal)
        self.startTimer(500)

    def timerEvent(self, event):
        if self.callback():
            self.killTimer(event.timerId())
            self.accept()
