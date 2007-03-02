#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import Qt
from PyQt4.QtGui import (QColor, QColorDialog, QFrame, QPen,
                         QStandardItem, QStandardItemModel, )
from PyQt4.Qwt5 import QwtPlotCurve

from ib.ext.TickType import TickType

from profit.lib import Settings, Signals, colorIcon
from profit.widgets.ui_plot import Ui_Plot


class ControlTreeItem(QStandardItem):
    """ Self-configuring control tree item.

    """
    def __init__(self, text, icon):
        """ Constructor.

        @param text string for first column
        @param icon QIcon instance for first column
        """
        QStandardItem.__init__(self, text)
        self.setCheckable(True)
        self.setCheckState(Qt.Unchecked)
        self.setEditable(False)
        self.setIcon(icon)


class Plot(QFrame, Ui_Plot):
    """ Plot container.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor of this widget
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.curves = {}
        self.colors = {}
        self.ydata = {}
        self.session = None
        self.settings = Settings()
        self.tickerId = None
        self.plotSplitter.setSizes([80, 300])

    def setSession(self, session, tickerId, *indexes):
        """ Associate a session with this instance.

        @param session Session instance
        @param tickerId id of ticker as integer
        @param *indexes unused
        @return None
        """
        self.session = session
        self.tickerCollection = session.tickerCollection
        self.tickerId = tickerId
        self.setupModel()
        self.setupTree()
        session.registerMeta(self)

    def setupModel(self):
        """ Configure the model and initial items for this instance.

        @return None
        """
        self.dataModel = dataModel = QStandardItemModel(self)
        ticker = self.tickerCollection[self.tickerId]
        root = dataModel.invisibleRootItem()
        for key in sorted(ticker.series):
            self.addSeries(key)
        self.connect(dataModel, Signals.standardItemChanged,
                     self.on_controlTree_itemChanged)

    def setupTree(self):
        """ Configures the controls tree for this instance.

        @return None
        """
        tree = self.controlTree
        tree.header().hide()
        model = self.dataModel
        tree.setModel(model)
        for col in range(model.columnCount()):
            tree.resizeColumnToContents(col)

    def addCurve(self, key, color, data):
        """ Creates a new, empty plot curve for the given key.

        @param key curve key
        @param color QColor instance associated with curve
        @param data sequence associated with curve
        @return None
        """
        self.curves[key] = curve = QwtPlotCurve()
        curve.setStyle(QwtPlotCurve.Lines)
        self.colors[key] = color
        self.ydata[key] = data

    def addSeries(self, key):
        """ Creates new controls and curve for an individual series.

        @param key series key
        @return None
        """
        dataModel = self.dataModel
        ticker = self.tickerCollection[self.tickerId]
        series = ticker.series[key]
        root = dataModel.invisibleRootItem()
        name = TickType.getField(key)
        color = self.curveColor(name)
        icon = colorIcon(color)
        item = ControlTreeItem(name, icon)
        root.appendRow(item)
        rowcol = item.row(), item.column()
        self.addCurve(rowcol, color, series)
        for index in series.indexes:
            color = self.curveColor(name, index.name)
            icon = colorIcon(color)
            subitem = ControlTreeItem(index.name, icon)
            item.appendRow(subitem)
            subrowcol = rowcol + (subitem.row(), subitem.column())
            self.addCurve(subrowcol, color, index)

    defaultCurveColors = {
        ('bidSize', ):'blue',
        ('bidSize', 'MACD'):'black',
    }

    def curveColor(self, *names):
        """ Loads color for named curve.

        @param *names one or more strings to form settings key
        @return QColor instance
        """
        names = tuple([str(name) for name in names])
        settings = self.settings
        settings.beginGroup(settings.keys.plots)
        key = '%s:%s' % (self.tickerId, str.join(':', names))
        default = self.defaultCurveColors.get(names, 'red')
        value = settings.value(key, default)
        settings.endGroup()
        return QColor(value)

    def saveCurveColor(self, color, *names):
        """ Saves named curve color setting.

        @param color QColor instance
        @param *names one or more strings to form settings key
        @return None
        """
        names = [str(name) for name in names]
        settings = self.settings
        settings.beginGroup(settings.keys.plots)
        key = '%s:%s' % (self.tickerId, str.join(':', names))
        settings.setValue(key, color)
        settings.endGroup()

    def enableCurve(self, item, enable=True):
        """ Sets the visibility and style of a plot curve.

        @param item tree widget item
        @param enabled if True, curve is configured and enabled,
                       otherwise curve is set invisible
        @return None
        """
        key = (item.row(), item.column())
        parent = item.parent()
        if parent:
            key = (parent.row(), parent.column()) + key
        try:
            curve = self.curves[key]
        except (KeyError, ):
            pass
        else:
            plot = self.plotWidget
            if enable:
                curve.setVisible(True)
                y = self.ydata[key]
                x = range(len(y))
                curve.setData(x, y)
                curve.attach(plot)
                curve.setPen(QPen(self.colors[key]))
            else:
                curve.setVisible(False)
            plot = self.plotWidget
            plot.updateLayout()
            plot.replot()

    def on_session_createdSeries(self, tickerId, field):
        """ Signal handler called when new Series objects are created.

        @param tickerId id of ticker with new series
        @param field series field
        """
        if tickerId != self.tickerId:
            return
        if field not in self.tickerCollection[tickerId].series:
            return
        self.addSeries(field)

    def on_session_TickPrice_TickSize(self, message):
        """ Signal handler for TickPrice and TickSize session messages.

        @param message Message instance
        @return None
        """
        if message.tickerId != self.tickerId:
            return
        ydata = self.ydata
        for key, curve in self.curves.items():
            if not curve.isVisible():
                continue
            y = ydata[key]
            x = range(len(y))
            curve.setData(x, y)
        self.plotWidget.replot()

    def on_controlTree_doubleClicked(self, index):
        """ Signal handler for controls tree double click.

        @param index QModelIndex instance
        @return None
        """
        parent = index.parent()
        key = index.row(), index.column()
        model = self.controlTree.model()
        if parent.isValid():
            parentkey = (parent.row(), parent.column())
            parentitem = model.item(*parentkey)
            item = parentitem.child(*key)
            key = parentkey + key
            names = (parentitem.text(), item.text(), )
        else:
            item = model.item(*key)
            names = (item.text(), )
        try:
            itemcolor = self.colors[key]
        except (AttributeError, ):
            pass
        else:
            color = QColorDialog.getColor(itemcolor, self)
            if color.isValid():
                self.colors[key] = color
                item.setIcon(colorIcon(color))
                self.saveCurveColor(color, *names)
                try:
                    curve = self.curves[key]
                except (KeyError, ):
                    pass
                else:
                    curve.setPen(QPen(color))
                    if curve.isVisible:
                        self.plotWidget.replot()

    def on_controlTree_itemChanged(self, item):
        """ Signal handler for all changes to control tree items.

        @param item changed tree widget item
        @return None
        """
        self.enableCurve(item, enable=item.checkState()==Qt.Checked)
