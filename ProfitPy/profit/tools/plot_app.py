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
import profit.device.util as util
import profit.lib.tools as tools


class StdoutWrapper(object):
    """ StdoutWrapper(widget) -> redirects stdout to widget

    """
    def __init__(self, widget, verbose):
        self.widget = widget
        self.verbose = verbose
        sys.stdout = self

    def write(self, value):
        self.widget.insert(qt.QString(value))
        if self.verbose:
            sys.__stdout__.write(value)

    def close(self):
        sys.stdout = sys.__stdout__


class PlotApp(plot_form.PlotForm):
    """ PlotApp(...) -> main plot controller window

    """
    title = 'Test Plot [%s]'

    def __init__(self, parent=None, name=None, fl=0):
        plot_form.PlotForm.__init__(self, parent, name, fl)
        self.wrapper = StdoutWrapper(self.stdoutTextEdit, verbose=0)
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
        secs, count, newticker = rebuilder(srcticker, self.strategyName, ltrim=50)
        newticker.print_report()
        print 'rebuilt ticker in %s seconds' % (secs, )

        nodewidgets.TechnicalTickerNode.enableExtended()
        nodewidgets.TechnicalTickerNode(plotwin, newticker)

        plotwin.setCaption('%s Test Plot' % (symbol, ))
        plotwin.reparent(self, qt.Qt.WType_TopLevel, qt.QPoint(0,0), True)
        plotwin.resize(qt.QSize(850, 600))

        self.rebuiltTickers[newticker.symbol] = newticker
        return plotwin

    def closeEvent(self, event):
        self.wrapper.close()
        event.accept()


if __name__ == '__main__':
    win, app = util.qMain(PlotApp)
    win.show()

    try:
        filename = sys.argv[1]
    except (IndexError, ):
        pass
    else:
        win.loadTickers(filename)

    try:
        strategyname = sys.argv[2]
    except (IndexError, ):
        strategyname = os.environ.get('PROFITPY_STRATEGY', '')
    win.setStrategy(strategyname)

    #try:
    #    symbols = sys.argv[2:]
    #except (IndexError, ):
    #    pass
    #else:
    #    for symbol in symbols:
    #        win.showTicker(symbol).show()     

    app.exec_loop()
