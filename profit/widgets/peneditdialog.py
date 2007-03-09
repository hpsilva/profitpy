#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import QVariant, Qt, pyqtSignature
from PyQt4.QtGui import QBrush, QColor, QColorDialog, QDialog, QIcon, QPixmap
from PyQt4.QtGui import QPainter, QPen

from profit.lib.core import Settings
from profit.lib.gui import colorIcon, complementColor
from profit.widgets.ui_peneditdialog import Ui_PenEditDialog


class PenPixmap(QPixmap):
    def __init__(self):
        QPixmap.__init__(self, 64, 16)
        self.fill(QColor('white'))

    def drawStyle(self, style, painter):
        painter.begin(self)
        pen = QPen(style)
        pen.setWidth(2)
        painter.setPen(pen)
        ymid = self.height()/2
        painter.drawLine(0, ymid, self.width(), ymid)
        painter.end()


styleItems = [
    (Qt.SolidLine, 'Solid'),
    (Qt.DashLine, 'Dash'),
    (Qt.DotLine, 'Dot'),
    (Qt.DashDotLine, 'Dash Dot'),
    (Qt.DashDotDotLine, 'Dash Dot Dot'),
]


class PenEditDialog(QDialog, Ui_PenEditDialog):
    def __init__(self, pen=None, parent=None):
        QDialog.__init__(self, parent)
        self.selectedPen = pen or QPen()
        self.setupUi(self)
        self.setupStyleCombo()
        self.setupColorButton()
        self.setupWidthSpin()
        self.penSample.installEventFilter(self)
        self.enableAdvanced(False)

    def enableAdvanced(self, enable=True):
        self.tabs.setTabEnabled(1, enable)

    def setupStyleCombo(self):
        current = self.selectedPen.style()
        combo = self.penStyle
        painter = QPainter()
        for index, (style, name) in enumerate(styleItems):
            pixmap = PenPixmap()
            pixmap.drawStyle(style, painter)
            combo.addItem(QIcon(pixmap), name, QVariant(style))
            if style == current:
                combo.setCurrentIndex(index)
        combo.setIconSize(pixmap.size())

    def setupColorButton(self):
        self.penColor.color = color = self.selectedPen.color()
        self.penColor.setIcon(colorIcon(color))

    def setupWidthSpin(self):
        self.penWidth.setValue(self.selectedPen.width())

    @pyqtSignature('int')
    def on_penStyle_activated(self, index):
        value, okay = self.penStyle.itemData(index).toInt()
        if okay:
            self.selectedPen.setStyle(Qt.PenStyle(value))
            self.penSample.update()

    @pyqtSignature('int')
    def on_penWidth_valueChanged(self, value):
        self.selectedPen.setWidth(value)
        self.penSample.update()

    @pyqtSignature('')
    def on_penColor_clicked(self):
        widget = self.penColor
        color = QColorDialog.getColor(widget.color, self)
        if color.isValid():
            widget.color = color
            widget.setIcon(colorIcon(color))
            self.selectedPen.setColor(color)
            self.penSample.update()

    def eventFilter(self, obj, event):
        if obj == self.penSample:
            if event.type() == event.Paint:
                obj.paintEvent(event)
                rect = obj.rect()
                painter = QPainter()
                painter.begin(obj)
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
            return QDialog.eventFilter(self, obj, event)


if __name__ == "__main__":
    import sys
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    dlg = PenEditDialog()
    dlg.show()
    sys.exit(app.exec_())
