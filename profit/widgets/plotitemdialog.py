#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

##
#
# This module defines the PlotItemDialog class for edit and display
# of plot item pens and plot curves.
#
##

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QBrush, QColor, QColorDialog, QDialog, QIcon
from PyQt4.QtGui import QPainter, QPen, QPixmap
from PyQt4.Qwt5 import QwtPlot, QwtPlotCurve, QwtSymbol

from profit.lib.core import Settings
from profit.lib.gui import colorIcon, complementColor
from profit.widgets.ui_plotitemdialog import Ui_PlotItemDialog


penStyles = [
    (Qt.SolidLine, 'Solid'),
    (Qt.DashLine, 'Dash'),
    (Qt.DotLine, 'Dot'),
    (Qt.DashDotLine, 'Dash Dot'),
    (Qt.DashDotDotLine, 'Dash Dot Dot'),
]


lineStyles = [
    (QwtPlotCurve.NoCurve, 'No Line'),
    (QwtPlotCurve.Lines, 'Line'),
    (QwtPlotCurve.Sticks, 'Sticks'),
    (QwtPlotCurve.Steps, 'Steps'),
    (QwtPlotCurve.Dots, 'Dots'),
]


symbolStyles = [
    (QwtSymbol.NoSymbol, 'No Symbol'),
    (QwtSymbol.Ellipse, 'Ellipse'),
    (QwtSymbol.Rect, 'Rectangle'),
    (QwtSymbol.Diamond, 'Diamond'),
    (QwtSymbol.Triangle, 'Triangle'),
    (QwtSymbol.DTriangle, 'Triangle Down'),
    (QwtSymbol.UTriangle, 'Triangle Up'),
    (QwtSymbol.LTriangle, 'Triangle Left'),
    (QwtSymbol.RTriangle, 'Triangle Right'),
    (QwtSymbol.Cross, 'Cross'),
    (QwtSymbol.XCross, 'Cross Diagonal'),
    (QwtSymbol.HLine, 'Line Horizontal'),
    (QwtSymbol.VLine, 'Line Vertical'),
    (QwtSymbol.Star1, 'Star 1'),
    (QwtSymbol.Star2, 'Star 2'),
    (QwtSymbol.Hexagon, 'Hexagon'),
]


brushStyles = [
    (Qt.NoBrush, 'None'),
    (Qt.SolidPattern, 'Solid'),
    (Qt.Dense1Pattern, 'Extremely Dense'),
    (Qt.Dense2Pattern, 'Very Dense'),
    (Qt.Dense3Pattern, 'Somewhat Dense'),
    (Qt.Dense4Pattern, 'Half Dense'),
    (Qt.Dense5Pattern, 'Somewhat Sparse'),
    (Qt.Dense6Pattern, 'Very Sparse'),
    (Qt.Dense7Pattern, 'Extremely Sparse'),
    (Qt.HorPattern, 'Horizontal Lines'),
    (Qt.VerPattern, 'Vertical Lines'),
    (Qt.CrossPattern, 'Crossing Horizontal and Vertical Lines'),
    (Qt.BDiagPattern, 'Backward Diagonal Lines'),
    (Qt.FDiagPattern, 'Forward Diagonal Lines'),
    (Qt.DiagCrossPattern, 'Crossing Diagonal Lines'),
]


class PenStylePixmap(QPixmap):
    """ Pixmap type for creating pen style icons.

    """
    def __init__(self):
        """ Constructor.

        """
        QPixmap.__init__(self, 32, 18)
        self.fill(QColor(Qt.white))

    def paintStyle(self, painter, style):
        """ Draws an example of specified pen style.

        @param painter QPainter instance
        @param style QPen style
        @return None
        """
        painter.begin(self)
        pen = QPen(style)
        pen.setWidth(2)
        painter.setPen(pen)
        ymid = self.height() / 2
        painter.drawLine(0, ymid, self.width(), ymid)
        painter.end()


class BrushStylePixmap(QPixmap):
    """ Pixmap type for creating brush style icons.

    """
    def __init__(self):
        """ Constructor.

        """
        QPixmap.__init__(self, 32, 18)
        self.fill(QColor(Qt.black))

    def paintStyle(self, painter, style):
        """ Draws an example of specified brush style.

        @param painter QPainter instance
        @param style QBrush style
        @return None
        """
        white = QColor(Qt.white)
        brush = QBrush(style)
        brush.setColor(white)
        pen = QPen(white)
        pen.setWidth(2)
        painter.begin(self)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width(), self.height())
        painter.end()


class LineStylePixmap(QPixmap):
    """ Pixmap type for creating plot curve style icons.

    """
    def __init__(self):
        """ Constructor.

        """
        QPixmap.__init__(self, 18, 18)
        self.fill(QColor(Qt.white))

    def paintStyle(self, painter, style):
        """ Draws an example of specified curve style.

        @param painter QPainter instance; ignored
        @param style QwtCurve style
        @return None
        """
        plot = SamplePlot()
        plot.curve.setStyle(style)
        plot.resize(self.size())
        plot.replot()
        plot.print_(self)


class SymbolStylePixmap(QPixmap):
    """ Pixmap type for creating plot symbol style icons.

    """
    def __init__(self):
        """ Constructor.

        """
        QPixmap.__init__(self, 18, 18)
        self.fill(QColor(Qt.white))

    def paintStyle(self, painter, style):
        """ Draws an example of specified plot symbol style.

        @param painter QPainter instance
        @param style QwtSymbol style
        @return None
        """
        brush = QBrush(QColor(Qt.white))
        pen = QPen(QColor(Qt.black))
        size = self.size()
        symbol = QwtSymbol(style, brush, pen, size)
        painter.begin(self)
        rect = self.rect()
        rect.adjust(2, 2, -2, -2)
        symbol.draw(painter, rect)
        painter.end()


class SamplePlot(QwtPlot):
    """ Plot type with simplified appearance and builtin data.

    """
    y = [0, 1, 0.5, 1.5]
    x = range(len(y))

    def __init__(self):
        """ Constructor.

        """
        QwtPlot.__init__(self)
        self.setupPlot(self)

    @classmethod
    def setupPlot(cls, plot):
        """ Configure a plot widget.

        The Qt Designer tool doesn't provide a way to promote QwtPlot
        widgets to be promoted to custom widgets, so this class method
        is provided to operate on instances created in a ui file.

        @param plot QwtPlot instance
        @return None
        """
        plot.enableAxis(plot.yLeft, False)
        plot.enableAxis(plot.xBottom, False)
        plot.setCanvasBackground(QColor(Qt.white))
        canvas = plot.canvas()
        canvas.setFrameStyle(canvas.NoFrame)
        plot.curve = QwtPlotCurve()
        plot.curve.attach(plot)
        plot.curve.setData(cls.x, cls.y)
        pen = QPen(Qt.black)
        pen.setWidth(0)
        plot.curve.setPen(pen)


def comboCurrentData(combo, cast):
    """ Locates current item data in a combobox and returns a cast for it.

    @param combo QComboBox instance
    @param cast type cast for item data
    @return combobox current item data
    """
    data = combo.itemData(combo.currentIndex()).toInt()[0]
    return cast(data)


def fillStyleFunction(pixmapType, stylesDefault):
    """ Creates function for filling combo with style names, icons, and data.

    @param pixmapType class for rendering style icons
    @param stylesDefault default style parameter value for returned function
    @return function for populating a style combobox
    """
    def fillFunction(combo, current, styles=stylesDefault):
        """ Populates combobox with style names, icons, and data.

        @param combo QComboBox instance
        @param current style to set as current item
        @return None
        """
        painter = QPainter()
        for index, (style, name) in enumerate(styles):
            pixmap = pixmapType()
            pixmap.paintStyle(painter, style)
            combo.addItem(QIcon(pixmap), name, QVariant(style))
            if style == current:
                combo.setCurrentIndex(index)
        combo.setIconSize(pixmap.size())
    return fillFunction


##
# Function for populating a pen style combobox.
fillPenStyles = fillStyleFunction(PenStylePixmap, penStyles)


##
# Function for populating a brush style combobox.
fillBrushStyles = fillStyleFunction(BrushStylePixmap, brushStyles)


##
# Function for populating a curve line style combobox.
fillLineStyles = fillStyleFunction(LineStylePixmap, lineStyles)


##
# Function for populating a symbol style combobox.
fillSymbolStyles = fillStyleFunction(SymbolStylePixmap, symbolStyles)


class PlotItemDialog(QDialog, Ui_PlotItemDialog):
    """ Dialog for editing plot item pens and plot curves.

    This class operates in two ways.  When given a QwtCurve, it
    enables all of its selection list and widget stack.  If given a
    QPen, it enables only the first item in the selection list and the
    first widget in its widget stack.

    Clients can use the 'applyToCurve' method after the dialog is
    shown to update the curve to match the dialog.
    """
    def __init__(self, item, parent=None):
        """ Constructor.

        @param item QwtPlotCurve or QPen instance
        @param parent ancestor of this widget
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)
        if isinstance(item, QwtPlotCurve):
            self.setupFromCurve(item)
        elif isinstance(item, QPen):
            self.setupFromPen(item)
        else:
            raise TypeError('item not curve or pen')

    def setupFromPen(self, pen):
        """ Configures this dialog for only pen display and edit.

        @param pen QPen instance
        @return None
        """
        self.sectionList.item(1).setHidden(True)
        self.sectionList.item(2).setHidden(True)
        self.plotSampleGroup.setHidden(True)
        self.setupPenPage(pen)

    def setupFromCurve(self, curve):
        """ Configures this dialog for curve display and edit.

        @param curve QwtPlotCurve instance
        @return None
        """
        self.setWindowTitle('Edit Plot Curve')
        self.setupPenPage(curve.pen())
        self.setupCurvePage(curve)
        self.setupSymbolPage(curve)
        SamplePlot.setupPlot(self.plotSample)
        self.plotSample.setCanvasBackground(curve.plot().canvasBackground())
        data = curve.data()
        if data.size():
            self.plotSample.curve.setData(data)
        self.applyToCurve(self.plotSample.curve)
        self.penSampleGroup.setVisible(False)

    def applyToCurve(self, curve):
        """ Applies values in this dialog to specified curve.

        @param curve QwtPlotCurve instance
        @return None
        """
        curve.setPen(QPen(self.selectedPen))
        linestyle = comboCurrentData(self.lineStyle, curve.CurveStyle)
        curve.setStyle(linestyle)
        curve.setBaseline(self.areaFillBaseline.value())

        brush = QBrush()
        if self.areaFill.isChecked():
            style = comboCurrentData(self.areaFillStyle, Qt.BrushStyle)
            brush.setStyle(style)
            brush.setColor(self.areaFillColor.color)
        curve.setBrush(brush)

        if linestyle == QwtPlotCurve.Steps:
            curve.setCurveAttribute(curve.Inverted,
                self.curveAttributeInverted.checkState()==Qt.Checked)
        elif linestyle == QwtPlotCurve.Lines:
            curve.setCurveAttribute(curve.Fitted,
                self.curveAttributeFitted.checkState()==Qt.Checked)
        curve.setPaintAttribute(curve.PaintFiltered,
            self.paintAttributeFiltered.checkState()==Qt.Checked)
        curve.setPaintAttribute(curve.ClipPolygons,
            self.paintAttributeClipPolygons.checkState()==Qt.Checked)

        symbol = QwtSymbol()
        style = comboCurrentData(self.symbolStyle, symbol.Style)
        symbol.setStyle(style)
        if style != QwtSymbol.NoSymbol:
            symbol.setSize(
                self.symbolWidth.value(), self.symbolHeight.value())
            pen = QPen()
            pen.setStyle(comboCurrentData(self.symbolPenStyle, Qt.PenStyle))
            pen.setColor(self.symbolPenColor.color)
            pen.setWidth(self.symbolPenWidth.value())
            symbol.setPen(pen)

            brush = QBrush()
            if self.symbolFill.isChecked():
                style = comboCurrentData(self.symbolFillStyle, Qt.BrushStyle)
                brush.setStyle(style)
                brush.setColor(self.symbolFillColor.color)
            symbol.setBrush(brush)
        curve.setSymbol(symbol)

    def setupPenPage(self, pen):
        """ Configures the pen display and edit page.

        @param pen QPen instance
        @return None
        """
        self.selectedPen = QPen(pen or QPen())
        fillPenStyles(self.penStyle, pen.style())
        self.penColor.color = color = pen.color()
        self.penColor.setIcon(colorIcon(color))
        self.penWidth.setValue(pen.width())
        self.penSample.installEventFilter(self)

    def setupCurvePage(self, curve):
        """ Configures the curve display and edit page.

        @param curve QwtPlotCurve instance
        @return None
        """
        brush = curve.brush()
        current = brush.style()
        fillLineStyles(self.lineStyle, curve.style())
        fillBrushStyles(self.areaFillStyle, current)
        self.areaFill.setChecked(current != Qt.NoBrush)
        self.areaFillColor.color = color = curve.brush().color()
        self.areaFillColor.setIcon(colorIcon(color))
        self.areaFillBaseline.setValue(curve.baseline())
        self.curveAttributeInverted.setChecked(
            curve.testCurveAttribute(curve.Inverted))
        self.curveAttributeFitted.setChecked(
            curve.testCurveAttribute(curve.Fitted))
        self.paintAttributeFiltered.setChecked(
            curve.testPaintAttribute(curve.PaintFiltered))
        self.paintAttributeClipPolygons.setChecked(
            curve.testPaintAttribute(curve.ClipPolygons))

    def setupSymbolPage(self, curve):
        """ Configures the symbol display and edit page.

        @param curve QwtPlotCurve instance
        @return None
        """
        symbol = curve.symbol()
        brush = symbol.brush()
        pen = symbol.pen()
        fillSymbolStyles(self.symbolStyle, symbol.style())
        fillBrushStyles(self.symbolFillStyle, brush.style())
        self.symbolFillColor.color = color = brush.color()
        self.symbolFillColor.setIcon(colorIcon(color))
        self.symbolFill.setChecked(brush != Qt.NoBrush)
        fillPenStyles(self.symbolPenStyle, pen.style())
        self.symbolPenColor.color = color = pen.color()
        self.symbolPenColor.setIcon(colorIcon(color))
        self.symbolPenWidth.setValue(pen.width())
        size = symbol.size()
        w = size.width()
        h = size.height()
        self.symbolWidth.setValue(w)
        self.symbolHeight.setValue(h)
        self.symbolSyncSize.setChecked(w==h)
        havesymbol = symbol.style() != QwtSymbol.NoSymbol
        self.symbolFill.setEnabled(havesymbol)
        self.symbolSizeGroup.setEnabled(havesymbol)
        self.symbolOutlineGroup.setEnabled(havesymbol)

    def updatePlotSample(self):
        """ Messages the plot sample to replot if it's visible.

        @return None
        """
        if self.plotSampleGroup.isVisible():
            self.applyToCurve(self.plotSample.curve)
            self.plotSample.replot()

    def selectColor(self, widget):
        """ Displays color selection dialog for a widget.

        @param widget object with 'color' attribute and 'setIcon' method
        @return new color if dialog accepted, otherwise None
        """
        color = QColorDialog.getColor(widget.color, self)
        if color.isValid():
            widget.color = color
            widget.setIcon(colorIcon(color))
            return color

    def eventFilter(self, watched, event):
        """ Filters framework events for another object.

        In this implementation, we trap paint events sent to the pen
        sample label widget and draw its contents based on the
        currently configured pen options.

        @param watched QObject instance
        @param event QEvent instance
        @return True if event handled, False otherwise
        """
        if watched == self.penSample:
            if event.type() == event.Paint:
                watched.paintEvent(event)
                rect = watched.rect()
                painter = QPainter()
                painter.begin(watched)
                comp = complementColor(self.selectedPen.color())
                painter.fillRect(rect, QBrush(comp))
                x1 = y1 = y2 = rect.height()/2
                x2 = rect.width() - y1
                painter.setPen(self.selectedPen)
                painter.drawLine(x1, y1, x2, y2)
                painter.end()
                return True
            else:
                return False
        else:
            return QDialog.eventFilter(self, watched, event)

    ## pen page signal handlers

    @pyqtSignature('int')
    def on_penStyle_activated(self, index):
        """ Signal handler for pen style combobox item activation.

        @param index row number of selected item.
        @return None
        """
        value, okay = self.penStyle.itemData(index).toInt()
        if okay:
            self.selectedPen.setStyle(Qt.PenStyle(value))
            self.penSample.update()
            self.updatePlotSample()

    @pyqtSignature('')
    def on_penColor_clicked(self):
        """ Signal handler for pen color button clicks.

        @return None
        """
        color = self.selectColor(self.penColor)
        if color:
            self.selectedPen.setColor(color)
            self.penSample.update()
            self.updatePlotSample()

    @pyqtSignature('int')
    def on_penWidth_valueChanged(self, value):
        """ Signal handler for pen width spinbox changes.

        @param value new value for spinbox
        @return None
        """
        self.selectedPen.setWidth(value)
        self.penSample.update()
        self.updatePlotSample()

    ## curve page signal handlers

    @pyqtSignature('int')
    def on_lineStyle_currentIndexChanged(self, index):
        """ Signal handler for curve line style combobox item activation.

        @param index row number of selected item.
        @return None
        """
        value, okay = self.lineStyle.itemData(index).toInt()
        if okay:
            self.curveAttributeInverted.setEnabled(value==QwtPlotCurve.Steps)
            self.curveAttributeFitted.setEnabled(value==QwtPlotCurve.Lines)
            hascurve = value != QwtPlotCurve.NoCurve
            self.areaFill.setEnabled(hascurve)
            self.curveAttributesGroup.setEnabled(hascurve)
            self.updatePlotSample()

    @pyqtSignature('bool')
    def on_areaFill_toggled(self, checked):
        """ Signal handler for area fill group checkbox toggle.

        @param checked new value for checkbox
        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_areaFillStyle_currentIndexChanged(self, index):
        """ Signal handler for area fill brush style combobox item activation.

        @param index row number of selected item.
        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('')
    def on_areaFillColor_clicked(self):
        """ Signal handler for area fill color button clicks.

        @return None
        """
        self.selectColor(self.areaFillColor)
        self.updatePlotSample()

    @pyqtSignature('double')
    def on_areaFillBaseline_valueChanged(self, value):
        """ Signal handler for curve baseline spinbox changes.

        @param value new value for spinbox
        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_curveAttributeInverted_stateChanged(self, state):
        """ Signal handler for inverted curve checkbox state changes.

        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_curveAttributeFitted_stateChanged(self, state):
        """ Signal handler for fitted curve checkbox state changes.

        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_paintAttributeFiltered_stateChanged(self, state):
        """ Signal handler for paint filtered checkbox state changes.

        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_paintAttributeClipPolygons_stateChanged(self, state):
        """ Signal handler for paint clip polys checkbox state changes.

        @return None
        """
        self.updatePlotSample()

    ## symbol page signal handlers

    @pyqtSignature('int')
    def on_symbolStyle_currentIndexChanged(self, index):
        """ Signal handler for symbol style combobox item activation.

        @param index row number of selected item.
        @return None
        """
        value, okay = self.symbolStyle.itemData(index).toInt()
        if okay:
            havesymbol = value != QwtSymbol.NoSymbol
            self.symbolFill.setEnabled(havesymbol)
            self.symbolSizeGroup.setEnabled(havesymbol)
            self.symbolOutlineGroup.setEnabled(havesymbol)
            self.updatePlotSample()

    @pyqtSignature('bool')
    def on_symbolFill_toggled(self, checked):
        """ Signal handler for symbol fill group checkbox toggle.

        @param checked new value for checkbox
        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_symbolFillStyle_currentIndexChanged(self, index):
        """ Signal handler for symbol brush style combobox item activation.

        @param index row number of selected item.
        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('')
    def on_symbolFillColor_clicked(self):
        """ Signal handler for symbol fill color button clicks.

        @return None
        """
        self.selectColor(self.symbolFillColor)
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_symbolWidth_valueChanged(self, value):
        """ Signal handler for symbol width spinbox changes.

        @param value new value for spinbox
        @return None
        """
        if self.symbolSyncSize.checkState() == Qt.Checked:
            self.symbolHeight.setValue(value)
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_symbolHeight_valueChanged(self, value):
        """ Signal handler for symbol height spinbox changes.

        @param value new value for spinbox
        @return None
        """
        if self.symbolSyncSize.checkState() == Qt.Checked:
            self.symbolWidth.setValue(value)
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_symbolSyncSize_stateChanged(self, state):
        """ Signal handler for sync symbol w/h checkbox state changes.

        @return None
        """
        if state == Qt.Checked:
            value = max(self.symbolWidth.value(), self.symbolHeight.value())
            self.symbolWidth.setValue(value)
            self.symbolHeight.setValue(value)

    @pyqtSignature('int')
    def on_symbolPenStyle_currentIndexChanged(self, index):
        """ Signal handler for symbol pen style combobox item activation.

        @param index row number of selected item.
        @return None
        """
        self.updatePlotSample()

    @pyqtSignature('')
    def on_symbolPenColor_clicked(self):
        """ Signal handler for symbol outline color button clicks.

        @return None
        """
        self.selectColor(self.symbolPenColor)
        self.updatePlotSample()

    @pyqtSignature('int')
    def on_symbolPenWidth_valueChanged(self, value):
        """ Signal handler for symbol pen width spinbox changes.

        @param value new value for spinbox
        @return None
        """
        self.updatePlotSample()
