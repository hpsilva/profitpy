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
__about__ = {
    'author' : 'Troy Melhase, troy@gci.net',
    'date' : '$Date$',
    'file' : '$Id$',
    'tag' : '$Name$',
    'revision' : '$Revision$',
}

import os
import sys

""" stuff we're after for the spline display :

  splrep    -- find smoothing spline given (x,y) points on curve.
   splprep   -- find smoothing spline given parametrically defined curve.
   splev     -- evaluate the spline or its derivatives.
   splint    -- compute definite integral of a spline.
   sproot    -- find the roots of a cubic spline.
   spalde    -- compute all derivatives of a spline at given points.
   bisplrep   -- find bivariate smoothing spline representation.
   bisplev 
"""

import qt

import plot_form


import profit.device.widgets.node as nodewidgets
import profit.device.widgets.shell as shell
import profit.device.util as util

import profit.lib.base as base
import profit.lib.coverage as coverage
import profit.lib.tools as tools

## this is a teribble ugly hack that doesn't belong here
import pprint
from Numeric import array
import scipy.interpolate as interpolate

def make_spline_drawer(plot_widget):
    def draw_spline(key, series, start, stop, bound_canvas):
        x = array(range(start, stop))
        y = array(series[start:stop])
    
        try:
            #vector_of_knots, spline_coefficients, spline_degree  = interpolate.splrep(x, y)
            #er = I.splrep(range(550,750), ticker.series[1][550:750])

    
            er = interpolate.splrep(x, y)
            for k in er:
                pprint.pprint(k)

            spline = list(interpolate.splev(x, er))




        except (Exception, ), ex:
            print '**', ex
        else:
            print er

        seq = spline
        sty = base.PlotStyleMarker('red')
        print 'zz', plot_widget.initCurve(key, seq, sty)


    return draw_spline
## end big hack chunk

class PlotWidget(nodewidgets.TechnicalTickerNode):
    """ PlotWidget() -> a ticker plot widget with a python shell widget

    """
    def __init__(self, parent, ticker):
        nodewidgets.TechnicalTickerNode.__init__(self, parent, ticker)
        sh = self.shell = shell.InteractiveShell(self)
        self.addTab(sh, 'Shell')

        ## TODO:  add a function to the shell for drawing the spline over a given
        ## region to the indicated (==1) ticker series plot.

        sh.interpreter.locals['ticker'] = ticker

        ## hack on!
        pw = self.plotPages[1].plots['main']
        sh.interpreter.locals['plot_widget'] = pw
        sh.interpreter.locals['draw_spline'] = make_spline_drawer(pw)
        ## hack off!

class PlotApp(plot_form.PlotForm):
    """ PlotApp(...) -> main plot controller window

    """
    title = 'Test Plot [%s]'

    def __init__(self, parent=None, name=None, fl=0):
        plot_form.PlotForm.__init__(self, parent, name, fl)
        base.stdtee(self, 'stdout', 'stderr')
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
            print 'Could not load a pickled tickers from %s' % (filename, )
            return

        self.fileName = filename
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
        try:
            ticker = self.rebuiltTickers[symbol]
            if not ticker:
                return
        except (KeyError, ):
            try:
                secs, count, ticker = \
                    tools.timed_ticker_rebuild(self.tickers[symbol], 
                                               self.strategyName, ltrim=0)
                self.rebuiltTickers[symbol] = ticker
                print 'rebuilt ticker in %s seconds' % (secs, )
            except (Exception, ), ex:
                print 'Exception rebuilding ticker: %r, %s' % (ex, ex, )
                import traceback
                traceback.print_exc()
                ticker = None

        for skey in ticker.strategy_keys:
            serobj = ticker.series[skey]
            stratobj = serobj.strategy
            coverage.simulate_final(serobj, stratobj)

        coverage.ticker_report(ticker, sys.stdout)
        supervisors = [(self.fileName, [ticker, ], ), ]
        coverage.strategy_report(self.strategyName, supervisors, sys.stdout, 
                                 print_head_foot=False, 
                                 print_sub_total=False, 
                                 print_grand_total=False, print_running_total=False)

        plotwin = qt.QVBox(self)
        PlotWidget(plotwin, ticker)
        plotwin.setCaption('%s Test Plot' % (symbol, ))
        plotwin.reparent(self, qt.Qt.WType_TopLevel, qt.QPoint(0,0), True)
        plotwin.resize(qt.QSize(850, 600))

    def not__closeEvent(self, event):
        base.stdnotee(self, 'stdout', 'stderr')
        for child in self.children():
            child.deleteLater()
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

    syms = sys.argv[3:]
    for sym in syms:
        win.showTicker(sym)

    app.exec_loop()
