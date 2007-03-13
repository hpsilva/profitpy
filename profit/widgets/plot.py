#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

##
#
# This module defines the Plot class for display of plots and plotting
# controls.
#
##

from PyQt4.QtCore import QByteArray, QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QBrush, QColor, QColorDialog, QFont, QFontDialog
from PyQt4.QtGui import QStandardItem, QStandardItemModel, QMenu, QPen, QFrame
from PyQt4.Qwt5 import QwtLegend, QwtPicker, QwtPlot, QwtPlotCurve
from PyQt4.Qwt5 import QwtPlotGrid, QwtPlotPicker, QwtPlotZoomer, QwtPainter

from ib.ext.TickType import TickType

from profit.lib.core import Settings, Signals
from profit.lib.gui import colorIcon, complementColor
from profit.widgets.plotitemdialog import PlotItemDialog
from profit.widgets.ui_plot import Ui_Plot


allAxes = (QwtPlot.xBottom, QwtPlot.xTop, QwtPlot.yRight, QwtPlot.yLeft)


def changePen(getr, setr, parent):
    """ Allow the user to change a pen with a PlotItemDialog.

    @param getr callable that returns current pen
    @param setr callable to set selected pen if dialog is accepted
    @param parent ancestor of dialog
    @return new pen if dialog is accepted, otherwise None
    """
    oldpen = getr()
    dlg = PlotItemDialog(oldpen, parent)
    if dlg.exec_() == dlg.Accepted:
        newpen = QPen(dlg.selectedPen)
        setr(newpen)
        return newpen


def changeColor(getr, setr, parent):
    """ Allow the user to change a color with a QColorDialog.

    @param getr callable that returns current color
    @param setr callable to set selected color if dialog is accepted
    @param parent ancestor of dialog
    @return new color if dialog is accepted, otherwise None
    """
    oldcolor = QColor(getr())
    newcolor = QColorDialog.getColor(oldcolor, parent)
    if newcolor.isValid():
        setr(newcolor)
        return newcolor


def defaultCanvasColor():
    """ Reasonable default for canvas color.

    @return QColor instance
    """
    return QColor(240, 240, 240)


def defaultMajorGridPen():
    """ Reasonable default for major grid pen.

    @return QPen instance
    """
    pen = QPen(QColor(170, 170, 170))
    pen.setStyle(Qt.DashLine)
    return pen


def defaultMinorGridPen():
    """ Reasonable default for minor grid pen.

    @return QPen instance
    """
    pen = QPen(QColor(210, 210, 210))
    pen.setStyle(Qt.DotLine)
    return pen


def defaultSplitterState():
    """ Resonable default for plot splitter state.

    @return QByteArray suitable for use with QSplitter.restoreState
    """
    return QByteArray.fromBase64('AAAA/wAAAAAAAAACAAAAiQAAAm8BAAAABgEAAAAB')


class PlotCurve(QwtPlotCurve):
    """ Specialized plot curve.

    """
    settingsLoaded = False

    def updateLegend(self, legend, enable=False):
        """ Framework hook to update plot legend with this curve.

        @param legend QwtLegend instance
        @param enable=False must be true to include this curve in legend
        @return None
        """
        if self.isVisible() and enable:
            QwtPlotCurve.updateLegend(self, legend)


class PlotGrid(QwtPlotGrid):
    """ Specalized plot grid.

    QwtPlotGrid instances will not draw their minor grids if the major
    grid is also not enabled.  This class reimplements 'draw' and
    'drawLines' to overcome this limitation.  Code for both was taken
    from the Qwt sources.
    """
    def __init__(self):
        """ Constructor.

        """
        QwtPlotGrid.__init__(self)
        self.enableX(False)
        self.enableY(False)
        self.enableXMin(False)
        self.enableYMin(False)

    def draw(self, painter, mx, my, rect):
        """ Draws minor and major grids.

        @param painter QPainter instance
        @param mx QwtScaleMap instance
        @param my QwtScaleMap instance
        @param rect QRect instance
        @return None
        """
        painter.setPen(self.minPen())
        sdx = self.xScaleDiv()
        sdy = self.yScaleDiv()
        if self.xMinEnabled():
            self.drawLines(
                painter, rect, Qt.Vertical, mx, sdx.ticks(sdx.MinorTick))
            self.drawLines(
                painter, rect, Qt.Vertical, mx, sdx.ticks(sdx.MediumTick))
        if self.yMinEnabled():
            self.drawLines(
                painter, rect, Qt.Horizontal, my, sdy.ticks(sdy.MinorTick))
            self.drawLines(
                painter, rect, Qt.Horizontal, my, sdy.ticks(sdy.MediumTick))
        painter.setPen(self.majPen())
        if self.xEnabled():
            self.drawLines(
                painter, rect, Qt.Vertical, mx, sdx.ticks(sdx.MajorTick))
        if self.yEnabled():
            self.drawLines(
                painter, rect, Qt.Horizontal, my, sdy.ticks(sdy.MajorTick))

    def drawLines(self, painter, rect, orientation, scalemap, values):
        """ Draws specified lines.

        @param painter QPainter instance
        @param rect QRect instance
        @param orientation Qt.Horizontal or Qt.Vertical
        @param scalemap QwtScaleMap instance
        @param values list of x or y values for line drawing
        @return None
        """
        x1 = rect.left()
        x2 = rect.right()
        y1 = rect.top()
        y2 = rect.bottom()
        for v in values:
            value = scalemap.transform(v)
            if orientation == Qt.Horizontal:
                if ((value >= y1) and (value <= y2)):
                    QwtPainter.drawLine(painter, x1, value, x2, value)
            else:
                if ((value >= x1) and (value <= x2)):
                    QwtPainter.drawLine(painter, value, y1, value, y2)


class PlotZoomer(QwtPlotZoomer):
    """ Stub for future implementation.

    """


class PlotPicker(QwtPlotPicker):
    """ Stub for future implementation.

    """


class Picker(QwtPicker):
    """ Stub for future implementation.

    """


class Legend(QwtLegend):
    """ Stub for future implementation.

    """


class ControlTreeItem(QStandardItem):
    """ Self-configuring control tree item.

    """
    def __init__(self, text, data):
        """ Constructor.

        @param text value for this item
        @param data reference to data series for this item
        """
        QStandardItem.__init__(self, text)
        self.setCheckable(True)
        self.setCheckState(Qt.Unchecked)
        self.setEditable(False)
        self.curve = PlotCurve(text)
        self.data = data

    def isChecked(self):
        """ True if this item is checked.

        """
        return self.checkState() == Qt.Checked

    def name(self):
        """ Name of item including parent names if any.

        """
        names = []
        while self:
            names.append(str(self.text()))
            self = self.parent()
        return str.join('/', reversed(names))

    def setColor(self, color):
        """ Sets the icon and color for this item.

        @param color QColor instance
        @return None
        """
        self.setIcon(colorIcon(color))


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

    def setupOptionsMenu(self):
        """ Configure the options button menu.

        @return None
        """
        optionsButton = self.optionsButton
        pop = QMenu(optionsButton)
        optionsButton.setMenu(pop)
        pop.addAction(self.actionDrawMajorX)
        pop.addAction(self.actionDrawMajorY)
        pop.addSeparator()
        pop.addAction(self.actionDrawMinorX)
        pop.addAction(self.actionDrawMinorY)
        pop.addSeparator()
        pop.addAction(self.actionDrawLegend)
        pop.addSeparator()
        pop.addAction(self.actionChangeCanvasColor)
        pop.addAction(self.actionChangeMajorGridStyle)
        pop.addAction(self.actionChangeMinorGridStyle)

    def setupPlot(self):
        """ Configure the plot widget.

        @return None
        """
        plot = self.plot
        plot.setFrameStyle(plot.NoFrame|plot.Plain)
        self.enableAutoScale()
        canvas = plot.canvas()
        canvas.setFrameStyle(plot.NoFrame|plot.Plain)
        layout = plot.plotLayout()
        layout.setCanvasMargin(0)
        layout.setAlignCanvasToScales(True)
        self.grid = PlotGrid()
        self.grid.attach(plot)
        plot.insertLegend(Legend(), plot.LeftLegend)
        self.actionDrawLegend.setChecked(False)
        self.actionDrawLegend.setEnabled(False)
        self.zoomer = PlotZoomer(
            QwtPlot.xBottom, QwtPlot.yRight, Picker.DragSelection,
            Picker.AlwaysOff, canvas)
        self.picker = PlotPicker(
            QwtPlot.xBottom, QwtPlot.yRight, Picker.NoSelection,
            QwtPlotPicker.CrossRubberBand, Picker.AlwaysOn, canvas)
        pen = QPen(Qt.black)
        self.zoomer.setRubberBandPen(pen)
        self.picker.setTrackerPen(pen)

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
        settings = self.settings
        name = self.plotName()
        statekey = '%s/%s' % (name, settings.keys.splitstate)
        state = settings.value(statekey, defaultSplitterState())
        self.plotSplitter.restoreState(state.toByteArray())
        self.setupTree()
        self.loadSelections()
        self.loadGrids()
        self.loadCanvasColor()
        self.loadLegend()
        self.updateAxis()
        axisactions = [self.actionChangeAxesFont, self.actionChangeAxesColor]
        for widget in self.axisWidgets():
            widget.addActions(axisactions)
            widget.setContextMenuPolicy(Qt.ActionsContextMenu)
        color = settings.value('%s/axiscolor' % name)
        if color.isValid():
            self.setAxisColor(QColor(color))
        font = settings.value('%s/axisfont' % name)
        if font.isValid():
            self.setAxisFont(QFont(font))
        self.plot.replot()
        session.registerMeta(self)

    def setupTree(self):
        """ Configure the model and initial items for this instance.

        @return None
        """
        ticker = self.tickerCollection[self.tickerId]
        tree = self.controlsTree
        tree.header().hide()
        self.controlsTreeModel = model = QStandardItemModel(self)
        tree.setModel(model)
        tree.sortByColumn(0, Qt.AscendingOrder)
        for field, series in ticker.series.items():
            self.addSeries(TickType.getField(field), series)
        self.connect(model, Signals.standardItemChanged,
                     self.on_controlsTree_itemChanged)
        for col in range(model.columnCount()):
            tree.resizeColumnToContents(col)
        tree.addActions(
            [self.actionChangeCurveStyle, self.actionChangeCurveAxis])

    def addSeries(self, name, series, parent=None):
        """ Creates new controls and curve for an individual series.

        @param name series key
        @return None
        """
        if parent is None:
            parent = self.controlsTreeModel.invisibleRootItem()
        item = ControlTreeItem(name, series)
        item.curve.setYAxis(QwtPlot.yRight)
        item.curve.setVisible(False)
        item.setColor(self.loadItemPen(item).color())
        parent.appendRow(item)
        self.controlsTreeItems.append(item)
        for index in getattr(series, 'indexes', []):
            self.addSeries(index.key, index, parent=item)

    def anyCheckedItems(self):
        """ True if any control is checked.

        """
        return bool(self.checkedItems)

    def axisWidgets(self):
        """ Yields each plot axis widget.

        """
        for axis in allAxes:
            yield self.plot.axisWidget(axis)

    def checkedItems(self):
        """ Sequence of checked controls.

        """
        return [item for item in self.controlsTreeItems if item.isChecked()]

    def checkedNames(self):
        """ Sequence of checked control names.

        """
        return [self.itemName(item) for item in self.checkedItems()]

    def checkZoom(self, rect):
        """ Sets autoscaling mode when plot is zoomed to its base.

        @param rect ignored
        @return None
        """
        if not self.zoomer.zoomRectIndex():
            self.enableAutoScale()

    def enableAutoScale(self):
        """ Sets autoscaling mode on all four axes.

        @return None
        """
        for axis in allAxes:
            self.plot.setAxisAutoScale(axis)

    def enableCurve(self, item, enable=True):
        """ Sets the visibility and style of a plot curve.

        @param item tree widget item
        @param enabled sets curve visible if True, otherwise invisible
        @return None
        """
        curve = item.curve
        plot = self.plot
        legend = plot.legend()
        if enable:
            if not curve.settingsLoaded:
                self.loadCurve(self.itemName(item), curve)
            curve.setData(item.data.x, item.data.y)
            curve.setVisible(True)
            curve.attach(plot)
            self.enableAutoScale()
        else:
            legend.remove(curve)
            curve.detach()
            curve.setVisible(False)
        checked = self.anyCheckedItems()
        self.actionDrawLegend.setEnabled(checked)
        if not checked:
            legend.clear()
            legend.hide()
            self.actionDrawLegend.setChecked(False)
        plot.updateAxes()
        self.zoomer.setZoomBase()
        self.connect(self.zoomer, Signals.zoomed, self.checkZoom)
        plot.replot()

    def getAxisColor(self):
        """ Returns the foreground color of the axis widgets.

        @return QColor instance
        """
        widget = self.referenceAxisWidget()
        palette = widget.palette()
        return palette.color(palette.WindowText)

    def itemName(self, item):
        """ Name for given item, including name of this plot.

        @param item ControlTreeItem instance
        @return name full item name including plot name
        """
        return '%s/%s' % (self.plotName(), item.name())

    def loadCanvasColor(self):
        """ Reads and sets the canvas color from saved settings.

        @return None
        """
        color = self.settings.value(
            '%s/canvascolor' % self.plotName(), defaultCanvasColor())
        self.plot.setCanvasBackground(QColor(color))

    def loadCurve(self, name, curve):
        """ Reads and configures a plot curve.

        @param name of curve
        @param curve QwtPlotCurve instance
        @return None
        """
        getv = self.settings.value
        curve.setBrush(QBrush(getv('%s/brush' % name, QBrush())))
        curve.setPen(QPen(getv('%s/pen' % name, QPen())))
        curve.setStyle(curve.CurveStyle(
            getv('%s/style' % name, QVariant(curve.Lines)).toInt()[0]))
        curve.setBaseline(
            getv('%s/baseline' % name, QVariant(0.0)).toDouble()[0])
        curve.setCurveAttribute(
            curve.Inverted, getv('%s/inverted' % name).toBool())
        curve.setCurveAttribute(
            curve.Fitted, getv('%s/fitted' % name).toBool())
        curve.setPaintAttribute(
            curve.PaintFiltered, getv('%s/filtered' % name).toBool())
        curve.setPaintAttribute(
            curve.ClipPolygons, getv('%s/clippoly' % name).toBool())
        curve.setYAxis(
            QwtPlot.Axis(getv('%s/yaxis' % name, QwtPlot.yRight).toInt()[0]))
        name = '%s/symbol' % name
        symbol = curve.symbol()
        symbol.setBrush(QBrush(getv('%s/brush' % name, QBrush())))
        symbol.setPen(QPen(getv('%s/pen' % name, QPen())))
        symbol.setStyle(
            symbol.Style(getv('%s/style' % name,
                              QVariant(symbol.NoSymbol)).toInt()[0]))
        symbol.setSize(getv('%s/size' % name).toSize())
        curve.settingsLoaded = True

    def loadGrids(self):
        """ Reads and sets the major and minor grid pens and visibility.

        @return None
        """
        name = self.plotName()
        grid = self.grid
        getv = self.settings.value
        pen = getv('%s/major/pen' % name, defaultMajorGridPen())
        grid.setMajPen(QPen(pen))
        pen = getv('%s/minor/pen' % name, defaultMinorGridPen())
        grid.setMinPen(QPen(pen))
        items = [('%s/major/x/enabled', self.actionDrawMajorX),
                 ('%s/major/y/enabled', self.actionDrawMajorY),
                 ('%s/minor/x/enabled', self.actionDrawMinorX),
                 ('%s/minor/y/enabled', self.actionDrawMinorY)]
        for key, action in items:
            v = getv(key % name)
            if not v.isValid() or v.toBool():
                action.trigger()

    def loadItemPen(self, item):
        """ Creates a pen from saved settings.

        @param item ControlTreeItem instance
        @return QPen instance
        """
        pen = self.settings.value('%s/pen' % self.itemName(item))
        if pen.isValid():
            pen = QPen(pen)
        else:
            pen = QPen() # lookup
        return pen

    def loadLegend(self):
        """ Restores the plot legend visibility from saved settings.

        @return None
        """
        key = '%s/legend/enabled' % self.plotName()
        if self.settings.value(key).toBool():
            self.actionDrawLegend.trigger()

    def loadSelections(self):
        """ Restores the control tree items state from saved settings.

        @return None
        """
        key = '%s/checkeditems' % self.plotName()
        names = self.settings.value(key).toStringList()
        names = [str(name) for name in names]
        for item in self.controlsTreeItems:
            if self.itemName(item) in names:
                item.setCheckState(Qt.Checked)

    def plotName(self):
        """ The name of this plot.

        """
        return '%s/%s' % (self.tickerId, self.objectName())

    def referenceAxisWidget(self):
        """ Returns a referece axis widget.

        """
        return self.plot.axisWidget(QwtPlot.xBottom)

    def saveCanvasColor(self):
        """ Saves the canvas background color to user settings.

        @return None
        """
        prefix = self.plotName()
        self.settings.setValue(
            '%s/canvascolor' % prefix, self.plot.canvasBackground())

    def saveCurve(self, name, curve):
        """ Saves visual settings of a curve.

        @param name curve name, used as settings key
        @param curve QwtPlotCurve instance
        @return None
        """
        setv = self.settings.setValue
        setv('%s/brush' % name, curve.brush())
        setv('%s/pen' % name, curve.pen())
        setv('%s/style' % name, curve.style())
        setv('%s/baseline' % name, curve.baseline())
        setv('%s/inverted' % name,
                 curve.testCurveAttribute(curve.Inverted))
        setv('%s/fitted' % name,
                 curve.testCurveAttribute(curve.Fitted))
        setv('%s/filtered' % name,
                 curve.testPaintAttribute(curve.PaintFiltered))
        setv('%s/clippoly' % name,
                 curve.testPaintAttribute(curve.ClipPolygons))
        setv('%s/yaxis' % name, curve.yAxis())
        name = '%s/symbol' % name
        symbol = curve.symbol()
        setv('%s/brush' % name, symbol.brush())
        setv('%s/pen' % name, symbol.pen())
        setv('%s/style' % name, symbol.style())
        setv('%s/size' % name, symbol.size())

    def saveLegend(self):
        """ Saves the visibility of the plot legend to user settings.

        @return None
        """
        key = '%s/legend/enabled' % self.plotName()
        self.settings.setValue(key, self.actionDrawLegend.isChecked())

    def saveMajorX(self):
        """ Saves the state and pen of the major grid x axis.

        @return None
        """
        name = self.plotName()
        setv = self.settings.setValue
        setv('%s/major/x/enabled' % name,
             self.actionDrawMajorX.isChecked())
        setv('%s/major/pen' % name, self.grid.majPen())

    def saveMajorY(self):
        """ Saves the state and pen of the major grid y axis.

        @return None
        """
        name = self.plotName()
        setv = self.settings.setValue
        setv('%s/major/y/enabled' % name,
             self.actionDrawMajorY.isChecked())
        setv('%s/major/pen' % name, self.grid.majPen())

    def saveMinorX(self):
        """ Saves the state and pen of the minor grid x axis.

        @return None
        """
        name = self.plotName()
        setv = self.settings.setValue
        setv('%s/minor/x/enabled' % name,
             self.actionDrawMinorX.isChecked())
        setv('%s/minor/pen' % name, self.grid.minPen())

    def saveMinorY(self):
        """ Saves the state and pen of the minor grid y axis.

        @return None
        """
        name = self.plotName()
        setv = self.settings.setValue
        setv('%s/minor/y/enabled' % name,
             self.actionDrawMinorY.isChecked())
        setv('%s/minor/pen' % name, self.grid.minPen())

    def saveSelections(self):
        """ Saves the selected control item names.

        @return None
        """
        key = '%s/checkeditems' % self.plotName()
        self.settings.setValue(key, self.checkedNames())

    def setAxisColor(self, color):
        """ Sets the axis widgets foreground and text color.

        @param color QColor instance
        @return None
        """
        for widget in self.axisWidgets():
            palette = widget.palette()
            palette.setColor(palette.WindowText, color)
            palette.setColor(palette.Text, color)
            widget.setPalette(palette)

    def setAxisFont(self, font):
        """ Sets the axis widgets font.

        @param font QFont instance
        @return None
        """
        for widget in self.axisWidgets():
            widget.setFont(font)

    def updateAxis(self):
        """ Enables each y axis if there are curves attached to it.

        @return None
        """
        items = self.checkedItems()
        rights = any(i for i in items if i.curve.yAxis()==QwtPlot.yRight)
        lefts = any(i for i in items if i.curve.yAxis()==QwtPlot.yLeft)
        self.plot.enableAxis(QwtPlot.yRight, rights)
        self.plot.enableAxis(QwtPlot.yLeft, lefts)
        if not rights and not lefts:
            self.plot.enableAxis(QwtPlot.yRight, True)

    ## session signal handlers

    def on_session_createdSeries(self, tickerId, field):
        """ Signal handler called when new Series objects are created.

        @param tickerId id of ticker with new series
        @param field series field
        """
        if tickerId != self.tickerId:
            return
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
        items = [i for i in self.controlsTreeItems if i.curve.isVisible()]
        for item in items:
            item.curve.setData(item.data.x, item.data.y)
        if items:
            self.plot.replot()

    ## action signal handlers

    @pyqtSignature('')
    def on_actionChangeCurveStyle_triggered(self):
        """ Signal handler called to edit a curve.

        @return None
        """
        pos = self.sender().data().toPoint()
        index = self.controlsTree.indexAt(pos)
        if index.isValid():
            item = self.controlsTreeModel.itemFromIndex(index)
            curve = item.curve
            if not curve.settingsLoaded:
                self.loadCurve(self.itemName(item), curve)
            cplot = curve.plot()
            if cplot is None:
                curve.attach(self.plot)
            dlg = PlotItemDialog(curve, self)
            if dlg.exec_() == dlg.Accepted:
                dlg.applyToCurve(curve)
                item.setColor(curve.pen().color())
                self.saveCurve(self.itemName(item), curve)
                self.enableCurve(item, enable=item.checkState()==Qt.Checked)
            if cplot is None:
                curve.detach()

    @pyqtSignature('')
    def on_actionChangeCurveAxis_triggered(self):
        """ Signal handler called to toggle the y axis of a curve.

        @return None
        """
        pos = self.sender().data().toPoint()
        index = self.controlsTree.indexAt(pos)
        if index.isValid():
            item = self.controlsTreeModel.itemFromIndex(index)
            curve = item.curve
            if curve.yAxis() == QwtPlot.yLeft:
                curve.setYAxis(QwtPlot.yRight)
            else:
                curve.setYAxis(QwtPlot.yLeft)
            self.updateAxis()
            self.saveCurve(self.itemName(item), curve)
            self.plot.replot()

    @pyqtSignature('bool')
    def on_actionDrawLegend_triggered(self, enable):
        """ Signal handler called to toggle the plot legend visibility.

        @param enable if True, legend is enabled
        @return False
        """
        legend = self.plot.legend()
        legend.setVisible(enable)
        if enable:
            items = self.checkedItems()
            if items:
                for item in items:
                    item.curve.updateLegend(legend, True)
            else:
                self.actionDrawLegend.setChecked(False)
        else:
            legend.clear()
        self.saveLegend()

    @pyqtSignature('bool')
    def on_actionDrawMajorX_triggered(self, enable):
        """ Signal handler called to toggle visiblity of major grid x axis.

        @param enable if True, grid axis is enabled
        @return None
        """
        self.grid.enableX(enable)
        self.plot.replot()
        self.saveMajorX()

    @pyqtSignature('bool')
    def on_actionDrawMajorY_triggered(self, enable):
        """ Signal handler called to toggle visiblity of major grid y axis.

        @param enable if True, grid axis is enabled
        @return None
        """
        self.grid.enableY(enable)
        self.plot.replot()
        self.saveMajorY()

    @pyqtSignature('bool')
    def on_actionDrawMinorX_triggered(self, enable):
        """ Signal handler called to toggle visiblity of minor grid x axis.

        @param enable if True, grid axis is enabled
        @return None
        """
        self.grid.enableXMin(enable)
        self.plot.replot()
        self.saveMinorX()

    @pyqtSignature('bool')
    def on_actionDrawMinorY_triggered(self, enable):
        """ Signal handler called to toggle visiblity of minor grid y axis.

        @param enable if True, grid axis is enabled
        @return None
        """
        self.grid.enableYMin(enable)
        self.plot.replot()
        self.saveMinorY()

    @pyqtSignature('')
    def on_actionChangeMajorGridStyle_triggered(self):
        """ Signal handler called to edit the major grid pen.

        @return None
        """
        pen = changePen(self.grid.majPen, self.grid.setMajPen, self)
        if pen:
            self.plot.replot()
            self.saveMajorX()
            self.saveMajorY()

    @pyqtSignature('')
    def on_actionChangeMinorGridStyle_triggered(self):
        """ Signal handler called to edit the minor grid pen.

        @return None
        """
        pen = changePen(self.grid.minPen, self.grid.setMinPen, self)
        if pen:
            self.plot.replot()
            self.saveMinorX()
            self.saveMinorY()

    @pyqtSignature('')
    def on_actionChangeCanvasColor_triggered(self):
        """ Signal handler called to edit the plot canvas background.

        @return None
        """
        plot = self.plot
        color = changeColor(
            plot.canvasBackground, plot.setCanvasBackground, self)
        if color:
            pen = QPen(complementColor(color))
            self.zoomer.setRubberBandPen(pen)
            self.picker.setTrackerPen(pen)
            plot.replot()
            self.saveCanvasColor()

    @pyqtSignature('')
    def on_actionChangeAxesFont_triggered(self):
        """ Signal handler called to edit the axes font.

        @return None
        """
        widget = self.referenceAxisWidget()
        default = widget.font()
        font, okay = QFontDialog.getFont(default, self, 'Select Axis Font')
        if okay:
            self.setAxisFont(font)
            self.settings.setValue(
                '%s/axisfont' % self.plotName(), font)

    @pyqtSignature('')
    def on_actionChangeAxesColor_triggered(self):
        """ Signal handler called to edit the axes color.

        """
        color = changeColor(self.getAxisColor, self.setAxisColor, self)
        if color:
            self.settings.setValue('%s/axiscolor' % self.plotName(), color)

    ## controls tree signal handlers

    def on_controlsTree_doubleClicked(self, index):
        """ Signal handler for control tree double click.

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
        self.updateAxis()
        self.saveSelections()

    def on_controlsTree_customContextMenuRequested(self, pos):
        """ Signal handler for context menu request over control tree.

        @param pos QPoint of mouse click
        @return None
        """
        tree = self.controlsTree
        index = tree.indexAt(pos)
        if index.isValid():
            item = self.controlsTreeModel.itemFromIndex(index)
            if item.curve.yAxis() == QwtPlot.yRight:
                self.actionChangeCurveAxis.setText('Move to Left Axis')
            else:
                self.actionChangeCurveAxis.setText('Move to Right Axis')
            actions = tree.actions()
            for action in actions:
                action.setData(QVariant(pos))
            QMenu.exec_(actions, tree.mapToGlobal(pos))

    def on_plotSplitter_splitterMoved(self, pos, index):
        """ Signal handler for splitter move; saves state to user settings.

        @param pos ignored
        @param index ignored
        @return None
        """
        settings = self.settings
        statekey = '%s/%s' % (self.plotName(), settings.keys.splitstate)
        settings.setValue(statekey, self.plotSplitter.saveState())
