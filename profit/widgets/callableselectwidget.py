#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from os.path import abspath, exists
from string import Template
from tempfile import NamedTemporaryFile

from PyQt4.QtCore import QProcess, QVariant, pyqtSignature
from PyQt4.QtGui import QFileDialog, QFrame, QInputDialog

from profit.lib.core import Settings, Signals
from profit.widgets.settingsdialog import SysPathDialog
from profit.widgets.ui_callableselect import Ui_CallableSelectWidget


class CallableSelectWidget(QFrame, Ui_CallableSelectWidget):
    revertSource = None
    saveSource = None

    unsetType, externalType, objectType, factoryType, sourceType = range(5)
    pythonTypes = (objectType, factoryType, sourceType)
    callTypeMap = {
        unsetType:'',
        externalType:'external',
        objectType:'object',
        factoryType:'factory',
        sourceType:'source',
    }

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.externalEditProcess = None
        setr = self.callableType.setItemData
        for key, value in self.callTypeMap.items():
            setr(key, QVariant(value))

    def basicSetup(self,  **kwds):
        self.callType = kwds.get('callType', self.unsetType)
        self.locationText = kwds.get('locationText', '')
        self.sourceEditorText = kwds.get('sourceEditorText', '')
        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)

    def getCallType(self):
        return self.callableType.currentIndex()

    def setCallType(self, value):
        wid = self.callableType
        try:
            index = value + 0
        except (TypeError, ):
            index = wid.findData(QVariant(value))
        wid.setCurrentIndex(index)

    callType = property(getCallType, setCallType)

    def getLocationText(self):
        return str(self.callableLocation.text())

    def setLocationText(self, text):
        self.callableLocation.setText(text)

    locationText = property(getLocationText, setLocationText)

    def getSourceEditorText(self):
        return str(self.callableSourceEditor.text())

    def setSourceEditorText(self, text):
        self.callableSourceEditor.setText(text)

    sourceEditorText = property(getSourceEditorText, setSourceEditorText)

    def warn(self, text):
        format = '<b>Warning:</b> %s' if text else '%s'
        self.locationWarning.setText('%s' % text)

    def on_textEdit_textChanged(self):
        try:
            self.callableCode()
        except (SyntaxError, ):
            msg = 'Warning:  invalid syntax.'
        else:
            msg = ''
        self.warn(msg)
        self.saveButton.setEnabled(True)
        self.revertButton.setEnabled(True)
        self.emit(Signals.modified)

    @pyqtSignature('int')
    def on_callableType_currentIndexChanged(self, index):
        if index == self.externalType:
            self.checkLocationExists()
        self.callableLocationSelect.setEnabled(index != self.sourceType)
        self.emit(Signals.modified)

    def checkLocationExists(self):
        if not exists(abspath(self.locationText)):
            msg = 'Warning: location does not exist.'
        else:
            msg = ''
        self.warn(msg)

    def callableCode(self):
        src = self.sourceEditorText
        return compile(src, 'strategyeditsrc', 'exec')

    def on_callableLocation_textChanged(self, text):
        self.warn('')
        if self.callType == self.sourceType:
            try:
                self.callableCode()
            except (SyntaxError, ):
                msg = 'Warning:  invalid syntax.'
            else:
                text = str(text)
                if text and text in code.co_names:
                    msg = ''
                else:
                    msg = 'Warning:  expression not found in source.'
            self.warn(msg)
        elif self.callType == self.externalType:
            self.checkLocationExists()
        self.emit(Signals.modified)

    @pyqtSignature('')
    def on_callableLocationSelect_clicked(self):
        name = None
        if self.callType == self.externalType:
            filename = QFileDialog.getOpenFileName(
                self, 'Select Program', '', 'Executable file (*.*)')
            if filename:
                name = filename
        elif self.callType in self.pythonTypes:
            dlg = SysPathDialog(self)
            if dlg.exec_() == dlg.Accepted:
                name = dlg.selectedEdit.text()
        else:
            pass # unknownType item (0) selected
        if name is not None:
            self.locationText = name
            self.emit(Signals.modified)

    @pyqtSignature('')
    def on_externalEditButton_clicked(self):
        settings = Settings()
        settings.beginGroup(settings.keys.app)
        editor = str(settings.value('editor', '').toString())
        if not editor:
            editor, okay = QInputDialog.getText(
                self, 'Configure Source Editor',
                'Enter editor command name.  '
                'Use $f as filename argument placeholder.')
            if okay:
                settings.setValue('editor', editor)
                editor = str(editor)
            else:
                editor = None
        if not editor:
            return
        self.externalEditProcess = editproc = QProcess(self)
        editproc.tmp = tmp = NamedTemporaryFile(
            'w+', prefix='strategy', suffix='.py')
        tmp.write(self.sourceEditorText)
        tmp.flush()
        self.connect(
            editproc, Signals.processFinished, self.on_externalEdit_finished)
        try:
            cmd = Template(editor).substitute(f=tmp.name)
        except (KeyError, ValueError, ), exc:
            print '## error', exc
        else:
            editproc.start(cmd)

    def on_externalEdit_finished(self, code, status):
        tmp = self.externalEditProcess.tmp
        if not code and not status:
            tmp.seek(0)
            self.sourceEditorText = tmp.read()
        tmp.close()
        self.externalEditProcess = None

    @pyqtSignature('')
    def on_revertButton_clicked(self):
        if self.revertSource:
            self.sourceEditorText = self.revertSource()
        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)

    @pyqtSignature('')
    def on_saveButton_clicked(self):
        if self.saveSource:
            self.saveSource(self.sourceEditorText)
        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)
