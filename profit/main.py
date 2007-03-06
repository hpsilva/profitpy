#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

# todo:
#    search bar for tickers, orders, account, etc.
#    account display plots
#    add prompts to close/quit if connected
#    add setting saves for message display colors
#    change "open" to "import"; provide actual "open" via
#        new window (if existing window has session messages)
#    modify orders display to use model/tree view
#    add check and read of startup .py script
#    write session collector script
#    create better defaults for plot colors
#    add account, orders, and strategy supervisors
#    fix zoom to (1000,1000) in plots
#    finalize about dialog box content
#    add help links to wiki

from functools import partial
from os import P_NOWAIT, getpgrp, killpg, popen, spawnvp
from signal import SIGQUIT
from sys import argv

from PyQt4.QtCore import QUrl, QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QApplication, QColor, QMainWindow
from PyQt4.QtGui import QFileDialog, QMessageBox, QProgressDialog, QMenu
from PyQt4.QtGui import QSystemTrayIcon
from PyQt4.QtGui import QIcon, QDesktopServices

from profit.lib import Signals, Settings, ValueColorItem, nogc
from profit.session import Session
from profit.widgets import profit_rc
from profit.widgets.accountsummary import AccountSummary
from profit.widgets.aboutdialog import AboutDialog
from profit.widgets.dock import Dock
from profit.widgets.output import OutputWidget
from profit.widgets.sessiontree import SessionTree
from profit.widgets.settingsdialog import SettingsDialog
from profit.widgets.shell import PythonShell
from profit.widgets.ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    iconName = ':images/icons/blockdevice.png'

    def __init__(self):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.setupLeftDock()
        self.setupBottomDock()
        self.setupMainIcon()
        self.setupSysTray()
        self.setupColors()
        self.readSettings()
        title = '%s (0.2 alpha)' % QApplication.applicationName()
        self.setWindowTitle(title)
        self.connect(self, Signals.settingsChanged, self.setupColors)
        self.connect(self, Signals.settingsChanged, self.setupSysTray)
        self.createSession()
        if len(argv) > 1:
            self.on_actionOpenSession_triggered(filename=argv[1])

    def setupLeftDock(self):
        self.accountDock = Dock('Account', self, AccountSummary)
        self.sessionDock = Dock('Session', self, SessionTree)
        self.tabifyDockWidget(self.sessionDock, self.accountDock)

    def setupBottomDock(self):
        area = Qt.BottomDockWidgetArea
        self.stdoutDock = Dock('Output', self, OutputWidget, area)
        self.stderrDock = Dock('Error', self, OutputWidget, area)
        makeShell = partial(PythonShell,
                            stdout=self.stdoutDock.widget(),
                            stderr=self.stderrDock.widget())
        self.shellDock = Dock('Shell', self, makeShell, area)
        self.tabifyDockWidget(self.shellDock, self.stdoutDock)
        self.tabifyDockWidget(self.stdoutDock, self.stderrDock)

    def setupMainIcon(self):
        icon = QIcon(self.iconName)
        self.setWindowIcon(icon)

    def setupSysTray(self):
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        if settings.value('useSystemTrayIcon', QVariant()).toInt()[0]:
            icon = self.windowIcon()
            try:
                trayIcon = self.trayIcon
            except (AttributeError, ):
                self.trayIcon = trayIcon = QSystemTrayIcon(self)
                self.trayMenu = trayMenu = QMenu()
                trayIcon.setIcon(icon)
                trayMenu.addAction(icon, QApplication.applicationName())
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

    def on_trayIcon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.setVisible(not self.isVisible())
        elif reason == QSystemTrayIcon.MiddleClick:
            if self.session and self.session.isConnected:
                msg = 'Connected'
            else:
                msg = 'Not Connected'
            self.trayIcon.showMessage('Connection Status:', msg)

    def createSession(self):
        ## lookup builder and pass instance here
        self.session = Session()
        self.emit(Signals.sessionCreated, self.session)

    @pyqtSignature('')
    def on_actionAboutProfitDevice_triggered(self):
        dlg = AboutDialog(self)
        dlg.exec_()

    @pyqtSignature('')
    def on_actionDocumentation_triggered(self):
        QDesktopServices.openUrl(
            QUrl('http://code.google.com/p/profitpy/w/list?q=label:Documentation'))

    @pyqtSignature('bool')
    def on_actionNewSession_triggered(self, checked=False):
        if len(argv) > 1:
            argv.remove(argv[1])
        pid = spawnvp(P_NOWAIT, argv[0], argv)

    @pyqtSignature('')
    def on_actionOpenSession_triggered(self, filename=None):
        if not filename:
            filename = QFileDialog.getOpenFileName(self)
        if filename:
            processEvents = QApplication.processEvents
            progress = QProgressDialog(self)
            progress.setLabelText('Reading session file.')
            progress.setCancelButtonText('Abort')
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle('Reading...')
            self.show()
            processEvents()
            progress.show()
            processEvents()
            try:
                loadit = self.session.load(str(filename))
                count = loadit.next()
                last = count - 1
            except (StopIteration, ):
                msg = 'Warning session not loaded from "%s"' % filename
                progress.close()
            else:
                progress.setLabelText('Loading session messages.')
                progress.setWindowTitle('Loading...')
                progress.setMaximum(last)
                msgid = -1
                for msgid in loadit:
                    processEvents()
                    progress.setValue(msgid)
                    if progress.wasCanceled():
                        progress.close()
                        break
                if msgid == last:
                    msg = 'Loaded all %s messages from file "%s".'
                    msg %= (count, filename)
                else:
                    msg = 'Load aborted; loaded %s messages of %s.'
                    msg %= (msgid+1, count)
            self.statusBar().showMessage(msg, 5000)

    @pyqtSignature('')
    def on_actionSettings_triggered(self):
        settings = Settings()
        dlg = SettingsDialog()
        dlg.readSettings(settings)
        if dlg.exec_() == dlg.Accepted:
            dlg.writeSettings(settings)
            self.emit(Signals.settingsChanged)

    @pyqtSignature('bool')
    def on_actionClearRecentMenu_triggered(self, checked=False):
        print '### clear recent menu', checked

    @pyqtSignature('')
    def on_actionSaveSession_triggered(self):
        if self.session.filename is None:
            self.actionSaveSessionAs.trigger()
        else:
            self.session.save()

    @pyqtSignature('')
    def on_actionSaveSessionAs_triggered(self):
        filename = QFileDialog.getSaveFileName(self)
        if filename:
            self.session.filename = str(filename)
            self.actionSaveSession.trigger()

    @pyqtSignature('')
    def on_actionCloseSession_triggered(self):
        if self.checkClose():
            self.close()

    @pyqtSignature('')
    def on_actionQuit_triggered(self):
        if self.checkClose():
            self.groupClose()

    def checkClose(self):
        check = True
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        confirm = settings.value('confirmCloseWhenModified', QVariant(1))
        confirm = confirm.toInt()[0]
        if self.session.isModified and confirm:
            buttons = QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel
            msg = QMessageBox.question(self, 'ProfitPy',
                                       'This session has been modified.\n'
                                       'Do you want to save your changes?',
                                       buttons,
                                       QMessageBox.Save)
            if msg == QMessageBox.Discard:
                pass
            elif msg == QMessageBox.Cancel:
                check = False
            elif msg == QMessageBox.Save:
                self.actionSaveSession.trigger()
        return check

    def groupClose(self):
        try:
            killpg(getpgrp(), SIGQUIT)
        except (AttributeError, ):
            self.close()

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()

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

    def writeSettings(self):
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        settings.setValue(settings.keys.size, self.size())
        settings.setValue(settings.keys.position, self.pos())
        settings.setValue(settings.keys.maximized, self.isMaximized())
        settings.setValue(settings.keys.winstate, self.saveState())
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
