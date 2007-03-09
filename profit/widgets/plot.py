#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

"""
set fill brush
style:  Lines, Sticks, Steps, Dots
toggle legend
"""

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import (QColor, QColorDialog, QFrame, QPen, QInputDialog,
                         QStandardItem, QStandardItemModel, QMenu, )
from PyQt4.Qwt5 import (QwtPicker, QwtPlot, QwtPlotCurve,
                        QwtPlotPicker, QwtPlotZoomer, QwtPlotGrid,
                        QwtLegend,
                        )

from ib.ext.TickType import TickType

from profit.lib.core import Settings, Signals
from profit.lib.gui import colorIcon, complementColor
from profit.widgets.plotitemdialog import PlotItemDialog
from profit.widgets.ui_plot import Ui_Plot


def changePen(parent, getr, setr):
    oldpen = QPen(getr())
    dlg = PlotItemDialog(oldpen, parent)
    if dlg.exec_() == dlg.Accepted:
        newpen = QPen(dlg.selectedPen)
        setr(newpen)
        return True


def changeColor(parent, getr, setr):
    oldcolor = QColor(getr())
    newcolor = QColorDialog.getColor(oldcolor, parent)
    if newcolor.isValid():
        setr(newcolor)
        return True


class PlotCurve(QwtPlotCurve):
    """ Stub for future implementation.

    """


class PlotPicker(QwtPlotPicker):
    """ Stub for future implementation.

    """


class ControlTreeItem(QStandardItem):
    """ Self-configuring control tree item.

    """
    def __init__(self, text, data):
        """ Constructor.

        """
        QStandardItem.__init__(self, text)
        self.setCheckable(True)
        self.setCheckState(Qt.Unchecked)
        self.setEditable(False)
        self.curve = PlotCurve(text)
        self.data = data
        self.pen = QPen(QColor('black'))

    def setColor(self, color):
        self.color = color
        self.setIcon(colorIcon(color))

    def setPen(self, pen):
        self.pen = pen
        self.setColor(pen.color())

    @property
    def name(self):
        names = []
        while self:
            names.append(str(self.text()))
            self = self.parent()
        return str.join(':', reversed(names))


class Plot(QFrame, Ui_Plot):
    """ Plot container.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor of this widget
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.settings = Settings()
        self.settings.beginGroup(self.settings.keys.plots)
        self.setupOptionsMenu()
        self.setupPlot()
        self.controlsTree.addActions([self.actionChangePenStyle, ])


    def setupOptionsMenu(self):
        optionsButton = self.optionsButton
        pop = QMenu(optionsButton)
        optionsButton.setMenu(pop)
        pop.addAction(self.actionMajorEnable)
        pop.addAction(self.actionMinorEnable)
        pop.addAction(self.actionLegendEnable)
        pop.addSeparator()
        pop.addAction(self.actionCanvasColor)
        pop.addAction(self.actionMajorStyle)
        pop.addAction(self.actionMinorStyle)

    def setupPlot(self):
        self.plotSplitter.setSizes([80, 300])

        plot = self.plot
        plot.setFrameStyle(plot.NoFrame|plot.Plain)
        plot.enableAxis(QwtPlot.yRight, True)
        plot.enableAxis(QwtPlot.yLeft, False)

        canvas = plot.canvas()
        canvas.setFrameStyle(plot.NoFrame|plot.Plain)

        layout = plot.plotLayout()
        layout.setCanvasMargin(0)
        layout.setAlignCanvasToScales(True)

        self.grid = grid = QwtPlotGrid()
        grid.attach(plot)

        self.legend = QwtLegend(plot)
        self.legend.setVisible(False)
        self.actionLegendEnable.setChecked(False)

        pen = QPen(Qt.black)
        self.zoomer = zoomer = \
            QwtPlotZoomer(QwtPlot.xBottom, QwtPlot.yRight,
                          QwtPicker.DragSelection,
                          QwtPicker.AlwaysOff, canvas)
        self.picker = picker = \
            PlotPicker(QwtPlot.xBottom, QwtPlot.yRight,
                          QwtPicker.NoSelection,
                          QwtPlotPicker.CrossRubberBand,
                          QwtPicker.AlwaysOn, canvas)
        zoomer.setRubberBandPen(pen)
        picker.setTrackerPen(pen)

    @pyqtSignature('bool')
    def on_actionLegendEnable_triggered(self, enable):
        self.legend.setVisible(enable)

    @pyqtSignature('bool')
    def on_actionMajorEnable_triggered(self, enable):
        grid = self.grid
        grid.enableX(enable)
        grid.enableY(enable)
        self.plot.replot()

    @pyqtSignature('bool')
    def on_actionMinorEnable_triggered(self, enable):
        grid = self.grid
        grid.enableXMin(enable)
        grid.enableYMin(enable)
        self.plot.replot()

    @pyqtSignature('')
    def on_actionMajorStyle_triggered(self):
        if changePen(self, self.grid.majPen, self.grid.setMajPen):
            self.savePen('gridmaj', self.grid.majPen())
            self.plot.replot()

    @pyqtSignature('')
    def on_actionMinorStyle_triggered(self):
        if changePen(self, self.grid.minPen, self.grid.setMinPen):
            self.savePen('gridmin', self.grid.minPen())
            self.plot.replot()

    @pyqtSignature('')
    def on_actionCanvasColor_triggered(self):
        plot = self.plot
        if changeColor(self, plot.canvasBackground, plot.setCanvasBackground):
            bg = plot.canvasBackground()
            self.saveColor('background', bg)
            pen = QPen(complementColor(bg))
            self.zoomer.setRubberBandPen(pen)
            self.picker.setTrackerPen(pen)
            plot.replot()

    def setSession(self, session, tickerId, *indexes):
        """ Associate a session with this instance.

        @param session Session instance
        @param tickerId id of ticker as integer
        @param *indexes unused
        @return None
        """
        self.controlsTreeItems = []
        self.session = session
        self.tickerCollection = session.tickerCollection
        self.tickerId = tickerId
        self.setupTree()
        session.registerMeta(self)
        plot = self.plot
        grid = self.grid
        plot.setCanvasBackground(
            self.loadColor('background', QColor('#A9A9A9')))
        grid.setMajPen(self.loadPen('gridmaj', QPen(QColor('#c0c0c0'))))
        grid.setMinPen(self.loadPen('gridmin', QPen(QColor('#070707'))))
        plot.replot()

    def setupTree(self):
        """ Configure the model and initial items for this instance.

        @return None
        """
        self.controlsTreeModel = controlsTreeModel = QStandardItemModel(self)
        ticker = self.tickerCollection[self.tickerId]
        root = controlsTreeModel.invisibleRootItem()
        for field, series in ticker.series.items():
            self.addSeries(TickType.getField(field), series)
        self.connect(controlsTreeModel, Signals.standardItemChanged,
                     self.on_controlsTree_itemChanged)
        tree = self.controlsTree
        tree.header().hide()
        model = self.controlsTreeModel
        tree.setModel(model)
        for col in range(model.columnCount()):
            tree.resizeColumnToContents(col)
        self.controlsTree.sortByColumn(0, Qt.AscendingOrder)

    def addSeries(self, name, series, parent=None):
        """ Creates new controls and curve for an individual series.

        @param name series key
        @return None
        """
        if parent is None:
            parent = self.controlsTreeModel.invisibleRootItem()
        item = ControlTreeItem(name, series)
        parent.appendRow(item)
        pen = self.loadItemPen(item)
        item.setPen(pen)
        self.controlsTreeItems.append(item)
        for index in getattr(series, 'indexes', []):
            self.addSeries(index.key, index, parent=item)

    def plotName(self):
        return '%s:%s' % (self.tickerId, self.objectName(), )

    def itemName(self, item):
        return '%s:%s' % (self.plotName(), item.name)

    def saveColor(self, name, color):
        key = '%s:%s' % (self.plotName(), name)
        self.settings.setValue(key, color)

    def loadColor(self, name, default):
        key = '%s:%s' % (self.plotName(), name)
        value = self.settings.value(key, default)
        return QColor(value)

    def savePen(self, name, pen):
        key = '%s:%s' % (self.plotName(), name)
        self.settings.setValue(key, pen)

    def loadPen(self, name, default):
        key = '%s:%s' % (self.plotName(), name)
        value = self.settings.value(key, default)
        return QPen(value)

    def saveItemPen(self, item):
        name = self.itemName(item)
        settings = self.settings
        settings.setValue('%s:pen' % name, item.pen)

    def loadItemPen(self, item):
        default = QPen()
        penkey = '%s:pen' % self.itemName(item)
        pen = self.settings.value(penkey)
        if pen.isValid():
            pen = QPen(pen)
        else:
            pen = QPen() # lookup
        return pen

    defaultCurveColors = {
        None : 'darkRed',
        ('high', ) : 'red',
        ('low', ) : 'blue',
        ('volume', ) : 'green',
        ('close', ) : 'black',
        ('bidSize', ):'blue',
        ('bidSize', 'MACD'):'black',
    }

    def defaultCurveColor(self, *names):
        try:
            return self.defaultCurveColors[names]
        except (KeyError, ):
            pass
        return self.defaultCurveColors[None]


    def enableCurve(self, item, enable=True):
        """ Sets the visibility and style of a plot curve.

        @param item tree widget item
        @param enabled if True, curve is configured and enabled,
                       otherwise curve is set invisible
        @return None
        """
        curve = item.curve
        plot = self.plot
        if enable:
            curve.setData(item.data.x, item.data.y)
            curve.setPen(item.pen)
            curve.setVisible(True)
            curve.setYAxis(QwtPlot.yRight)
            curve.attach(plot)
        else:
            curve.setVisible(False)
            curve.detach()
        plot.setAxisAutoScale(QwtPlot.xBottom)
        plot.setAxisAutoScale(QwtPlot.yRight)
        plot.updateAxes()
        self.zoomer.setZoomBase()
        plot.replot()

    def on_session_createdSeries(self, tickerId, field):
        """ Signal handler called when new Series objects are created.

        @param tickerId id of ticker with new series
        @param field series field
        """
        if tickerId != self.tickerId:
            return
        #if field not in self.tickerCollection[tickerId].series:
        #    return
        series = self.tickerCollection[self.tickerId].series[field]
        self.addSeries(TickType.getField(field), series)
        self.controlsTree.sortByColumn(0, Qt.AscendingOrder)

    def on_session_TickPrice_TickSize(self, message):
        """ Signal handler for TickPrice and TickSize session messages.

        @param message Message instance
        @return None
        """
        if message.tickerId != self.tickerId:
            return
        for i in [i for i in self.controlsTreeItems if i.curve.isVisible()]:
            i.curve.setData(i.data.x, i.data.y)
        self.plot.replot()

    @pyqtSignature('')
    def on_actionChangePenStyle_triggered(self):
        pos = self.sender().data().toPoint()
        index = self.controlsTree.indexAt(pos)
        if index.isValid():
            item = self.controlsTreeModel.itemFromIndex(index)
            dlg = PlotItemDialog(QPen(item.pen), self)
            if dlg.exec_() == dlg.Accepted:
                item.setPen(QPen(dlg.selectedPen))
                self.saveItemPen(item)
                self.enableCurve(item, enable=item.checkState()==Qt.Checked)

    def on_controlsTree_doubleClicked(self, index):
        """ Signal handler for controls tree double click.

        @param index QModelIndex instance
        @return None
        """
        tree = self.controlsTree
        if index.isValid():
            pos = tree.visualRect(index).center()
            actions = tree.actions()
            for action in actions:
                action.setData(QVariant(pos))
            self.actionChangePenStyle.trigger()

    def on_controlsTree_itemChanged(self, item):
        """ Signal handler for all changes to control tree items.

        @param item changed tree widget item
        @return None
        """
        self.enableCurve(item, enable=item.checkState()==Qt.Checked)


    def on_controlsTree_customContextMenuRequested(self, pos):
        tree = self.controlsTree
        index = tree.indexAt(pos)
        if index.isValid():
            item = self.controlsTreeModel.itemFromIndex(index)
            actions = tree.actions()
            for action in actions:
                action.setData(QVariant(pos))
            QMenu.exec_(actions, tree.mapToGlobal(pos))

