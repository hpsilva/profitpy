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
import sys
import time
import traceback

import profit.lib.base as base
import profit.lib.session as session
import profit.lib.tickers as tickers
import profit.lib.tools as tools


separator = '-' * 79

def coverage(files, fh):
    ticker_builder = tools.timed_ticker_rebuild

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



def files_sorter(a, b):
    splt = os.path.split
    try:
        return cmp(int(splt(a)[-1].split('.')[-1]),
                   int(splt(b)[-1].split('.')[-1]))
    except (AttributeError, ValueError, IndexError, ):
        return cmp(a, b)


def run(strategy, files):
    start = time.time()

    total_profit = total_trades = 0
    ticksort = lambda a, b: cmp(a.symbol, b.symbol)
    rebuilder = tools.timed_ticker_rebuild

    print 'Strategy coverage run started at %s' % (time.ctime(), )
    print 'Using strategy name %s' % (strategy, )
    print 
    for filename in files:

        print 'File %s' % (filename, )
        print 'Symbol\tTrades\t  Profit\tEffective'
        print separator
        tickers = tools.load_object(filename)
        source_tickers = tickers.values()
        source_tickers.sort(ticksort)
        for source_ticker in source_tickers:
            sym = source_ticker.symbol
            print sym, '\t', 
            secs, count, newticker = rebuilder(source_ticker, strategy)

            print '\n****code marker for examining the rebuilt ticker series'
            print type(newticker.series[1].strategy); sys.exit(0)
            print count

        print
        print


    end = time.time()
    print separator
    print 'Strategy coverage run completed in %2.2f seconds' % (end - start, )


def print_usage(name):
    print 'Usage:'
    print '\t%s strategy file [file [file [...]]]' % (name, )
    print


def print_strat_ex(name):
    print separator
    traceback.print_exc()
    print separator
    print 'Exception loading strategy builder named %s' % (name, )
    print


if __name__ == '__main__':
    try:
        strat = sys.argv[1]
        files = sys.argv[2:]
        if not files:
            raise IndexError()
    except (IndexError, ):
        print_usage(name=sys.argv[0])
        sys.exit(1)

    try:
        strat_session = session.Session(strategy_builder=strat)
    except (Exception, ), ex:
        print_strat_ex(strat)
        sys.exit(2)

    files.sort(files_sorter)
    run(strategy=strat, files=files)
