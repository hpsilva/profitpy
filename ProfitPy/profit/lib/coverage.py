#!/usr/bin/env python
##~
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
##~
import os
import optparse
import sys
import time

import profit.lib.base as base
import profit.lib.tickers as tickers
import profit.lib.tools as tools

ticker_builder = tools.timed_ticker_rebuild


def ticker_sorter(a, b):
    return cmp(a.symbol, b.symbol)


def files_sorter(a, b):
    splt = os.path.split
    return cmp(int(splt(a)[-1].split('.')[-1]),
               int(splt(b)[-1].split('.')[-1]))


def coverage_test(files):
    total_profit = total_trades = 0
    separator = '-' * 41

    files.sort(files_sorter)
    for filename in files:
        print 'Coverage Test %s' % filename
        print separator
        print 'Symbol\tTrades\t  Profit\tEffective'
        print separator

        eff = {}
        tickers = tools.load_object(filename)
        source_tickers = tickers.values()
        source_tickers.sort(ticker_sorter)
        for source_ticker in source_tickers:
            sym = source_ticker.symbol
            fillsecs, msgcount, new_ticker = \
                ticker_builder(source_ticker, strategy_builders,)

            reports = new_ticker.series[1].strategy.history.summary()
            if reports:
                rptlen = len(reports)
                profit = reports[-1][-1]
                eff[sym] = (rptlen, profit)
                print '%4s\t%6s\t%8.2f' % (sym, rptlen, profit)

        if eff:
            trades = sum([v[0] for v in eff.values()])
            profit = sum([v[1] for v in eff.values()])
            eff = profit / trades
            rpt = (trades, profit, eff)
            total_profit += profit
            total_trades += trades

            print separator
            print 'Total\t%6s\t%8.2f\t%9.2f' % rpt
            print

    print '* Total\tTrades\tProfit\tEffectiveness'
    if total_trades:
        rpt = (total_trades, total_profit, total_profit/total_trades)
    else:
        rpt = (total_trades, total_profit, 0)
    print '*      \t%4s\t%6.2f\t%7.2f' % rpt
    print


if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.add_option('-f', '--files', dest='files', help='Files to process')
    parser.add_option('-s', '--strategy', dest='strategy', default='', help='Strategy callable name')
    options, args = parser.parse_args()

    print options, args
    if not options.files:
        parser.error('-f or --files option required')

    #try:
    #    strategyname = sys.argv[1]
    #except (IndexError, ):
    #    strategyname = os.environ.get('PROFITPY_STRATEGY', '')
    #win.setStrategy(strategyname)



    #try:
    #    files = sys.argv[2:]
    #    if not files:
    #        raise IndexError()
    #except (IndexError, ):
    #    print 'Usage %s file [file]...' % (sys.argv[0], )
    #    sys.exit(1)

    #try:
    #    r = coverage_test(files)
    #except (KeyboardInterrupt, ):
    #    print '** interuppted **'


    print 'running...'
    print 'done'
