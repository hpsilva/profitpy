#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import Qt, pyqtSignature
from PyQt4.QtGui import QApplication, QColor, QColorDialog, QDialog, QFont, QFontDialog

from profit.lib import Settings, colorIcon
from profit.widgets.syspathdialog import SysPathDialog
from profit.widgets.ui_settingsdialog import Ui_SettingsDialog


def getCheckState(o):
    return o.checkState()

def setCheckState(o, v):
    o.setCheckState(Qt.CheckState(v.toInt()[0]))

def getText(o):
    return o.text()

def setText(o, v):
    o.setText(v.toString())

def getValue(o):
    return o.value()

def setIntValue(o, v):
    o.setValue(v.toInt()[0])

def getFont(o):
    return QFont(o.font())

def setFont(o, v):
    v = QFont(v)
    try:
        name = v.toString().split(',')[0]
    except (IndexError, ):
        name = v.rawName()
    size = v.pointSize()
    bold = 'Bold' if v.bold() else ''
    o.setFont(v)
    o.setText('%s %s %s' % (name, size, bold))

def getColor(o):
    return o.color

def colorSetter(target):
    def setColor(o, v):
        o.color = color = QColor(v)
        o.setIcon(colorIcon(color))
    return setColor


schema = {}

schema[Settings.keys.main] = [
    ('confirmCloseWhenModified', getCheckState, setCheckState, Qt.Checked),
    ('confirmCloseWhenConnected', getCheckState, setCheckState, Qt.Checked),
    ('defaultHostName', getText, setText, 'localhost'),
    ('defaultPortNumber', getValue, setIntValue, 7496),
    ('defaultClientId', getValue, setIntValue, 0),
    ('useSystemTrayIcon', getCheckState, setCheckState, Qt.Checked),
    ('startupScript', getText, setText, ''),
]

schema[Settings.keys.strategy] = [
    ('accountSupervisor', getText, setText, ''),
    ('orderSupervisor', getText, setText, ''),
    ('tradeIndicator', getText, setText, ''),
]

schema[Settings.keys.appearance] = [
    ('shellFont', getFont, setFont, 'Monospace'),
    ('increaseColor', getColor, colorSetter('increaseColor'), QColor(Qt.darkGreen)),
    ('neutralColor', getColor, colorSetter('neutralColor'), QColor(Qt.blue)),
    ('decreaseColor', getColor, colorSetter('decreaseColor'), QColor(Qt.red)),
]


def sysPathSelectMethod(target):
    @pyqtSignature('')
    def selector(self):
        dlg = SysPathDialog(self)
        if dlg.exec_() == dlg.Accepted:
            widget = getattr(self, target)
            widget.setText(dlg.selectedEdit.text())
    return selector


def colorValueSelectMethod(target):
    @pyqtSignature('')
    def selector(self):
        widget = getattr(self, target)
        color = QColorDialog.getColor(widget.color, self)
        if color.isValid():
            widget.color = color
            widget.setIcon(colorIcon(color))
    return selector


class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

    def readSettings(self, settings):
        for key, lookups in schema.items():
            settings.beginGroup(key)
            for name, getr, setr, default in lookups:
                value = settings.value(name, default)
                obj = getattr(self, name)
                setr(obj, value)
            settings.endGroup()

    def writeSettings(self, settings):
        for key, lookups in schema.items():
            settings.beginGroup(key)
            for name, getr, setr, default in lookups:
                obj = getattr(self, name)
                value = getr(obj)
                settings.setValue(name, value)
            settings.endGroup()
        settings.sync()

    on_selectAccountSupervisor_clicked = sysPathSelectMethod('accountSupervisor')
    on_selectOrderSupervisor_clicked = sysPathSelectMethod('orderSupervisor')
    on_selectTradeIndicator_clicked = sysPathSelectMethod('tradeIndicator')
    on_increaseColor_clicked = colorValueSelectMethod('increaseColor')
    on_neutralColor_clicked = colorValueSelectMethod('neutralColor')
    on_decreaseColor_clicked = colorValueSelectMethod('decreaseColor')

    @pyqtSignature('')
    def on_selectShellFont_clicked(self):
        default = QFont(self.shellFont.font())
        font, okay = QFontDialog.getFont(default, self, 'Select Shell Font')
        if okay:
            setFont(self.shellFont, font)


if __name__ == '__main__':
    app = QApplication([])
    win = SettingsDialog()
    settings = Settings()
    win.readSettings(settings)
    if win.exec_() == win.Accepted:
        win.writeSettings(settings)
        for key, lookups in schema.items():
            print '[%s]' % key
            for name, getr, setr, default in lookups:
                obj = getattr(win, name)
                print '%s=%s' % (name, getr(obj))
            print
