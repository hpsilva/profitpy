#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase <troy@gci.net>
# Distributed under the terms of the GNU General Public License v2

from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QFrame

from profit.lib.core import Settings, Signals
import profit.widgets.plot
reload(profit.widgets.plot)
from profit.widgets.plot import Plot
from profit.widgets.ui_plotdisplay import Ui_PlotDisplay


class PlotDisplay(QFrame, Ui_PlotDisplay):
    """ Combines two plot widgets into a single display.

    """
    def __init__(self, parent=None):
        """ Constructor.

        @param parent ancestor object
        """
        QFrame.__init__(self, parent)
        self.setupUi(self)
        self.sessionArgs = None
        self.plotWidgets = []

    def addPlot(self):
        plot = Plot()
        splitter = self.plotSplitter
        widgets = self.plotWidgets
        after = -1
        try:
            sender = self.sender().parent()
        except (AttributeError, ):
            pass
        else:
            plots = [(splitter.widget(i), i) for i in range(splitter.count())]
            try:
                after = 1 + dict(plots)[sender]
            except (KeyError, ):
                pass
        widgets.append(plot)
        self.reconfigurePlots()
        self.connect(plot.actionNewPlot, Signals.triggered, self.addPlot)
        self.connect(plot.actionClosePlot, Signals.triggered, self.closePlot)
        if self.sessionArgs:
            session, tickerId, args = self.sessionArgs
            plot.setSession(session, tickerId, *args)
        splitter.insertWidget(after, plot)
        plot.show()

    def closePlot(self):
        try:
            plot = self.sender().parent()
        except (AttributeError, ):
            pass
        else:
            if plot in self.plotWidgets:
                self.plotWidgets.remove(plot)
            plot.close()
        self.reconfigurePlots()

    def reconfigurePlots(self):
        self.setActionsEnabled()
        self.reconnectSplitters()
        self.renamePlots()
        self.saveCount()

    def reconnectSplitters(self):
        widgets = self.plotWidgets
        signal = Signals.splitterMoved
        for widget in widgets:
            for other in [w for w in widgets if w is not widget]:
                self.disconnect(
                    widget.plotSplitter, signal,
                    other.plotSplitter.moveSplitter)
                self.disconnect(
                    other.plotSplitter, signal,
                    widget.plotSplitter.moveSplitter)
        if widgets:
            first, others = widgets[0], widgets[1:]
            for other in others:
                self.connect(
                    first.plotSplitter, signal,
                    other.plotSplitter.moveSplitter)

    def renamePlots(self):
        for index, plot in enumerate(self.plotWidgets):
            plot.setObjectName('indexPlot%s' % index)

    def saveCount(self):
        settings = Settings()
        settings.beginGroup('Plots')
        settings.beginGroup('%s' % self.sessionArgs[1])
        settings.setValue('displaycount', len(self.plotWidgets))

    def setActionsEnabled(self):
        single = len(self.plotWidgets) < 2
        maxed = len(self.plotWidgets) > 5
        for plot in self.plotWidgets:
            plot.actionClosePlot.setEnabled(not single)
            plot.actionNewPlot.setEnabled(not maxed)

    def setSession(self, session, tickerId, *args):
        """ Associate a session with this instance.

        @param session Session instance
        @param tickerId id of ticker as integer
        @param *indexes unused
        @return None
        """
        self.sessionArgs = (session, tickerId, args)
        if not self.plotWidgets:
            settings = Settings()
            settings.beginGroup('Plots')
            settings.beginGroup('%s' % tickerId)
            count = settings.value('displaycount', QVariant(1)).toInt()[0]
            for i in range(count):
                self.addPlot()
        else:
            for plot in self.plotWidgets:
                plot.setSession(session, tickerId, *args)
