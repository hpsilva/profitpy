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
"""

This module demonstrates a few session builder functions.

The core idea here is to define hooks into the session object construction.  
These hooks are typically passed in as strings in the form:

    [package.]module.callable

In the gui and command line tools, these are entered as so:

    $ python plot_app.py --strategy=SomePackage.MyStrategy.SetupTheBeeOhEmBee



    account = 'profit.lib.account.build'
    strategy = None
    tickers = 'profit.lib.tickers.build'
    tickers_mapping = 'profit.lib.tickers.default_mapping'

These types aren't exposed to the main gui app yet, but can be specified by 
clients using profit.lib.session:

    connection = 'Ib.Socket.build'
    broker = 'profit.lib.broker.build'

The Profit Device widget specifies an alternate socket reader like so:


        params = {'connection_builder' : link.QIbSocketReader.build}
        # ...
        sess = session.Session(**params)


<bound method wrappertype.build of <class 'profit.device.link.QIbSocketReader'>>
 {}

profit.lib.account.build 
    {'connection_builder': <bound method wrappertype.build of <class 'profit.device.link.QIbSocketReader'>>}

profit.lib.tickers.default_mapping 
    {'connection_builder': <bound method wrappertype.build of <class 'profit.device.link.QIbSocketReader'>>}

profit.lib.tickers.build 
    {'connection_builder': <bound method wrappertype.build of <class 'profit.device.link.QIbSocketReader'>>, 
    'symbol_table': [(100, 'AAPL'), (101, 'ADBE'), (102, 'ALTR'), (103, 'AMAT'), (104, 'AMZN'), (105, 'BBBY'), (106, 'BEAS'), (107, 'BRCD'), (108, 'BRCM'), (109, 'CEPH'), (110, 'CHKP'), (111, 'CNXT'), (112, 'COST'), (113, 'CSCO'), (114, 'CTXS'), (115, 'DELL'), (116, 'DISH'), (117, 'EBAY'), (118, 'FLEX'), (119, 'GILD'), (120, 'JDSU'), (121, 'JNPR'), (122, 'KLAC'), (123, 'MEDI'), (124, 'MERQ'), (125, 'MSFT'), (126, 'MXIM'), (127, 'NTAP'), (128, 'NVDA'), (129, 'NVLS'), (130, 'NXTL'), (131, 'ORCL'), (132, 'PDLI'), (133, 'PMCS'), (134, 'PSFT'), (135, 'QCOM'), (136, 'SBUX'), (137, 'SPOT'), (138, 'SUNW'), (139, 'YHOO')]}

profit.lib.broker.build 
    {'connection_builder': <bound method wrappertype.build of <class 'profit.device.link.QIbSocketReader'>>}
None{'connection_builder': <bound method wrappertype.build of <class 'profit.device.link.QIbSocketReader'>>}




"""
import random   ## this is not a good sign!

import Ib.Socket as ibsocket
import profit.lib.account as account
import profit.lib.base as base
import profit.lib.policies as policies
import profit.lib.series as series


def connection_id_from_database(**kwds):
    """ here's a perfect opportunity to lookup a client id from an external 
        datasource.  this example doesn't do that, of course.

    """
    client_id = 1234
    return ibsocket.build(client_id=client_id)


def modified_account_object(connection=None, **kwds):
    """ this function does pretty much the same thing as the default account 
        builder (profit.lib.account.build).

    """
    min_cash = 10000
    initial_order_id = 1234
    executions = account.AccountExecutions()
    positions = account.AccountPortfolio()
    policy = policies.OrderPolicyHandler(auto_start=True)
    return account.AccountSupervisor(connection, min_cash, executions,
                                     positions, policy, initial_order_id)


def small_tickers_listing(**kwds):
    """ this builder specifies a short list of tickers.

    """
    somesymbols = ('AAPL,ADBE,AMAT,BEAS,BRCD,CEPH,CHKP,CNXT,CSCO,CTXS,DELL,'
                   'DISH,EBAY,GILD,JNPR,KLAC,MEDI,MERQ,NVDA,NVLS,PDLI')
    somesymbols = somesymbols.split(',')
    somesymbols.sort()
    return [(index+100, symbol) for index, symbol in enumerate(somesymbols)]


def sample_strategy(strategy_keys=[base.PriceTypes.Bid, ], **kwds):
    """ the purpose the strategy builder is to add strategy object to each 
        ticker.  each ticker is modified to include technical indicators.
    """
    tickers = kwds['tickers']
    style_func = base.PlotStyleMarker.set_style
    targets = [(ticker, ser)
                    for ticker in tickers.values()
                        for (key, ser) in ticker.series.items()
                            if key in strategy_keys]

    for (ticker, ser) in targets:
        index_func = ser.index_map.set
        indexes = base.AttributeMapping()
        style_func(ser, color='#aa0000')
        make_series_indexes(ser, indexes, index_func, style_func)


Reverse = base.Directions.Reverse
NoReverse = base.Directions.NoReverse
NoSignal = base.Directions.NoSignal

Short = base.Directions.Short
Long = base.Directions.Long
NoDirection = base.Directions.NoDirection


def make_series_indexes(ser, indexes, set_index, set_plot):

    class RandomStrategy(series.SeriesIndex):
        def __init__(self, ser, trade_shares):
            series.SeriesIndex.__init__(self, ser)

            self.indication = (NoDirection, NoReverse)
            self.history = [] ## required for nice plots
            self.signals = [Short, Long, ] + [NoDirection ,] * 50
            self.trade_shares = trade_shares

            random.shuffle(self.signals)


        def reindex(self):
            signal = random.choice(self.signals)
            direction = NoReverse
            ser = self.series

            if signal:
                self.indication = (signal, direction)
            else:
                self.indication = (NoDirection, NoReverse)

            self.append(signal)
            hist = len(ser)-1, ser[-1], signal, direction, self.trade_shares
            self.history.append(hist)

    kama = set_index('KAMA', series.KAMA, ser, 10)
    set_plot(kama, color='#00aa00', axis='main left')

    kama_sig = set_index('KAMA Signal', series.KAMA, kama, 10)
    set_plot(kama_sig, color='#0000aa', axis='main left')

    kama_slope = set_index('KAMA Slope', 
                           series.LinearRegressionSlope, kama, 4)
    set_plot(kama_slope, color='yellow', axis='osc left', init_display=True)

    kama_macd = set_index('KAMA-Signal MACD', series.Convergence, kama_sig, kama)
    set_plot(kama_macd, color='#ffffff', axis='osc left', curve_style='stick')

    ser.strategy = strategy = \
       set_index('Strategy', RandomStrategy, ser=ser, trade_shares=100)
    set_plot(strategy, color='#b3b3b3', axis='main right', curve_type='strategy')

    idx_names = ('kama', 'kama_sig', 'kama_macd', 'kama_slope', 'strategy')

    idxes = [(key, obj) for key, obj in locals().items() if key in idx_names]
    indexes.update(dict(idxes))


