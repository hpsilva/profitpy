#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2
import logging
import sys

from os.path import abspath, exists
from string import Template
from tempfile import NamedTemporaryFile

from PyQt4.QtCore import QProcess, QVariant, pyqtSignature
from PyQt4.QtGui import QFileDialog, QFrame, QInputDialog, QMessageBox

from profit.lib.core import Settings, Signals
from profit.lib.widgets.syspathdialog import SysPathDialog
from profit.lib.widgets.ui_callableselect import Ui_CallableSelectWidget


class CallableSelectWidget(QFrame, Ui_CallableSelectWidget):
    revertSource = None
    saveSource = None

    (unsetType, externalType, objectType, factoryType,
     sourceType, fileType) = range(6)
    callTypeMap = {
        unsetType:'',
        externalType:'external',
        objectType:'object',
        factoryType:'factory',
        sourceType:'source',
        fileType:'file',
    }
    pythonTypes = [
        callTypeMap[objectType],
        callTypeMap[factoryType],
        callTypeMap[sourceType],
    ]
    fsTypes = [
        callTypeMap[externalType],
        callTypeMap[fileType],
    ]

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.externalEditProcess = None
        setr = self.callableType.setItemData
        for key, value in self.callTypeMap.items():
            setr(key, QVariant(value))

    def basicAttrs(self, **kwds):
        items = [
            ('callType', self.unsetType),
            ('locationText', ''),
            ('sourceEditorText', ''),
            ('revertSource', None),
            ('saveSource', None), ]
        for name, default in items:
            logging.debug("setting attr %s", name)
            setattr(self, name, kwds.get(name, default))

    def basicSetup(self,  **kwds):
        logging.debug("editor basicSetup")

        #logging.debug("sourceEditorText", self.sourceEditorText)


        for key, value in self.callTypeMap.items():
            if kwds.get('disable%sType' % value.title(), False):
                self.callableType.removeItem(
                    self.callableType.findData(QVariant(value)))
                self.stackedWidget.removeWidget(
                    self.stackedWidget.widget(key))
        self.basicAttrs(**kwds)
        self.saveButton.setEnabled(False)
        self.revertButton.setEnabled(False)


    def callTypeText(self):
        return self.callableType.currentText()

    callTypeText = property(callTypeText)

    def getCallType(self):
        wid = self.callableType
        return str(wid.itemData(wid.currentIndex()).toString())

    def setCallType(self, value):
        wid = self.callableType
        wid.setCurrentIndex(wid.findData(QVariant(value)))

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

    def warn(self, text, widget=None):
        format = '<b>Warning:</b> %s.' if text else '%s'
        if widget is None:
            widget = self.locationWarning
        widget.setText(format % text)

    def on_textEdit_textChanged(self):
        try:
            self.callableCode()
        except (SyntaxError, ):
            msg = 'invalid syntax'
        else:
            msg = ''
        self.warn(msg, self.sourceWarning)
        self.saveButton.setEnabled(True)
        self.revertButton.setEnabled(True)
        self.emit(Signals.modified)

    @pyqtSignature('int')
    def on_callableType_currentIndexChanged(self, index):
        if index == self.externalType:
            self.checkLocationExists()
        self.callableLocationSelect.setDisabled(
            self.callType == self.callTypeMap[self.sourceType])
        self.emit(Signals.modified)

    def checkLocationExists(self):
        if not exists(abspath(self.locationText)):
            msg = 'location does not exist'
        else:
            msg = ''
        self.warn(msg)

    def callableCode(self):
        try:
            src = self.sourceEditorText
        except (AttributeError, ):
            src = ''
        return compile(src, 'strategyeditsrc', 'exec')

    def on_callableLocation_textChanged(self, text):
        self.warn('')
        if self.callType == self.callTypeMap[self.sourceType]:
            try:
                code = self.callableCode()
            except (SyntaxError, ):
                msg = 'invalid syntax'
            else:
                text = str(text)
                if text and text in code.co_names:
                    msg = ''
                else:
                    msg = 'expression not found in source'
            self.warn(msg)
        elif self.callType in self.fsTypes:
            self.checkLocationExists()
        self.emit(Signals.modified)

    @pyqtSignature('')
    def on_callableLocationSelect_clicked(self):
        name = None
        calltype = self.callType
        if calltype in self.fsTypes:
            filename = QFileDialog.getOpenFileName(
                self, 'Select %s' % self.callTypeText, '',
                'Executable file (*.*)')
            if filename:
                name = filename
        elif calltype in self.pythonTypes:
            dlg = SysPathDialog(self)
            if dlg.exec_() == dlg.Accepted:
                name = dlg.selectedEdit.text()
        elif not calltype:
            QMessageBox.warning(
                self, 'Invalid Type', 'Select a callable type first.')
        else:
            pass # unknownType item (0) selected
        if name is not None:
            self.locationText = name
            self.emit(Signals.modified)

    @pyqtSignature('')
    def on_externalEditButton_clicked(self):
        settings = Settings()
        settings.beginGroup(settings.keys.main)
        editor = str(settings.value('externalEditor', '').toString())
        if not editor:
            editor, okay = QInputDialog.getText(
                self, 'Configure Source Editor',
                'Enter editor command name.  '
                'Use $f as filename argument placeholder.')
            if okay:
                settings.setValue('externalEditor', editor)
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


if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    window = CallableSelectWidget(parent=None)
    window.show()
    sys.exit(app.exec_())
