#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2


from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QBrush, QColor, QColorDialog, QFrame, QPen
from PyQt4.QtGui import QStandardItem, QStandardItemModel, QMenu
from PyQt4.Qwt5 import QwtLegend, QwtPicker, QwtPlot, QwtPlotCurve
from PyQt4.Qwt5 import QwtPlotGrid, QwtPlotPicker, QwtPlotZoomer

from ib.ext.TickType import TickType

from profit.lib.core import Settings, Signals
from profit.lib.gui import colorIcon, complementColor
from profit.widgets.plotitemdialog import PlotItemDialog
from profit.widgets.ui_plot import Ui_Plot

# TODO: left/right yaxis setting
# TODO: save and restore selected items
# TODO: save and restore selected grids
# TODO: enable x-only and y-only major and minor grid axis


def changePen(parent, getr, setr):
    oldpen = getr()
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
    settingsLoaded = False

    def updateLegend(self, legend):
        if self.isVisible() and legend.isVisible():
            return QwtPlotCurve.updateLegend(self, legend)


class PlotGrid(QwtPlotGrid):
    nullPen = QPen(Qt.transparent)

    def enableX(self, enable):
        if enable:
            self.setMajPen(self.okayPen)
            QwtPlotGrid.enableX(self, True)
        else:
            self.setMajPen(self.nullPen)

    def enableY(self, enable):
        if enable:
            self.setMajPen(self.okayPen)
            QwtPlotGrid.enableX(self, True)
        else:
            self.setMajPen(self.nullPen)

    def setMajPen(self, pen):
        if pen is not self.nullPen:
            self.okayPen = pen
        QwtPlotGrid.setMajPen(self, pen)


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

    def isChecked(self):
        return self.checkState() == Qt.Checked

    @property
    def name(self):
        names = []
        while self:
            names.append(str(self.text()))
            self = self.parent()
        return str.join('/', reversed(names))


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
        self.controlsTree.addActions([self.actionChangeCurveStyle, ])

    def setupOptionsMenu(self):
        optionsButton = self.optionsButton
        pop = QMenu(optionsButton)
        optionsButton.setMenu(pop)
        pop.addAction(self.actionDrawMajorGrid)
        pop.addAction(self.actionDrawMinorGrid)
        pop.addAction(self.actionDrawLegend)
        pop.addSeparator()
        pop.addAction(self.actionChangeCanvasColor)
        pop.addAction(self.actionChangeMajorGridStyle)
        pop.addAction(self.actionChangeMinorGridStyle)

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
        self.grid = PlotGrid()
        self.grid.attach(plot)
        plot.insertLegend(QwtLegend(), plot.LeftLegend)
        self.actionDrawLegend.setChecked(False)
        self.actionDrawLegend.setEnabled(False)
        self.zoomer = QwtPlotZoomer(
            QwtPlot.xBottom, QwtPlot.yRight, QwtPicker.DragSelection,
            QwtPicker.AlwaysOff, canvas)
        self.picker = PlotPicker(
            QwtPlot.xBottom, QwtPlot.yRight, QwtPicker.NoSelection,
            QwtPlotPicker.CrossRubberBand, QwtPicker.AlwaysOn, canvas)
        pen = QPen(Qt.black)
        self.zoomer.setRubberBandPen(pen)
        self.picker.setTrackerPen(pen)

    @pyqtSignature('bool')
    def on_actionDrawLegend_triggered(self, enable):
        legend = self.plot.legend()
        legend.setVisible(enable)
        if enable:
            items = self.checkedItems()
            if items:
                legend.show()
                for item in items:
                    item.curve.updateLegend(legend)
            else:
                self.actionDrawLegend.setChecked(False)
        else:
            legend.clear()
            legend.hide()

    @pyqtSignature('bool')
    def on_actionDrawMajorGrid_triggered(self, enable):
        self.grid.enableX(enable)
        self.grid.enableY(enable)
        self.plot.replot()

    @pyqtSignature('bool')
    def on_actionDrawMinorGrid_triggered(self, enable):
        self.grid.enableXMin(enable)
        self.grid.enableYMin(enable)
        self.plot.replot()

    @pyqtSignature('')
    def on_actionChangeMajorGridStyle_triggered(self):
        if changePen(self, self.grid.majPen, self.grid.setMajPen):
            self.savePen('majorgrid/pen', self.grid.majPen())
            self.plot.replot()

    @pyqtSignature('')
    def on_actionChangeMinorGridStyle_triggered(self):
        if changePen(self, self.grid.minPen, self.grid.setMinPen):
            self.savePen('minorgrid/pen', self.grid.minPen())
            self.plot.replot()

    @pyqtSignature('')
    def on_actionChangeCanvasColor_triggered(self):
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
        grid.setMajPen(self.loadPen('majorgrid/pen', QPen(QColor('#c0c0c0'))))
        grid.setMinPen(self.loadPen('minorgrid/pen', QPen(QColor('#070707'))))
        plot.replot()

    def setupTree(self):
        """ Configure the model and initial items for this instance.

        @return None
        """
        self.controlsTreeModel = model = QStandardItemModel(self)
        ticker = self.tickerCollection[self.tickerId]
        root = model.invisibleRootItem()
        for field, series in ticker.series.items():
            self.addSeries(TickType.getField(field), series)
        self.connect(model, Signals.standardItemChanged,
                     self.on_controlsTree_itemChanged)
        tree = self.controlsTree
        tree.header().hide()
        tree.setModel(model)
        for col in range(model.columnCount()):
            tree.resizeColumnToContents(col)
        tree.sortByColumn(0, Qt.AscendingOrder)

    def addSeries(self, name, series, parent=None):
        """ Creates new controls and curve for an individual series.

        @param name series key
        @return None
        """
        if parent is None:
            parent = self.controlsTreeModel.invisibleRootItem()
        item = ControlTreeItem(name, series)
        item.curve.setYAxis(QwtPlot.yRight)
        item.curve.attach(self.plot)
        item.setPen(self.loadItemPen(item))
        parent.appendRow(item)
        self.controlsTreeItems.append(item)
        for index in getattr(series, 'indexes', []):
            self.addSeries(index.key, index, parent=item)

    def plotName(self):
        return '%s/%s' % (self.tickerId, self.objectName())

    def itemName(self, item):
        return '%s/%s' % (self.plotName(), item.name)

    def saveColor(self, name, color):
        key = '%s/%s' % (self.plotName(), name)
        self.settings.setValue(key, color)

    def loadColor(self, name, default):
        key = '%s/%s' % (self.plotName(), name)
        value = self.settings.value(key, default)
        return QColor(value)

    def savePen(self, name, pen):
        key = '%s/%s' % (self.plotName(), name)
        self.settings.setValue(key, pen)

    def loadPen(self, name, default):
        key = '%s/%s' % (self.plotName(), name)
        value = self.settings.value(key, default)
        return QPen(value)

    def saveItemPen(self, item):
        name = self.itemName(item)
        settings = self.settings
        settings.setValue('%s/pen' % name, item.pen)

    def saveItemCurve(self, item, curve):
        prefix = self.itemName(item)
        setValue = self.settings.setValue
        setValue('%s/brush' % prefix, curve.brush())
        setValue('%s/pen' % prefix, curve.pen())
        setValue('%s/style' % prefix, curve.style())
        setValue('%s/baseline' % prefix, curve.baseline())
        setValue('%s/inverted' % prefix,
                 curve.testCurveAttribute(curve.Inverted))
        setValue('%s/fitted' % prefix,
                 curve.testCurveAttribute(curve.Fitted))
        setValue('%s/filtered' % prefix,
                 curve.testPaintAttribute(curve.PaintFiltered))
        setValue('%s/clippoly' % prefix,
                 curve.testPaintAttribute(curve.ClipPolygons))
        prefix = '%s/symbol' % prefix
        symbol = curve.symbol()
        setValue('%s/brush' % prefix, symbol.brush())
        setValue('%s/pen' % prefix, symbol.pen())
        setValue('%s/style' % prefix, symbol.style())
        setValue('%s/size' % prefix, symbol.size())

    def loadItemCurve(self, item):
        prefix = self.itemName(item)
        curve = item.curve
        value = self.settings.value
        curve.setBrush(
            QBrush(value('%s/brush' % prefix, QBrush())))
        curve.setPen(
            QPen(value('%s/pen' % prefix, QPen())))
        curve.setStyle(
            curve.CurveStyle(value('%s/style' % prefix,
                                   QVariant(curve.Lines)).toInt()[0]))
        curve.setBaseline(
            value('%s/baseline' % prefix, QVariant(0.0)).toDouble()[0])
        curve.setCurveAttribute(curve.Inverted,
            value('%s/inverted' % prefix, QVariant()).toBool())
        curve.setCurveAttribute(curve.Fitted,
            value('%s/fitted' % prefix, QVariant()).toBool())
        curve.setPaintAttribute(curve.PaintFiltered,
            value('%s/filtered' % prefix, QVariant()).toBool())
        curve.setPaintAttribute(curve.ClipPolygons,
            value('%s/clippoly' % prefix, QVariant()).toBool())
        prefix = '%s/symbol' % prefix
        symbol = curve.symbol()
        symbol.setBrush(
            QBrush(value('%s/brush' % prefix, QBrush())))
        symbol.setPen(
            QPen(value('%s/pen' % prefix, QPen())))
        symbol.setStyle(
            symbol.Style(value('%s/style' % prefix,
                                   QVariant(symbol.NoSymbol)).toInt()[0]))
        symbol.setSize(
            value('%s/size' % prefix, QVariant()).toSize())
        curve.settingsLoaded = True

    def loadItemPen(self, item):
        default = QPen()
        penkey = '%s/pen' % self.itemName(item)
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

    def checkedItems(self):
        return [item for item in self.controlsTreeItems if item.isChecked()]

    def enableCurve(self, item, enable=True):
        """ Sets the visibility and style of a plot curve.

        @param item tree widget item
        @param enabled if True, curve is configured and enabled,
                       otherwise curve is set invisible
        @return None
        """
        curve = item.curve
        plot = self.plot
        legend = plot.legend()
        if enable:
            if not curve.settingsLoaded:
                self.loadItemCurve(item)
            curve.setData(item.data.x, item.data.y)
            curve.setVisible(True)
        else:
            legend.remove(curve)
            curve.setVisible(False)
        checked = self.checkedItems()
        self.actionDrawLegend.setEnabled(bool(checked))
        if not checked:
            legend.clear()
            legend.hide()
            self.actionDrawLegend.setChecked(False)
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
    def on_actionChangeCurveStyle_triggered(self):
        pos = self.sender().data().toPoint()
        index = self.controlsTree.indexAt(pos)
        if index.isValid():
            item = self.controlsTreeModel.itemFromIndex(index)
            curve = item.curve
            if not curve.settingsLoaded:
                self.loadItemCurve(item)
            dlg = PlotItemDialog(curve, self)
            if dlg.exec_() == dlg.Accepted:
                dlg.applyToCurve(curve)
                item.setPen(curve.pen())
                self.saveItemCurve(item, curve)
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
            self.actionChangeCurveStyle.trigger()

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

