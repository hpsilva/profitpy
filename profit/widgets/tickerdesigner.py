#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

# TODO: write serializer
# TODO: write deserializer
# TODO: write docstrings on series types
# TODO: add defaults to series params and set in editors
# TODO: implement new, open, save, save as and close

from PyQt4.QtCore import QByteArray, QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QApplication, QMainWindow, QIcon, QLabel, QLineEdit
from PyQt4.QtGui import QStandardItem, QStandardItemModel, QToolBar, QPixmap
from PyQt4.QtGui import QComboBox, QSpinBox, QDoubleSpinBox, QSizePolicy
from PyQt4.QtGui import QBrush, QColor, QFileDialog, QImageReader

from ib.ext.Contract import Contract
from ib.ext.TickType import TickType

from profit import series
from profit.lib.core import Settings, Signals
from profit.widgets.ui_tickerdesigner import Ui_TickerDesigner


def defaultSplitterState():
    """ Resonable default for plot splitter state.

    @return QByteArray suitable for use with QSplitter.restoreState
    """
    return QByteArray.fromBase64(
        'AAAA/wAAAAAAAAADAAAAkwAAAVUAAACiAQAAAAYBAAAAAQ==')


def tickerFieldTypes():
    """ Creates mapping of ticker data fields to field names.

    @return field to field name mapping
    """
    items = [(k, getattr(TickType, k)) for k in dir(TickType)]
    items = [(k, v) for k, v in items if isinstance(v, int)]
    unknown = TickType.getField(-1)
    items = [(v, TickType.getField(v)) for k, v in items]
    return dict([(k, v) for k, v in items if v != unknown])


def seriesIndexTypes():
    """ Creates mapping of index class names to index types.

    @return index class name to index class mapping.
    """
    def isIndexType(t):
        return hasattr(t, 'params')
    items = [(k, getattr(series, k)) for k in dir(series)]
    return dict([(k, v) for k, v in items if isIndexType(v)])


class SchemaItem(QStandardItem):
    """ Base class for schema tree items.

    """
    def __init__(self, text):
        """ Constructor.

        @param text string value for item
        """
        QStandardItem.__init__(self, text)
        self.setEditable(False)
        self.cutSource = self.copySource = False

    def resetForeground(self):
        self.setForeground(QApplication.activeWindow().palette().text())

    def setCopy(self):
        self.copySource = True
        self.cutSource = False
        self.setForeground(QBrush(QColor(Qt.blue)))

    def setCut(self):
        self.cutSource = True
        self.copySource = False
        self.setForeground(QBrush(QColor(Qt.red)))

    @property
    def immediateChildren(self):
        """ Yields each immediate child of this item.

        """
        for row in range(self.rowCount()):
            yield self.child(row)

    @property
    def children(self):
        """ Yields all children of this item.

        """
        for r in range(self.rowCount()):
            child = self.child(r, 0)
            yield child
            for c in child.children:
                yield c

    @property
    def siblings(self):
        """ Yields each sibling of this item.

        """
        parent = self.parent()
        for r in range(parent.rowCount()):
            child = parent.child(r, 0)
            if child is not self:
                yield child

    @property
    def root(self):
        """ Returns the top-most parent of this item.

        """
        item = self
        while True:
            if item.parent():
                item = item.parent()
            else:
                break
        return item


class TickerItem(SchemaItem):
    """ Schema tree root-level items.

    TickerItems may contain FieldItems only.  This restriction is
    enforced by the gui.
    """
    def __init__(self, tickerId, symbol, exchange='', secType='',
                 expiry='', right='', strike=0.0, currency=''):
        """ Constructor.

        @param tickerId numeric identifier of ticker
        @param symbol underlying ticker symbol as string
        """
        SchemaItem.__init__(self, symbol)
        self.tickerId = tickerId
        self.symbol = symbol
        self.exchange = exchange
        self.secType = secType
        self.expiry = expiry
        self.right = right
        self.strike = strike
        self.currency = currency

    def loadIcon(self, settings):
        """ Load and set an icon appropriate for this item.

        @param settings QSettings instance
        @return None
        """
        icon = settings.value('%s/icon' % self.tickerId)
        if icon.isValid():
            icon = QIcon(icon)
        else:
            path = ':images/tickers/%s.png' % self.symbol.lower()
            if QPixmap(path).isNull():
                icon = QIcon(':images/icons/mime_empty.png')
            else:
                icon = QIcon(path)
        self.setIcon(icon)

    @property
    def schema(self):
        """ Generated schema dictionary for this item.

        """
        fields = [child.schema for child in self.immediateChildren]
        return dict(tickerId=self.tickerId,
                    symbol=self.symbol,
                    exchange=self.exchange,
                    secType=self.secType,
                    expiry=self.expiry,
                    right=self.right,
                    strike=self.strike,
                    currency=self.currency,
                    fields=fields)


class FieldItem(SchemaItem):
    """ Child item type for TickerItems.

    FieldItems store a ticker data field that corresponds to the data
    field of incoming market data.
    """
    def __init__(self, name):
        """ Constructor.

        @param name string value for item
        """
        SchemaItem.__init__(self, name)
        self.id = -1

    def clone(self):
        clone = FieldItem(self.text())
        clone.id = self.id
        for child in self.immediateChildren:
            clone.appendRow(child.clone())
        return clone

    @property
    def schema(self):
        """ Generated schema dictionary for this item.

        """
        indexes = [child.schema for child in self.immediateChildren]
        return dict(name=str(self.text()), id=self.id, indexes=indexes)


class IndexItem(SchemaItem):
    """ Child item type for FieldItems and other IndexItems.

    IndexItems store the name of the class to construct the index, as
    well as a dictionary of parameters for the index class
    constructor.
    """
    def __init__(self, typeName):
        """ Constructor.

        @param typeName index class name as string
        """
        SchemaItem.__init__(self, typeName)
        self.typeName = typeName
        self.parameters = {}

    def clone(self):
        clone = IndexItem(self.text())
        clone.typeName = self.typeName
        clone.parameters = self.parameters.copy()
        self.deepClone(self, clone)
        return clone

    def deepClone(self, source, target):
        for child in source.immediateChildren:
            clone = child.clone()
            target.appendRow(clone)
            self.deepClone(child, clone)

    @property
    def schema(self):
        """ Generated schema dictionary for this item.

        """
        data = self.parameters.copy()
        indexes = [child.schema for child in self.immediateChildren]
        data.update(typeName=self.typeName, indexes=indexes)
        return data


class TickerDesigner(QMainWindow, Ui_TickerDesigner):
    """ Ticker Designer main window class.

    """
    defaultText = 'Unknown'
    fieldTypes = tickerFieldTypes()
    indexTypes = seriesIndexTypes()
    itemTypePages = {TickerItem:1, FieldItem:2, IndexItem:3}

    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor of this widget
        """
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.editItem = None
        self.clipItem = None
        self.setupWidgets()
        self.readSettings()
        self.lastSaved = None

    # index parameter and documentation group methods

    def buildIndexParamWidgets(self, cls, item):
        """ Rebuilds the index parameter group widgets.

        @param cls index class object
        @param item IndexItem instance
        @return None
        """
        parent = self.indexParamGroup
        layout = parent.layout().children()[0]
        parent.setVisible(bool(cls.params))
        for row, (name, props) in enumerate(cls.params):
            builder = getattr(self, '%sEditor' % props.get('type', 'unknown'),
                              self.unknownEditor)
            label = QLabel(name, parent)
            label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
            sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            label.setSizePolicy(sp)
            layout.addWidget(label, row, 0)
            layout.addWidget(builder(name, item, props, parent), row, 1)

    def buildIndexDocWidgets(self, cls):
        """ Rebuilds the index parameter documentation widgets.

        @param cls index class object or None
        @return None
        """
        if cls:
            doc = (cls.__doc__ or '').strip()
        else:
            doc = ''
        self.indexParamDoc.setText(doc)
        self.indexDocGroup.setVisible(bool(doc))

    def resetIndexWidgets(self):
        """ Removes parameter group widgets, hides parameter and doc groups.

        @return None
        """
        self.buildIndexDocWidgets(None)
        group = self.indexParamGroup
        layout = group.layout().children()[0]
        child = layout.takeAt(0)
        while child:
             child.widget().deleteLater()
             child = layout.takeAt(0)
        group.setVisible(False)

    # parameter editor widget builder methods

    def intEditor(self, name, item, props, parent):
        """ Creates a new editor suitable for integer values.

        @param name item parameter name, as string, to receive value updates
        @param item IndexItem instance
        @param props mapping of index class constructor properties
        @param parent ancestor of new widget
        @return QSpinBox widget
        """
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

    def floatEditor(self, name, item, props, parent):
        """ Creates a new editor suitable for float values.

        @param name item parameter name, as string, to receive value updates
        @param item IndexItem instance
        @param props mapping of index class constructor properties
        @param parent ancestor of new widget
        @return QDoubleSpinBox widget
        """
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

    def lineEditor(self, name, item, props, parent):
        """ Creates a new editor suitable for selecting a series or index.

        @param name item parameter name, as string, to receive value updates
        @param item IndexItem instance
        @param props mapping of index class constructor properties
        @param parent ancestor of new widget
        @return QComboBox widget
        """
        children = list(item.root.children)
        editor = QComboBox(parent)
        editor.addItem('')
        exclude = [item.text(), self.defaultText]
        editor.addItems([c.text() for c in children
                         if c.text() not in exclude])
        try:
            editor.setCurrentIndex(editor.findText(item.parameters[name]))
        except (KeyError, ):
            item.parameters[name] = ''
        @pyqtSignature('int')
        def onChange(index):
            item.parameters[name] = str(editor.currentText())
        editor.onChange = onChange
        editor.connect(editor, Signals.currentIndexChanged, onChange)
        return editor

    def unknownEditor(self, name, item, props, parent):
        """ Creates a new display widget for an unknown parameter type.

        @param name item parameter name, as string, to receive value updates
        @param item IndexItem instance
        @param props mapping of index class constructor properties
        @param parent ancestor of new widget
        @return QLabel widget
        """
        editor = QLabel('unknown type', parent)
        return editor

    # ordinary methods

    def addTickerItem(self, **kwds):
        """ Creates new TickerItem at the model root.

        @param **kwds key-value pairs passed to TickerItem constructor
        @return created TickerItem instance
        """
        item = TickerItem(**kwds)
        item.loadIcon(self.settings)
        self.model.appendRow(item)
        return item

    def addFieldItem(self):
        """ Creates new FieldItem as child of the current selection.

        @return created FieldItem instance
        """
        item = FieldItem(self.defaultText)
        self.editItem.appendRow(item)
        self.treeView.expand(item.parent().index())
        return item

    def addIndexItem(self):
        """ Creates new IndexItem as child of the current selection.

        @return created IndexItem instance
        """
        item = IndexItem(self.defaultText)
        self.editItem.appendRow(item)
        self.treeView.expand(item.parent().index())
        return item

    def closeEvent(self, event):
        """ Framework close event handler.  Writes settings and accepts event.

        @param event QCloseEvent instance
        @return None
        """
        self.writeSettings()
        event.accept()

    def enableActions(self, index):
        """ Enables or disables edit and design actions.

        @param index QModelIndex instance or None
        @return None
        """
        up = down = cut = delete = copy = paste = False
        isticker = isindexorfield = False
        if index and index.isValid():
            clip = self.clipItem
            model = index.model()
            item = model.itemFromIndex(index)
            isticker = isinstance(item, TickerItem)
            isfield = isinstance(item, FieldItem)
            isindex = isinstance(item, IndexItem)
            isindexorfield = isfield or isindex
            ## can always delete an item
            delete = True
            ## can only cut and copy field and index items
            cut = copy = isindexorfield
            ## can only paste certain combinations
            if isticker:
                paste = isinstance(clip, FieldItem)
            elif isfield:
                paste = isinstance(clip, IndexItem)
            elif isindex:
                paste = isinstance(clip, IndexItem)
            if clip and clip.cutSource and clip == item:
                paste = False
            up = model.sibling(index.row()-1, 0, index).isValid()
            down = model.sibling(index.row()+1, 0, index).isValid()

        self.actionMoveUp.setEnabled(up)
        self.actionMoveDown.setEnabled(down)
        self.actionInsertIndex.setEnabled(isindexorfield)
        self.actionInsertField.setEnabled(isticker)
        self.actionCut.setEnabled(cut)
        self.actionDelete.setEnabled(delete)
        self.actionCopy.setEnabled(copy)
        self.actionPaste.setEnabled(paste)

    def moveItem(self, item, offset):
        """ Moves item up or down schema tree.

        @param item SchemaItem instance to move.
        @param offset -1 to move up, 1 to move down
        @return None
        """
        model = self.model
        index = model.indexFromItem(item)
        tree = self.treeView
        tree.collapse(index)
        row = index.row()
        otherindex = index.sibling(row+offset, 0)
        tree.collapse(otherindex)
        other = model.itemFromIndex(otherindex)
        parent = item.parent()
        if not parent:
            parent = model.invisibleRootItem()
        parent.takeChild(row+offset, 0)
        parent.takeChild(row, 0)
        parent.setChild(row+offset, item)
        parent.setChild(row, other)
        newindex = model.indexFromItem(item)
        selectmodel = tree.selectionModel()
        selectmodel.clear()
        selectmodel.select(newindex, selectmodel.Select)
        self.enableActions(newindex)

    def readSettings(self):
        """ Applies stored setting values to instance.

        @return None
        """
        self.settings = obj = Settings()
        obj.beginGroup(obj.keys.designer)
        self.resize(obj.value(obj.keys.size, obj.defaultSize).toSize())
        self.move(obj.value(obj.keys.position, obj.defaultPosition).toPoint())
        if obj.value(obj.keys.maximized, False).toBool():
            self.showMaximized()
        self.restoreState(
            obj.value(obj.keys.winstate, QVariant()).toByteArray())
        state = obj.value(
            obj.keys.splitstate, defaultSplitterState()).toByteArray()
        self.splitter.restoreState(state)

    def setupTickerItem(self, item):
        """ Configures ticker page widgets from given item.

        @param item TickerItem instance
        @return None
        """
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

    def setupFieldItem(self, item):
        """ Configures field page widgets from given item.

        @param item FieldItem instance
        @return None
        """
        combo = self.fieldCombo
        combo.setCurrentIndex(combo.findData(QVariant(item.id)))

    def setupIndexItem(self, item):
        """ Configures index page widgets from given item.

        @param item IndexItem instance
        @return None
        """
        self.indexName.setText(item.text())
        combo = self.indexCombo
        index = combo.findData(QVariant(item.typeName))
        combo.setCurrentIndex(index)
        data = self.indexCombo.itemData(index)
        if data.isValid():
            name = str(data.toString())
            self.resetIndexWidgets()
            try:
                cls = self.indexTypes[name]
            except (KeyError, ):
                pass
            else:
                self.buildIndexParamWidgets(cls, item)
                self.buildIndexDocWidgets(cls)

    def setupWidgets(self):
        """ Configures window widgets for initial display.

        @return None
        """
        self.splitter.setSizes([150, 300])
        for toolbar in self.findChildren(QToolBar):
            self.menuToolbars.addAction(toolbar.toggleViewAction())
        self.indexCombo.addItem('<none>', QVariant())
        for name in sorted(self.indexTypes):
            self.indexCombo.addItem(name, QVariant(name))
        self.fieldCombo.addItem('<none>', QVariant())
        for id, name in sorted(self.fieldTypes.items()):
            self.fieldCombo.addItem(name, QVariant(id))

    def showMessage(self, text, duration=3000):
        self.statusBar().showMessage(text, duration)

    def readSchema(self, schema):
        """ Creates tree items from given schema.

        @param schema ticker schema as dictionary
        @return None
        """
        self.model = QStandardItemModel(self)
        self.treeView.setModel(self.model)
        self.treeView.header().hide()
        for data in schema:
            self.addTickerItem(**data)

    def writeSettings(self):
        """ Saves window settings and state.

        @return None
        """
        settings = self.settings
        settings.setValue(settings.keys.size, self.size())
        settings.setValue(settings.keys.position, self.pos())
        settings.setValue(settings.keys.maximized, self.isMaximized())
        settings.setValue(settings.keys.winstate, self.saveState())
        settings.setValue(settings.keys.splitstate, self.splitter.saveState())

    def maybeChangeIndexName(self, item, previous):
        """ Changes index name if appropriate.

        @param item IndexItem instance
        @param previous last index type name
        @return None
        """
        widget = self.indexName
        current = str(widget.text())
        include = [self.defaultText, '']
        if current in include or current.startswith('%s-' % previous):
            flags = Qt.MatchStartsWith | Qt.MatchRecursive
            matches = self.model.findItems(item.typeName, flags)
            suffix = 1
            for match in matches:
                if item.root == match.root:
                    try:
                        name = str(match.text())
                        offset = int(name.split('-')[1])
                    except (ValueError, IndexError, ), ex:
                        pass
                    else:
                        suffix = max(suffix, offset+1)
            widget.setText('%s-%s' % (item.typeName, suffix))

    # widget signal handlers

    def on_currencyEdit_textEdited(self, text):
        """ Signal handler for ticker currency line edit widget text changes.

        @param text new value for line edit
        @return None
        """
        item = self.editItem
        if item:
            item.currency = str(text)

    def on_exchangeEdit_textEdited(self, text):
        """ Signal handler for exchange line edit widget text changes.

        @param text new value for line edit
        @return None
        """
        if self.editItem:
            self.editItem.exchange = str(text)

    def on_expiryEdit_textEdited(self, text):
        """ Signal handler for ticker expiry line edit widget text changes.

        @param text new value for line edit
        @return None
        """
        item = self.editItem
        if item:
            item.expiry = str(text)

    @pyqtSignature('int')
    def on_fieldCombo_currentIndexChanged(self, index):
        """ Signal handler for field type combobox selection changes.

        @param index selected item index
        @return None
        """
        item = self.editItem
        if item:
            data = self.fieldCombo.itemData(index)
            if data.isValid():
                fid = data.toInt()[0]
                if fid in [other.id for other in item.siblings]:
                    self.showMessage('Duplicate ticker fields not allowed.')
                    self.fieldCombo.setCurrentIndex(0)
                    return
                old = item.text()
                try:
                    new = self.fieldTypes[fid]
                    item.setText(new)
                except (KeyError, ):
                    pass
                else:
                    item.id = fid
                    self.renameLines(item, old, new)


    @pyqtSignature('')
    def on_iconSelect_clicked(self):
        """ Signal handler for select icon button.

        @return None
        """
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
    def on_idSpin_valueChanged(self, value):
        """ Signal handler for ticker id spin box changes.

        @param value new value of spinbox
        @return None
        """
        item = self.editItem
        if item:
            item.tickerId = value

    @pyqtSignature('int')
    def on_indexCombo_currentIndexChanged(self, index):
        """ Signal handler for index type combobox selection changes.

        @param index selected item index
        @return None
        """
        self.resetIndexWidgets()
        item = self.editItem
        if item:
            data = self.indexCombo.itemData(index)
            if data.isValid():
                typeName = str(data.toString())
                try:
                    cls = self.indexTypes[typeName]
                except (KeyError, ):
                    pass
                else:
                    old = item.typeName
                    item.typeName = typeName
                    self.buildIndexParamWidgets(cls, item)
                    self.buildIndexDocWidgets(cls)
                    self.maybeChangeIndexName(item, old)

    def on_indexName_textChanged(self, text):
        """ Signal handler for index name line edit widget changes.

        @param text new value for line edit
        @return None
        """
        try:
            old = self.indexName.oldText
        except (AttributeError, ):
            old = self.indexName.oldText = ''
        self.renameLines(self.editItem, old, text)
        self.indexName.oldText = str(text)
        if self.editItem:
            self.editItem.symbol = str(text)
            self.editItem.setText(text)

    @pyqtSignature('int')
    def on_rightCombo_currentIndexChanged(self, index):
        """ Signal handler for security right combobox selection changes.

        @param index selected item index
        @return None
        """
        item = self.editItem
        if item:
            item.right = str(self.rightCombo.currentText())

    @pyqtSignature('int')
    def on_secTypeCombo_currentIndexChanged(self, index):
        """ Signal handler for security type combobox selection changes.

        @param index selected item index
        @return None
        """
        if self.editItem:
            self.editItem.secType = str(self.secTypeCombo.currentText())

    @pyqtSignature('double')
    def on_strikeSpin_valueChanged(self, value):
        """ Signal handler for ticker strike price spin box changes.

        @param value new value of spinbox
        @return None
        """
        item = self.editItem
        if item:
            item.strike = value

    def on_symbolEdit_textEdited(self, text):
        """ Signal handler for symbol name line edit widget changes.

        @param text new value for line edit
        @return None
        """
        if self.editItem:
            self.editItem.symbol = str(text)
            self.editItem.setText(text)

    def on_treeView_clicked(self, index):
        """ Signal handler for schema tree mouse click.

        @param index QModelIndex instance
        @return None
        """
        self.enableActions(index)
        item = self.model.itemFromIndex(index)
        itemtype = type(item)
        try:
            pageindex = self.itemTypePages[itemtype]
        except (KeyError, ):
            pass
        else:
            self.controlStack.setCurrentIndex(pageindex)
            setup = getattr(self, 'setup%s' % itemtype.__name__, None)
            if setup:
                try:
                    self.editItem = None
                    setup(item)
                finally:
                    self.editItem = item

    # action signal handlers

    @pyqtSignature('')
    def on_actionCopy_triggered(self):
        if not self.actionCopy.isEnabled():
            return
        if self.clipItem:
            self.clipItem.resetForeground()
        self.clipItem = self.editItem
        self.clipItem.setCopy()

    @pyqtSignature('')
    def on_actionCut_triggered(self):
        if not self.actionCut.isEnabled():
            return
        if self.clipItem:
            self.clipItem.resetForeground()
        self.clipItem = self.editItem
        self.clipItem.setCut()

    @pyqtSignature('')
    def on_actionPaste_triggered(self):
        if not self.actionPaste.isEnabled():
            return
        sourceitem = self.clipItem
        targetitem = self.editItem
        model = self.model
        sourcerow = model.indexFromItem(sourceitem).row()
        sourceparent = sourceitem.parent()
        if sourceitem.cutSource:
            sourceparent.takeChild(sourcerow, 0)
            newchild = sourceitem
        else:
            newchild = sourceitem.clone()
        targetitem.setChild(targetitem.rowCount(), newchild)
        if sourceitem.cutSource:
            newchild.resetForeground()
            model.removeRow(sourcerow, sourceparent.index())
            self.clipItem = None
        self.enableActions(model.indexFromItem(targetitem))

    @pyqtSignature('')
    def on_actionDelete_triggered(self):
        """ Signal handler for item delete action; removes item from tree.

        @return None
        """
        item = self.editItem
        if item:
            self.editItem = None
            index = self.model.indexFromItem(item)
            self.model.removeRow(index.row(), index.parent())
            self.enableActions(None)
            self.treeView.selectionModel().clear()
            self.controlStack.setCurrentIndex(0)

    @pyqtSignature('')
    def on_actionInsertTicker_triggered(self):
        """ Signal handler for insert ticker action; adds ticker item to tree.

        @return None
        """
        tickerId = 1
        root = self.model.invisibleRootItem()
        items = [root.child(r, 0) for r in range(root.rowCount())]
        if items:
            tickerId += max([item.tickerId for item in items])
        self.addTickerItem(tickerId=tickerId, symbol=self.defaultText)

    @pyqtSignature('')
    def on_actionInsertField_triggered(self):
        """ Signal handler for insert field action; adds field item to tree.

        @return None
        """
        self.addFieldItem()

    @pyqtSignature('')
    def on_actionInsertIndex_triggered(self):
        """ Signal handler for insert index action; adds index item to tree.

        """
        self.addIndexItem()

    @pyqtSignature('')
    def on_actionMoveDown_triggered(self):
        """ Signal handler for item move down action; moves item down tree.

        @return None
        """
        item = self.editItem
        if item:
            self.moveItem(item, 1)

    @pyqtSignature('')
    def on_actionMoveUp_triggered(self):
        """ Signal handler for item move up action; moves item up tree.

        @return None
        """
        item = self.editItem
        if item:
            self.moveItem(item, -1)

    @pyqtSignature('')
    def on_actionPrintSchema_triggered(self):
        """ Signal handler for print schema action; writes schema to stdout.

        @return None
        """
        import pprint
        for item in self.schema:
            pprint.pprint(item)
            print

    @property
    def schema(self):
        root = self.model.invisibleRootItem()
        return [root.child(row).schema for row in range(root.rowCount())]

    def renameLines(self, item, previous, current):
        if item:
            previous, current = str(previous), str(current)
            def pred(obj):
                return obj != item and hasattr(obj, 'parameters')
            for child in [c for c in item.root.children if pred(c)]:
                for key, value in child.parameters.items():
                    if value == previous:
                        child.parameters[key] = current


testSymbols = [
    {'tickerId':100, 'symbol':'AAPL', 'exchange':'SMART', 'secType':'STK'},
    {'tickerId':101, 'symbol':'EBAY', 'exchange':'SMART', 'secType':'STK'},
    {'tickerId':102, 'symbol':'NVDA', 'exchange':'NASDAQ', 'secType':'STK'},
]


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = TickerDesigner()
    window.readSchema(testSymbols)
    window.show()
    sys.exit(app.exec_())
