#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

# TODO: implement cut
# TODO: implement copy
# TODO: implement paste
# TODO: write serializer
# TODO: write deserializer
# TODO: write docstrings on series types

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QApplication, QMainWindow, QIcon, QLabel, QLineEdit
from PyQt4.QtGui import QStandardItem, QStandardItemModel, QToolBar, QPixmap
from PyQt4.QtGui import QComboBox, QSpinBox, QDoubleSpinBox, QSizePolicy
from PyQt4.QtGui import QFileDialog, QImageReader

from ib.ext.Contract import Contract
from ib.ext.TickType import TickType

from profit import series
from profit.lib.core import Settings, Signals
from profit.widgets.ui_tickerdesigner import Ui_TickerDesignerWindow


def fieldTypes():
    items = [(k, getattr(TickType, k)) for k in dir(TickType)]
    items = [(k, v) for k, v in items if isinstance(v, int)]
    unknown = TickType.getField(-1)
    items = [(v, TickType.getField(v)) for k, v in items]
    return dict([(k, v) for k, v in items if v != unknown])
fieldTypes = fieldTypes()


def indexTypes():
    def isIndexType(t):
        return hasattr(t, 'params')
    items = [(k, getattr(series, k)) for k in dir(series)]
    return dict([(k, v) for k, v in items if isIndexType(v)])
indexTypes = indexTypes()


class FieldItem(QStandardItem):
    def __init__(self, name):
        QStandardItem.__init__(self, name)
        self.setEditable(False)
        self.id = -1


class IndexItem(QStandardItem):
    def __init__(self, name):
        QStandardItem.__init__(self, name)
        self.setEditable(False)
        self.name = name
        self.parameters = {}


class TickerItem(QStandardItem):
    def __init__(self, tickerId, symbol, exchange='', secType='',
                 expiry='', right='', strike=0.0, currency='', settings=None):
        QStandardItem.__init__(self, symbol)
        self.setEditable(False)
        self.tickerId = tickerId
        self.symbol = symbol
        self.exchange = exchange
        self.secType = secType
        self.expiry = expiry
        self.right = right
        self.strike = strike
        self.currency = currency
        if settings:
            icon = settings.value('%s/icon' % tickerId)
            if icon.isValid():
                icon = QIcon(icon)
            else:
                path = ':images/tickers/%s.png' % symbol.lower()
                if QPixmap(path).isNull():
                    icon = QIcon(':images/icons/mime_empty.png')
                else:
                    icon = QIcon(path)
            self.setIcon(icon)


class TickerDesignerWindow(QMainWindow, Ui_TickerDesignerWindow):
    defaultText = 'Unknown'
    itemTypes = {
        TickerItem:1, FieldItem:2, IndexItem:3
    }

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.editItem = None
        self.pasteItem = None
        self.setupWidgets()
        self.readSettings()
        self.paramBuilders = {
            'line':self.buildIndexLineCombo,
            'int':self.buildIndexSpinBox,
            'float':self.buildIndexDoubleSpinBox,
            'unknown':self.buildIndexUnknown,
        }

    def buildIndexGroups(self, cls, item):
        parent = self.indexParamGroup
        layout = parent.layout().children()[0]
        builders = self.paramBuilders
        for row, (name, props) in enumerate(cls.params):
            builder = builders.get(props.get('type'), builders['unknown'])
            label = QLabel(name, parent)
            label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
            sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            label.setSizePolicy(sp)
            layout.addWidget(label, row, 0)
            layout.addWidget(builder(name, item, props, parent), row, 1)
        doc = (cls.__doc__ or '').strip()
        self.indexParamDoc.setText(doc)
        self.indexDocGroup.setVisible(bool(doc))

    # parameter editor widget builders

    def buildIndexSpinBox(self, name, item, props, parent):
        editor = QSpinBox(parent)
        editor.setButtonSymbols(editor.PlusMinus)
        editor.setAlignment(Qt.AlignRight)
        try:
            minv = props['min']
        except (KeyError, ):
            pass
        else:
            editor.setMinimum(minv)
        try:
            editor.setValue(item.parameters[name])
        except (KeyError, ):
            item.parameters[name] = editor.value()
        def onChange(value):
            item.parameters[name] = value
        editor.onChange = onChange
        editor.connect(editor, Signals.intValueChanged, onChange)
        return editor

    def buildIndexDoubleSpinBox(self, name, item, props, parent):
        editor = QDoubleSpinBox(parent)
        editor.setButtonSymbols(editor.PlusMinus)
        editor.setAlignment(Qt.AlignRight)
        editor.setSingleStep(0.01)
        try:
            minv = props['min']
        except (KeyError, ):
            pass
        else:
            editor.setMinimum(minv)
        try:
            editor.setValue(item.parameters[name])
        except (KeyError, ):
            item.parameters[name] = editor.value()
        def onChange(value):
            item.parameters[name] = value
        editor.onChange = onChange
        editor.connect(editor, Signals.doubleValueChanged, onChange)
        return editor

    def buildIndexLineCombo(self, name, item, props, parent):
        children = list(self.childrenOf(self.rootOf(item)))
        editor = QComboBox(parent)
        editor.addItems([c.text() for c in children if c.text() != item.text()])
        try:
            editor.setCurrentIndex(editor.findText(item.parameters[name]))
        except (KeyError, ):
            item.parameters[name] = ''
        @pyqtSignature('int')
        def onChange(index):
            item.parameters[name] = str(editor.currentText())
            print '##', item.parameters
        editor.onChange = onChange
        editor.connect(editor, Signals.currentIndexChanged, onChange)
        return editor

    def buildIndexUnknown(self, name, item, props, parent):
        editor = QLabel('unknown type', parent)
        return editor

    def clearIndexGroups(self):
        layout = self.indexParamGroup.layout().children()[0]
        child = layout.takeAt(0)
        while child:
             child.widget().deleteLater()
             child = layout.takeAt(0)

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()

    def enableActions(self, index=None):
        up = down = cut = delete = copy = False
        insertfield = insertindex = False
        paste = bool(self.pasteItem)
        if index and index.isValid():
            cut = copy = delete = True
            model = index.model()
            sibling = model.sibling
            row = index.row()
            up = sibling(row-1, 0, index).isValid()
            down = sibling(row+1, 0, index).isValid()
            item = model.itemFromIndex(index)
            insertfield = isinstance(item, TickerItem)
            insertindex = isinstance(item, (FieldItem, IndexItem))
        self.actionMoveUp.setEnabled(up)
        self.actionMoveDown.setEnabled(down)
        self.actionInsertIndex.setEnabled(insertindex)
        self.actionInsertField.setEnabled(insertfield)
        self.actionCut.setEnabled(cut)
        self.actionDelete.setEnabled(delete)
        self.actionCopy.setEnabled(copy)
        self.actionPaste.setEnabled(paste)

    def insertField(self):
        item = FieldItem(self.defaultText)
        self.editItem.appendRow(item)
        self.treeView.expand(item.parent().index())

    def insertIndex(self):
        item = IndexItem(self.defaultText)
        self.editItem.appendRow(item)
        self.treeView.expand(item.parent().index())

    def insertTicker(self, **kwds):
        item = TickerItem(settings=self.settings, **kwds)
        self.model.appendRow(item)

    def moveItem(self, item, offset):
        model = self.model
        index = model.indexFromItem(item)
        self.treeView.collapse(index)
        row = index.row()
        otherindex = index.sibling(row+offset, 0)
        self.treeView.collapse(otherindex)
        other = model.itemFromIndex(otherindex)
        parent = item.parent()
        if not parent:
            parent = model.invisibleRootItem()
        parent.takeChild(row+offset, 0)
        parent.takeChild(row, 0)
        parent.setChild(row+offset, item)
        parent.setChild(row, other)
        newindex = model.indexFromItem(item)
        selectmodel = self.treeView.selectionModel()
        selectmodel.clear()
        selectmodel.select(newindex, selectmodel.Select)
        self.enableActions(newindex)

    def readSettings(self):
        self.settings = settings = Settings()
        settings.beginGroup(settings.keys.designer)
        size = settings.value(
            settings.keys.size, settings.defaultSize).toSize()
        pos = settings.value(
            settings.keys.position, settings.defaultPosition).toPoint()
        maxed = settings.value(settings.keys.maximized, False).toBool()
        self.resize(size)
        self.move(pos)
        if maxed:
            self.showMaximized()
        state = settings.value(settings.keys.winstate, QVariant())
        self.restoreState(state.toByteArray())
        state = settings.value(settings.keys.splitstate, QVariant())
        self.splitter.restoreState(state.toByteArray())

    def setupFieldItem(self, item):
        combo = self.fieldCombo
        combo.setCurrentIndex(combo.findData(QVariant(item.id)))

    def setupIndexItem(self, item):
        self.indexName.setText(item.text())
        combo = self.indexCombo
        index = combo.findData(QVariant(item.name))
        combo.setCurrentIndex(index)
        data = self.indexCombo.itemData(index)
        if data.isValid():
            name = str(data.toString())
            self.clearIndexGroups()
            try:
                cls = indexTypes[name]
            except (KeyError, ):
                pass
            else:
                self.buildIndexGroups(cls, item)

    def setupTickerItem(self, item):
        self.idSpin.setValue(item.tickerId)
        self.symbolEdit.setText(item.symbol)
        combo = self.secTypeCombo
        combo.setCurrentIndex(combo.findText(item.secType))
        self.exchangeEdit.setText(item.exchange)
        self.iconPreview.setPixmap(item.icon().pixmap(32,32))
        self.expiryEdit.setText(item.expiry)
        self.strikeSpin.setValue(item.strike)
        self.currencyEdit.setText(item.currency)
        combo = self.rightCombo
        combo.setCurrentIndex(combo.findText(item.right))

    def setupWidgets(self):
        self.splitter.setSizes([150, 300])
        for toolbar in self.findChildren(QToolBar):
            self.menuToolbars.addAction(toolbar.toggleViewAction())
        self.indexCombo.addItem('<none>', QVariant())
        for name in sorted(indexTypes):
            self.indexCombo.addItem(name, QVariant(name))
        self.fieldCombo.addItem('<none>', QVariant())
        for id, name in sorted(fieldTypes.items()):
            self.fieldCombo.addItem(name, QVariant(id))

    def symbolFill(self, symbols):
        self.model = QStandardItemModel(self)
        self.treeView.setModel(self.model)
        self.treeView.header().hide()
        for data in symbols:
            self.insertTicker(**data)

    def writeSettings(self):
        settings = self.settings
        settings.setValue(settings.keys.size, self.size())
        settings.setValue(settings.keys.position, self.pos())
        settings.setValue(settings.keys.maximized, self.isMaximized())
        settings.setValue(settings.keys.winstate, self.saveState())
        settings.setValue(settings.keys.splitstate, self.splitter.saveState())

    # widget signal handlers

    def on_exchangeEdit_textEdited(self, text):
        if self.editItem:
            self.editItem.exchange = str(text)

    @pyqtSignature('int')
    def on_idSpin_valueChanged(self, value):
        item = self.editItem
        if item:
            item.tickerId = value

    def on_indexName_textChanged(self, text):
        if self.editItem:
            self.editItem.symbol = str(text)
            self.editItem.setText(text)

    @pyqtSignature('int')
    def on_secTypeCombo_currentIndexChanged(self, index):
        if self.editItem:
            self.editItem.secType = str(self.secTypeCombo.currentText())

    def on_symbolEdit_textEdited(self, text):
        if self.editItem:
            self.editItem.symbol = str(text)
            self.editItem.setText(text)

    def on_treeView_clicked(self, index):
        self.enableActions(index)
        item = self.model.itemFromIndex(index)
        itemtype = type(item)
        try:
            pageindex = self.itemTypes[itemtype]
        except (KeyError, ):
            pass
        else:
            self.stackedWidget.setCurrentIndex(pageindex)
            setup = getattr(self, 'setup%s' % itemtype.__name__, None)
            if setup:
                try:
                    self.editItem = None
                    setup(item)
                finally:
                    self.editItem = item

    # action signal handlers

    @pyqtSignature('')
    def on_actionMoveUp_triggered(self):
        item = self.editItem
        if item:
            self.moveItem(item, -1)

    @pyqtSignature('')
    def on_actionMoveDown_triggered(self):
        item = self.editItem
        if item:
            self.moveItem(item, 1)

    @pyqtSignature('')
    def on_actionDelete_triggered(self):
        item = self.editItem
        if item:
            self.editItem = None
            index = self.model.indexFromItem(item)
            self.model.removeRow(index.row(), index.parent())
            self.enableActions()
            self.treeView.selectionModel().clear()
            self.stackedWidget.setCurrentIndex(0)

    @pyqtSignature('')
    def on_actionInsertSymbol_triggered(self):
        tickerId = 1
        root = self.model.invisibleRootItem()
        items = [root.child(r, 0) for r in range(root.rowCount())]
        if items:
            tickerId += max([item.tickerId for item in items])
        self.insertTicker(tickerId=tickerId, symbol=self.defaultText)

    @pyqtSignature('')
    def on_actionInsertField_triggered(self):
        self.insertField()

    @pyqtSignature('')
    def on_actionInsertIndex_triggered(self):
        self.insertIndex()

    @pyqtSignature('int')
    def on_fieldCombo_currentIndexChanged(self, index):
        item = self.editItem
        if item:
            data = self.fieldCombo.itemData(index)
            if data.isValid():
                fid = data.toInt()[0]
                if fid in [other.id for other in self.siblings(item)]:
                    self.statusBar().showMessage(
                        'Duplicate ticker fields not allowed.', 3000)
                    self.fieldCombo.setCurrentIndex(0)
                    return
                try:
                    item.setText(fieldTypes[fid])
                except (KeyError, ):
                    pass
                else:
                    item.id = fid

    @pyqtSignature('')
    def on_iconSelect_clicked(self):
        item = self.editItem
        if item:
            formats = str.join(' ', ['*.%s' % str(fmt) for fmt in
                                     QImageReader.supportedImageFormats()])
            filename = QFileDialog.getOpenFileName(
                self, 'Select Symbol Icon', '', 'Images (%s)' % formats)
            if filename:
                icon = QIcon(filename)
                item.setIcon(icon)
                self.iconPreview.setPixmap(icon.pixmap(32,32))
                settings = self.settings
                settings.setValue('%s/icon' % item.tickerId, icon)

    @pyqtSignature('int')
    def on_indexCombo_currentIndexChanged(self, index):
        self.clearIndexGroups()
        item = self.editItem
        if item:
            data = self.indexCombo.itemData(index)
            if data.isValid():
                name = str(data.toString())
                try:
                    cls = indexTypes[name]
                except (KeyError, ):
                    pass
                else:
                    item.name = name
                    self.buildIndexGroups(cls, item)
                    self.maybeChangeIndexName(item)

    def on_expiryEdit_textEdited(self, text):
        item = self.editItem
        if item:
            item.expiry = str(text)

    @pyqtSignature('int')
    def on_rightCombo_currentIndexChanged(self, index):
        item = self.editItem
        if item:
            item.right = str(self.rightCombo.currentText())

    @pyqtSignature('double')
    def on_strikeSpin_valueChanged(self, value):
        item = self.editItem
        if item:
            item.strike = value

    def on_currencyEdit_textEdited(self, text):
        item = self.editItem
        if item:
            item.currency = str(text)

    def maybeChangeIndexName(self, item):
        widget = self.indexName
        if widget.text() not in [self.defaultText, '']:
            return
        matches = self.model.findItems(
            item.name, Qt.MatchStartsWith|Qt.MatchRecursive)
        suffix = 1
        for match in matches:
            if self.rootOf(item) == self.rootOf(match):
                try:
                    name = str(match.text())
                    offset = int(name.split('-')[1])
                except (ValueError, IndexError, ), ex:
                    pass
                else:
                    suffix = max(suffix, offset+1)
        widget.setText('%s-%s' % (item.name, suffix))

    def rootOf(self, item):
        while True:
            if item.parent():
                item = item.parent()
            else:
                break
        return item

    def siblings(self, item):
        parent = item.parent()
        for r in range(parent.rowCount()):
            child = parent.child(r, 0)
            if child is not item:
                yield child

    def childrenOf(self, item):
        for r in range(item.rowCount()):
            child = item.child(r, 0)
            yield child
            for c in self.childrenOf(child):
                yield c



testSymbols = [
    {'tickerId':100, 'symbol':'AAPL', 'exchange':'SMART', 'secType':'STK'},
    {'tickerId':101, 'symbol':'EBAY', 'exchange':'SMART', 'secType':'STK'},
    {'tickerId':102, 'symbol':'NVDA', 'exchange':'NASDAQ', 'secType':'STK'},
]


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = TickerDesignerWindow()
    window.symbolFill(testSymbols)
    window.show()
    sys.exit(app.exec_())
