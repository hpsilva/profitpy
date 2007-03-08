#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import (QColor, QColorDialog, QFrame, QPen, QInputDialog,
                         QStandardItem, QStandardItemModel, QMenu, )
from PyQt4.Qwt5 import (QwtPicker, QwtPlot, QwtPlotCurve,
                        QwtPlotPicker, QwtPlotZoomer, QwtPlotGrid,
                        QwtLegend,
                        )

from ib.ext.TickType import TickType

from profit.lib.core import Settings, Signals
from profit.lib.gui import colorIcon
from profit.widgets.ui_plot import Ui_Plot


"""
set fill brush
style:  Lines, Sticks, Steps, Dots
toggle legend
"""


class PlotCurve(QwtPlotCurve):
    """ Stub for future implementation.

    """


class PlotPicker(QwtPlotPicker):
    """ Stub for future implementation.

    """


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


def complementColor(c):
    hx = str(c.name())[1:]
    comp = ['%.2X' % (255 - int(a, 16)) for a in (hx[0:2], hx[2:4], hx[4:6])]
    return QColor('#' + str.join('', comp))


def changeColor(self, getr, setr):
    oldcolor = getr()
    newcolor = QColorDialog.getColor(oldcolor, self)
    if newcolor.isValid():
        setr(newcolor)
        self.plot.replot()


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
        self.data = {}
        self.session = None
        self.tickerId = None
        self.settings = Settings()
        self.settings.beginGroup(self.settings.keys.plots)
        self.setupOptionsMenu()
        self.setupPlot()
        self.setupZoomer()
        self.controlTree.addActions([
            self.actionLineColor,
            self.actionLineStyle,
            ])

    def on_controlTree_customContextMenuRequested(self, pos):
        tree = self.controlTree
        index = tree.indexAt(pos)
        if index.isValid():
            item = self.dataModel.itemFromIndex(index)
            actions = tree.actions()
            for action in actions:
                action.setData(QVariant(pos))
            QMenu.exec_(actions, tree.mapToGlobal(pos))

    @pyqtSignature('')
    def on_actionLineStyle_triggered(self):
        pos = self.actionLineStyle.data().toPoint()
        index = self.controlTree.indexAt(pos)
        if index.isValid():
            value, okay = QInputDialog.getItem(
                self, 'Select Line Style',
                'Line Style:',
                ['Line', 'Step', 'Dot', ],
                0, # current
                False, # editable
            )
            print str(value), okay

    @pyqtSignature('')
    def on_actionLineColor_triggered(self):
        pos = self.actionLineColor.data().toPoint()
        index = self.controlTree.indexAt(pos)
        if index.isValid():
            self.on_controlTree_doubleClicked(index)

    def setupOptionsMenu(self):
        optionsButton = self.optionsButton
        pop = QMenu(optionsButton)
        optionsButton.setMenu(pop)
        pop.addAction(self.actionMajorEnable)
        pop.addAction(self.actionMinorEnable)
        pop.addAction(self.actionLegendEnable)
        pop.addSeparator()
        pop.addAction(self.actionCanvasColor)
        pop.addAction(self.actionMajorColor)
        pop.addAction(self.actionMinorColor)

    def setupPlot(self):
        plot = self.plot
        plot.setFrameStyle(plot.NoFrame|plot.Plain)
        self.plotSplitter.setSizes([80, 300])
        self.grid = grid = QwtPlotGrid()
        grid.attach(plot)
        self.legend = QwtLegend(plot)
        self.legend.setVisible(False)
        self.actionLegendEnable.setChecked(False)

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
    def on_actionMajorColor_triggered(self):
        grid = self.grid
        changeColor(self, grid.majPen().color, grid.setMajPen)

    @pyqtSignature('')
    def on_actionMinorColor_triggered(self):
        grid = self.grid
        changeColor(self, grid.minPen().color, grid.setMinPen)

    @pyqtSignature('')
    def on_actionCanvasColor_triggered(self):
        plot = self.plot
        changeColor(self, plot.canvasBackground, plot.setCanvasBackground)
        bg = plot.canvasBackground()
        bg = complementColor(bg)
        pen = QPen(bg)
        self.zoomer.setRubberBandPen(pen)
        self.picker.setTrackerPen(pen)

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

    def setupZoomer(self):
        """ Configures the zoomer and picker objects for this instance.

        @return None
        """
        plot = self.plot
        plot.enableAxis(QwtPlot.yRight, True)
        plot.enableAxis(QwtPlot.yLeft, False)
        canvas = plot.canvas()
        layout = plot.plotLayout()
        layout.setCanvasMargin(0)
        layout.setAlignCanvasToScales(True)
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

    def addCurve(self, key, color, data):
        """ Creates a new, empty plot curve for the given key.

        @param key curve key
        @param color QColor instance associated with curve
        @param data sequence associated with curve
        @return None
        """
        self.curves[key] = curve = PlotCurve()
        curve.setStyle(PlotCurve.Lines)
        self.colors[key] = color
        self.data[key] = data

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
            color = self.curveColor(name, index.key)
            icon = colorIcon(color)
            subitem = ControlTreeItem(index.key, icon)
            item.appendRow(subitem)
            subrowcol = rowcol + (subitem.row(), subitem.column())
            self.addCurve(subrowcol, color, index)


    def curveColor(self, *names):
        """ Loads color for named curve.

        @param *names one or more strings to form settings key
        @return QColor instance
        """
        names = tuple([str(name) for name in names])
        settings = self.settings
        key = '%s:%s' % (self.tickerId, str.join(':', names))
        default = self.defaultCurveColor(*names)
        #print '### ', names, default
        value = settings.value(key, default)
        return QColor(value)



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

    def saveCurveColor(self, color, *names):
        """ Saves named curve color setting.

        @param color QColor instance
        @param *names one or more strings to form settings key
        @return None
        """
        names = [str(name) for name in names]
        settings = self.settings
        key = '%s:%s' % (self.tickerId, str.join(':', names))
        settings.setValue(key, color)

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
            plot = self.plot
            if enable:
                curve.setData(self.data[key].x, self.data[key].y)
                curve.setPen(QPen(self.colors[key]))
                curve.setVisible(True)
                curve.setYAxis(QwtPlot.yRight)
                curve.attach(plot)
            else:
                curve.setVisible(False)
                curve.detach()
            plot = self.plot

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
        data = self.data
        for key, curve in self.curves.items():
            if curve.isVisible():
                curve.setData(data[key].x, data[key].y)
        self.plot.replot()

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
                        self.plot.replot()

    def on_controlTree_itemChanged(self, item):
        """ Signal handler for all changes to control tree items.

        @param item changed tree widget item
        @return None
        """
        self.enableCurve(item, enable=item.checkState()==Qt.Checked)
