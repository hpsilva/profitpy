#!/usr/bin/env python
##~ Copyright 2004 Troy Melhase <troy@gci.net>
##~ 
##~ This file is part of the ProfitPy package.
##~ 
##~ ProfitPy is free software; you can redistribute it and/or modify
##~ it under the terms of the GNU General Public License as published by
##~ the Free Software Foundation; either version 2 of the License, or
##~ (at your option) any later version.
##~ 
##~ ProfitPy is distributed in the hope that it will be useful,
##~ but WITHOUT ANY WARRANTY; without even the implied warranty of
##~ MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##~ GNU General Public License for more details.
##~ 
##~ You should have received a copy of the GNU General Public License
##~ along with ProfitPy; if not, write to the Free Software
##~ Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

"""
import os
import sys

import qt

import plot_form


import profit.device.widgets.node as nodewidgets
import profit.device.widgets.shell as shell
import profit.device.util as util

import profit.lib.base as base
import profit.lib.tools as tools


class PlotWidget(nodewidgets.TechnicalTickerNode):
    def __init__(self, parent, ticker):
        nodewidgets.TechnicalTickerNode.__init__(self, parent, ticker)
        self.shell = shell.InteractiveShell(self)
        self.addTab(self.shell, 'Shell')
        self.shell.interpreter.locals['ticker'] = ticker

class PlotApp(plot_form.PlotForm):
    """ PlotApp(...) -> main plot controller window

    """
    title = 'Test Plot [%s]'

    def __init__(self, parent=None, name=None, fl=0):
        plot_form.PlotForm.__init__(self, parent, name, fl)
        base.stdTee(self, 'stdout', 'stderr')
        self.tickersListView.setColumnAlignment(2, qt.Qt.AlignRight)
        self.setCaption(self.title % '')
        self.resize(qt.QSize(400, 700))

        self.connect(self.openButton, qt.SIGNAL('clicked()'), 
                     self.handleOpenTickers)
        self.connect(self.tickersListView, 
                     qt.SIGNAL('doubleClicked(QListViewItem *)'),
                     self.handleShowTicker)

    def handleOpenTickers(self):
        filename = qt.QFileDialog.getOpenFileName('.',  '*', self) 
        filename = str(filename)
        if filename:
            self.loadTickers(filename)

    def loadTickers(self, filename):
        obj = tools.load_object(filename)
        if obj.__class__.__name__ == 'TickerSupervisor':
            self.tickers = obj
            self.rebuiltTickers = {}
        else:
            print 'couldn not fathom a ticker object from the pickle'
            return

        self.setCaption(self.title % filename)
        self.tickersListView.clear()

        for (tid, tsym), tobj in obj.items():
            item = qt.QListViewItem(self.tickersListView)
            item.setText(0, str(tid))
            item.setText(1, tsym)
            item.setText(2, str(len(tobj.series[1])))

    def handleShowTicker(self, item):
        sym = str(item.text(1))
        self.showTicker(sym)

    def setStrategy(self, stratname):
        print 'using strategy named "%s"' % (stratname, )
        self.strategyName = stratname

    def showTicker(self, symbol):
        plotwin = qt.QVBox(self)
        srcticker = self.tickers[symbol]

        rebuilder = tools.timed_ticker_rebuild

        try:
            secs, count, newticker = rebuilder(srcticker, self.strategyName, ltrim=50)
        except (Exception, ), ex:
            print 'Exception rebuilding ticker: %r, %s' % (ex, ex, )
        else:
            newticker.print_report()
            print 'rebuilt ticker in %s seconds' % (secs, )

            ## move to a subtype of TechnicalTickerNode with a shell
            PlotWidget(plotwin, newticker)

            plotwin.setCaption('%s Test Plot' % (symbol, ))
            plotwin.reparent(self, qt.Qt.WType_TopLevel, qt.QPoint(0,0), True)
            plotwin.resize(qt.QSize(850, 600))

            self.rebuiltTickers[newticker.symbol] = newticker
            return plotwin

    def closeEvent(self, event):
        base.stdNoTee(self, 'stdout', 'stderr')
        event.accept()

    def write(self, value):
        self.stdoutTextEdit.insert(qt.QString(value))


if __name__ == '__main__':
    win, app = util.kMain(PlotApp, "Plot App", args=sys.argv[0:1])
    win.show()

    try:
        strategyname = sys.argv[1]
    except (IndexError, ):
        strategyname = os.environ.get('PROFITPY_STRATEGY', '')
    win.setStrategy(strategyname)

    try:
        filename = sys.argv[2]
    except (IndexError, ):
        pass
    else:
        win.loadTickers(filename)

    app.exec_loop()
