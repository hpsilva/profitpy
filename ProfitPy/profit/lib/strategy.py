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
""" strategy

"""
import profit.lib.base as base
import profit.lib.series as series


Reverse = base.Directions.Reverse
NoReverse = base.Directions.NoReverse

Short = base.Directions.Short
Long = base.Directions.Long
NoDirection = base.Directions.NoDirection


class StrategyIndex(series.SeriesIndex):
    """ StrategyIndex(...) -> a base type for user strategies

        Clients should use this class as a base and reimplement the 'query' 
        method, and return Short, Long, or NoDirection from that.
    """
    def __init__(self, ser, trade_shares):
        series.SeriesIndex.__init__(self, ser)
        self.trade_shares = trade_shares
        self.indication = (NoDirection, NoReverse)
        self.history = []
        self.position = 0

    def query(self):
        """ query() -> this method must be implemented by clients

        """
        exmsg = "Class %s does not reimplement 'query' method'"
        exmsg = exmsg % (self.__class__.__name__, )
        raise NotImplementedError(exmsg)

    def reindex(self):
        """ reindex() -> calculate a signal for this strategy

            This implementation defers strategy calculation to the 'query' 
            method then uses that result to determine the Reverse-NoReverse
            value, then finally uses both values together to form an 
            indication.
        """
        signal = self.query()
        ser = self.series
        shares = self.trade_shares
        lastposition = self.position
        reverse = NoReverse

        ## if there is an existing position, a new signal, and if the position
        ## direction is different than the current signal, indicate a reverse
        if lastposition and signal:
            if (abs(lastposition) / lastposition) != signal:
                reverse = 1
        
        ## formulate the current indication
        if signal:
            self.indication = (signal, reverse)
        else:
            self.indication = (NoDirection, NoReverse)

        ## adjust the position according to the signal and reverse.  if there
        ## is a previous position and no reverse, the position is furthered.
        if lastposition and reverse:
            quan = -lastposition
            self.position = 0
        else:
            quan = shares * signal
            self.position += quan

        x = len(ser) - 1
        y = ser[-1]

        key = (x, y, signal, reverse, )
        extras = (shares, self.position, quan, )
        self.history.append(key + extras)

        self.append(signal)


class strat_iter(object):
    def __init__(self, strat):
        self.strat = strat

    def next(self):
        yield self.strat.next()

        x = 0
        while True:
            try:
                yield self[x]
                x += 1
            except (IndexError, ):
                raise StopIteration()


## older code ; make sure these calls are factored out

    def __signal_orders(self):
        """ signal_orders() ->

        """
        oc_lookup = {NoReverse : 'O', Reverse : 'C',}
        oc = oc_lookup[reverse]
        signals = self.history
        
 
        order = base.Order(quantity=quan, limit_price=y, 
                           transmit=0, open_close=open_close)


    def __summary(self):
        """ summary() -> summarize the orders tracked with this object

        """
        ## simulate a final close order if there's an open position
        ## note that this screws up a call to summary on a live strategy
        if self.position:
            dr = -(self.position / abs(self.position))
            x = len(self.strategy.series)
            y = self.strategy.series[-1]
            self.save(x, y, direction=dr, reverse=1, shares=self.position)

        reports = []
        running_total = 0

        ## maybe need to track error rate here
        for order in [record[6] for record in self]:
            order_cost = base.Order.cost_long(order)
            running_total -= order_cost
            reports.append((order.limit_price, order_cost, running_total))

        return reports
