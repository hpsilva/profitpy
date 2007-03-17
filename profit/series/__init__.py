#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

# TODO: write docstrings on series types

from time import time
from Numeric import arctan, array, log
from scipy.stats import linregress, mean, std, median, mode


class Series(list):
    """ Series objects are lists that maintain indexes.

    """
    def __init__(self):
        list.__init__(self)
        self.indexes = []
        self.x = []
        self.y = []

    def append(self, value):
        """ append value to this series and update its indexes

        """
        list.append(self, value)
        if value is not None:
            self.y.append(value)
            self.x.append(len(self))
        for index in self.indexes:
            index.reindex()

    def addIndex(self, key, func, *args, **kwds):
        indexes = self.indexes
        keys = [i.key for i in indexes]
        if key in keys:
            index = [i for i in indexes if i.key==key][0]
        else:
            index = func(*args, **kwds)
            index.key = key
            indexes.append(index)
        return index


class BaseIndex(list):
    """ Base class for index types.

    """
    def __init__(self):
        list.__init__(self)
        self.x = []
        self.y = []


    def append(self, value):
        """ append value to this series and update its indexes

        """
        list.append(self, value)
        if value is not None:
            self.y.append(value)
            self.x.append(len(self))


class SeriesIndex(BaseIndex):
    """ Base class for series indexes.

    """
    def __init__(self, series):
        BaseIndex.__init__(self)
        self.series = series


class MovingAverageIndex(SeriesIndex):
    """ MovingAverageIndex -> base class for moving average indexes

    """
    def __init__(self, series, periods):
        SeriesIndex.__init__(self, series)
        self.periods = periods
        self.periods_range = range(periods)


class CenterOfGravity(MovingAverageIndex):
    """ Center of gravity oscillator index.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        try:
            n, d = 0, 0
            for c in range(periods):
                n += (1+c) * period[-c]
                d += period[-c]
            cg = -n/d
            # bah - these adjustments are for plotting
            # need a way to identify plot axis
            #cg += 50.5
            cg += 15.5
        except (TypeError, IndexError, ZeroDivisionError, ):
            cg = None
        self.append(cg)


class FisherTransform(MovingAverageIndex):
    """ FisherTransform -> er?

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def __init__(self, series, periods):
        MovingAverageIndex.__init__(self, series, periods)
        self.inter = []

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        current = period[-1]
        mx = max(period)
        mn = min(period)
        try:
            inter = 0.33 * 2 * ((current - mn) / (mx - mn) - 0.5) + (0.67 * self.inter[-1])
            if inter > 0.99:
                inter = 0.99
            elif inter < -0.99:
                inter = -0.99
            fish = 0.5 * log((1 + inter) / (1 - inter)) + (0.5 * self[-1])
        except (TypeError, IndexError, ZeroDivisionError, ):
            inter = 0
            fish = 0

        self.inter.append(inter)
        self.append(fish)


class MAMA(MovingAverageIndex):
    """ Mother of Adaptave Moving Averages - broken beyond belief, too.

    """
    fast_limit = 0.5
    slow_limit = 0.05
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def __init__(self, series, periods):
        MovingAverageIndex.__init__(self, series, periods)
        self.hist = {'q1':[], 'i1':[], 'q2':[], 'i2':[], 're':[], 'im':[],
                     'sms':[], 'dts':[], 'prs':[], 'sps':[], 'phs':[], }


    def reindex(self):
        hist = self.hist
        sms, dts, prs, sps, phs = \
            hist['sms'], hist['dts'], hist['prs'], hist['sps'], hist['phs']
        q1, i1, q2, i2, re, im = \
            hist['q1'], hist['i1'], hist['q2'], hist['i2'], hist['re'], hist['im']

        series = self.series
        periods = self.periods

        if len(series) > periods:
            sm = sum((4*series[-1], 3*series[-2], 2*series[-3], series[-4])) / 10
            sms.append(sm)

            dt = (0.0962*sms[-1] + 0.5769*sms[-3] - 0.5769*sms[-5] - 0.0962*sms[-7]) * (0.075*prs[-2] + 0.54)
            dts.append(dt)

            qa = (.0962*dts[-1] + 0.5769*dts[-3] - 0.5769*dts[-5] - 0.0962*dts[-7]) * (0.075*prs[-2] + 0.54)
            q1.append(qa)

            ia = dts[-4]
            i1.append(ia)

            jI = (0.0962*i1[-1] + 0.5769*i1[-3] - 0.5769*i1[-5] - 0.0962*i1[-7]) * (0.075*prs[-2] + 0.54)
            jQ = (0.0962*q1[-1] + 0.5769*q1[-3] - 0.5769*q1[-5] - 0.0962*q1[-7]) * (0.075*prs[-2] + 0.54)

            ib = i1[-1] - jQ
            qb = q1[-1] - jI
            ib = 0.2*ib + 0.8*i2[-1]
            qb = 0.2*qb + 0.8*q2[-1]
            i2.append(ib)
            q2.append(qb)

            ra = i2[-1]*i2[-2] + q2[-1]*q2[-2]
            ima = i2[-1]*q2[-2] - q2[-1]*i2[-2]
            ra = 0.2*ra + 0.8*re[-1]
            ima = 0.2*ra + 0.8*im[-1]
            re.append(ra)
            im.append(ima)

            if im[-1] != 0 and re[-1] != 0:
                pra = 360 / arctan(im[-1]/re[-1])
            else:
                pra = 0

            if pra > 1.5*prs[-1]: pra = 1.5*prs[-1]
            if pra < 0.67*prs[-1]: prs = 0.67*prs[-1]
            if pra < 6: pra = 6
            if pra > 50: pra = 50
            pra = 0.2*pra + 0.8*prs[-1]
            prs.append(pra)

            spa = 0.33*prs[-1] + 0.67*sps[-1]
            sps.append(spa)

            if i1[-1] != 0:
                ph = arctan(q1[-1] / i1[-1])
            else:
                ph = 0
            phs.append(ph)

            dp = phs[-2] - phs[-1]
            if dp < 1: dp = 1
            alpha = self.fast_limit / dp
            if alpha < self.slow_limit: alpha = self.slow_limit
            mama = alpha*series[-1] + (1 - alpha)*self[-1]
            #FAMA = .5*alpha*MAMA + (1 - .5*alpha)*FAMA[1];
            self.append(mama)
        else:
            last = series[-1]
            for vlst in hist.values():
                vlst.append(last)
            self.append(last)


class SmoothedRSI(MovingAverageIndex):
    """ Smoothed relative strength index.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def __init__(self, series, periods):
        MovingAverageIndex.__init__(self, series, periods)
        self.smooth = []

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        smooth = self.smooth

        try:
            s = (period[-1] + 2*period[-2] + 2*period[-3] + period[-4]) / 6.0
            smooth.append(s)
        except (IndexError, ):
            self.append(0)
            return

        smooth.append(s)
        cu = cd = 0
        try:
            for count in range(1, periods):
                s = smooth[-count]
                ps = smooth[-count-1]
                if s > ps:
                    cu += s - ps
                if s < ps:
                    cd += ps - s
        except (IndexError, ):
            self.append(0)
            return

        try:
            srsi = cu/(cu+cd)
        except (ZeroDivisionError, ):
            srsi = 0
        self.append(srsi)


class SMA(MovingAverageIndex):
    """ Simple Moving Average index.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        sma = None
        if len(period) == periods:
            try:
                sma = mean(period)
            except (TypeError, IndexError):
                pass
        self.append(sma)


class EMA(MovingAverageIndex):
    """ Exponential Moving Average index.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1)),
        ('k', dict(type='float', min=0.001, default=2.0))
    ]

    def __init__(self, series, periods, k=2.0):
        MovingAverageIndex.__init__(self, series, periods)
        self.k = k

    def reindex(self):
        try:
            last = self[-1]
        except (IndexError, ):
            self.append(None)
            return
        periods = self.periods
        ema = None
        if last is None:
            try:
                period = self.series[-periods:]
                if len(period) == periods:
                    ema = mean(period)
            except (TypeError, ):
                pass
        else:
            pt = self.series[-1]
            k = self.k / (periods + 1)
            ema = last + (k * (pt - last))
        self.append(ema)


class KAMA(MovingAverageIndex):
    """ Kaufmann Adaptive Moving Average index.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1)),
        ('fast_look', dict(type='float', min=0.0, default=2)),
        ('slow_look', dict(type='float', min=0.0, default=30)),
    ]

    def __init__(self, series, periods, fast_look=2, slow_look=30):
        MovingAverageIndex.__init__(self, series, periods)
        self.fastest = 2.0 / (fast_look+1)
        self.slowest = 2.0 / (slow_look+1)
        self.efficiency_factor = (self.fastest - self.slowest) + self.slowest ## er?

    def reindex(self):
        " kama = S * price + (1 - S) * kama[-1] "
        series = self.series
        periods = self.periods
        last = series[-1]
        try:
            prev = series[-2]
        except (IndexError, ):
            self.append(last)
            return
        noise = 0
        eff = 1
        try:
            p1 = series[-periods:]
            p2 = series[-periods-1:-1]
            noise = sum([abs(a-b) for a, b in zip(p1, p2)])
        except (IndexError, ):
            pass
        if noise:
            eff = abs(last - prev) / noise
        s = eff * self.efficiency_factor
        s = s * s
        kama = s*last + (1-s)*self[-1]
        self.append(kama)


class DistanceCoefficient(MovingAverageIndex):
    """ Distance Coefficient index.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1)),
    ]

    def __init__(self, series, periods):
        MovingAverageIndex.__init__(self, series, periods)

    def reindex(self):
        series = self.series
        periods = self.periods
        period = self.series[-periods:]
        dists = [0, ] * periods
        coeff = [0, ] * periods
        try:
            for i in range(-1, -periods, -1):
                for k in range(-2, -periods, -1):
                    dists[i] = dists[i] + (series[i] - series[i+k]) * (series[i] - series[i+k])
                coeff[i] = dists[i]
            num = sumcoeff = 0
            for k in range(periods):
                num += coeff[i]*period[i]
                sumcoeff += coeff[i]
            if sumcoeff:
                filt = num / sumcoeff
            else:
                filt = 0
        except (IndexError, ):
            filt = None
        self.append(filt)


class WMA(MovingAverageIndex):
    """ Weighted Moving Average index.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1)),
    ]

    def __init__(self, series, periods):
        MovingAverageIndex.__init__(self, series, periods)
        offsets = range(1, periods+1)
        periods_sum = float(sum(offsets))
        self.weights = array([x/periods_sum for x in offsets])

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        wma = None
        if len(period) == periods:
            try:
                wma = sum(period * self.weights)
            except (TypeError, ):
                pass
        self.append(wma)


class Convergence(SeriesIndex):
    """ Convergence Line index.

    """
    params = [
        ('series', dict(type='line')),
        ('signal', dict(type='line')),
    ]

    def __init__(self, series, signal):
        SeriesIndex.__init__(self, series)
        self.signal = signal

    def reindex(self):
        try:
            self.append(self.signal[-1] - self.series[-1])
        except (TypeError, ):
            self.append(None)


class PercentConvergence(SeriesIndex):
    """ Index of convergence as a percentage.

    """
    params = [
        ('series', dict(type='line')),
        ('signal', dict(type='line')),
    ]

    def __init__(self, series, signal):
        SeriesIndex.__init__(self, series)
        self.signal = signal

    def reindex(self):
        try:
            self.append((1 - self.signal[-1] / self.series[-1]) * 100)
        except (TypeError, ZeroDivisionError, ):
            self.append(None)


class MACDHistogram(SeriesIndex):
    """ Tracks difference between line and its signal.

    """
    params = [
        ('series', dict(type='line')),
        ('signal', dict(type='line')),
    ]

    def __init__(self, series, signal):
        SeriesIndex.__init__(self, series)
        self.signal = signal

    def reindex(self):
        try:
            self.append(self.series[-1] - self.signal[-1])
        except (TypeError, ):
            self.append(None)


class DetrendedPriceOscillator(SeriesIndex):
    """ Detrended price oscillator index.

    DPO = Close - Simple moving average [from (n / 2 + 1) days ago]
    """
    params = [
        ('series', dict(type='line')),
        ('moving_average', dict(type='line')),
    ]

    def __init__(self, series, moving_average):
        self.series, self.moving_average = series, moving_average

    def reindex(self):
        last = self.series[-1]
        lookback = (self.moving_average.periods/2) + 1
        try:
            dpo = last - self.moving_average[-lookback]
        except (TypeError, IndexError):
            dpo = None
        self.append(dpo)


class Trix(SeriesIndex):
    params = [
        ('series', dict(type='line')),
    ]

    def reindex(self):
        try:
            current, previous = self.series[-1], self.series[-2]
            trix = (current - previous) / previous
            trix *= 100
        except (TypeError, IndexError):
            trix = None
        self.append(trix)


class Volatility(MovingAverageIndex):
    """ Volatility index.

    Volatility = standard deviation of closing price [for n periods] /
    average closing price [for n periods]
    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1)),
    ]

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        vol = None
        if len(period) == periods:
            try:
                vol = std(period) / mean(period)
                vol *= 100
            except TypeError:
                pass
        self.append(vol)


class Momentum(SeriesIndex):
    """ Momentum index.

    """
    params = [
        ('series', dict(type='line')),
        ('lookback', dict(type='int', min=1)),
    ]

    def __init__(self, series, lookback):
        SeriesIndex.__init__(self, series)
        self.lookback = lookback

    def reindex(self):
        try:
            last, prev = self.series[-1], self.series[-self.lookback]
            momentum = last - prev
        except (IndexError, TypeError):
            momentum = None
        self.append(momentum)


class RateOfChange(SeriesIndex):
    """ Rate of change index.

    """
    params = [
        ('series', dict(type='line')),
        ('lookback', dict(type='int', min=1)),
    ]

    def __init__(self, series, lookback):
        SeriesIndex.__init__(self, series)
        self.lookback = lookback

    def reindex(self):
        try:
            last, prev = self.series[-1], self.series[-self.lookback]
            momentum = last - prev
            rate = momentum / (prev*100)
            rate *= 100
        except (IndexError, TypeError, ZeroDivisionError):
            rate = None
        self.append(rate)


class VerticalHorizontalFilter(MovingAverageIndex):
    """ VerticalHorizontalFilter

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        vhf = None
        if len(period) == periods:
            try:
                diffs = array(period[1:]) - period[0:-1]
                vhf = (max(period) - min(period)) / sum(abs(diffs))
            except (IndexError, TypeError, ZeroDivisionError):
                pass
        self.append(vhf)


class Stochastic(MovingAverageIndex):
    """ Stochastic

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        lowest = min(period)
        highest = max(period)
        cl = self.series[-1] - lowest
        hl = highest - lowest
        if cl == 0:
            k = 0.0
        else:
            k = cl / float(hl)
        self.append(k)


class WilliamsR(MovingAverageIndex):
    """ WilliamsR

    WilliamsR is almost the same as Stochastic except that it's
    adjusted * -100.
    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def reindex(self):
        periods = self.periods
        period = self.series[-periods:]
        lowest = min(period)
        highest = max(period)
        hc = highest - self.series[-1]
        hl = highest - lowest
        try:
            r = (hc / hl) * -100
        except (ZeroDivisionError, ):
            r = 0
        self.append(r)


class BollingerBand(SeriesIndex):
    """ BollingerBand

    """
    params = [
        ('series', dict(type='line')),
        ('period', dict(type='int', min=1)),
        ('dev_factor', dict(type='float')),
    ]

    def __init__(self, series, period, dev_factor):
        SeriesIndex.__init__(self, series)
        self.period = period # allows for periods != periods of series
        self.dev_factor = dev_factor

    def reindex(self):
        period = self.series[-self.period:]
        last = self.series[-1]
        try:
            dev = std(period)
            dev *= self.dev_factor
            dev += last
        except (TypeError, ZeroDivisionError, ):
            dev = None
        self.append(dev)


class LinearRegressionSlope(SeriesIndex):
    """ LinearRegressionSlope

    LinearRegressionSlope(series, periods) -> slope of the linear
    regression
    """
    params = [
        ('series', dict(type='line')),
        ('period', dict(type='int', min=1)),
        ('scale', dict(type='float', default=1.0)),
    ]

    def __init__(self, series, periods, scale=1):
        SeriesIndex.__init__(self, series)
        self.periods = periods
        self.scale = scale
        self.xarray = array(range(0, periods))

    def reindex(self):
        xa = self.xarray
        ya = array(self.series[-self.periods:])
        try:
            slope, intercept, r, two_tail_prob, est_stderr = linregress(xa, ya)
        except (TypeError, ValueError, ZeroDivisionError):
            slope = 0.0
        self.append(slope * self.scale)


class TrueRange(MovingAverageIndex):
    """ True range index.

    True Range is the greater of:

    * High for the period less the Low for the period
    * High for the period less the Close for the previous period
    * Close for the previous period and the Low for the current
      period.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1)),
    ]

    def reindex(self):
        periods = self.periods
        items = self.series[-periods:]
        if len(items) == periods and periods > 1:
            high = max(items)
            low = min(items)
            prev_last = self.series[-2]
            truerange = max((high-low, high-prev_last, prev_last-low))
        else:
            truerange = None
        self.append(truerange)


class OrderStatisticFilter(MovingAverageIndex):
    """ Ordered Statistic Filter base class.

    OS filters base their operation on the ranking of the samples
    within the filter window.  The data are ranked by their summary
    statistics, such as their mean or variance, rather than by their
    temporal position.
    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]


class MedianValue(OrderStatisticFilter):
    """ Indexes a series by the median.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def reindex(self):
        values = self.series[-self.periods:]
        m = median(values).toscalar()
        self.append(m)


class ModeValue(OrderStatisticFilter):
    """ Indexes a series by the mode.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1))
    ]

    def reindex(self):
        values = self.series[-self.periods:]
        m = mode(values)[0].toscalar()
        self.append(m)


class DelayFilter(SeriesIndex):
    """ Duplicates a series by a previous value.

    """
    params = [
        ('series', dict(type='line')),
        ('lookback', dict(type='int', min=1))
    ]

    def __init__(self, series, lookback):
        self.series = series
        self.lookback = lookback

    def reindex(self):
        try:
            v = self.series[-self.lookback]
        except (IndexError, ):
            v = None
        self.append(v)


class TimeIndex(SeriesIndex):
    """ Tracks the time stamps of values as they're added.

    """
    params = [
        ('series', dict(type='line')),
    ]

    def __init__(self, series, timefunc=None):
        SeriesIndex.__init__(self, series)
        self.timefunc = timefunc if timefunc else time

    def reindex(self):
        self.append(self.timefunc())


class ChangeIndex(SeriesIndex):
    """ Tracks the difference between updates.

    """
    params = [
        ('series', dict(type='line')),
    ]

    def reindex(self):
        try:
            change = self.series[-1] - self.series[-2]
        except (TypeError, IndexError):
            change = None
        self.append(change)


class IndexIndex(SeriesIndex):
    """ Index that maintains the current series length.

    """
    params = [
        ('series', dict(type='line')),
    ]

    def __init__(self, series):
        SeriesIndex.__init__(self, series)
        self.idx = 0

    def reindex(self):
        self.append(self.idx)
        self.idx += 1


class LevelIndex(SeriesIndex):
    """ Constant level indexing.

    """
    params = [
        ('series', dict(type='line')),
        ('level', dict(type='float')),
    ]

    def __init__(self, series, level):
        SeriesIndex.__init__(self, series)
        self.level = level

    def reindex(self):
        self.append(self.level)


class OffsetIndex(SeriesIndex):
    params = [
        ('series', dict(type='line')),
        ('offset', dict(type='float')),
    ]

    def __init__(self, series, offset):
        SeriesIndex.__init__(self, series)
        self.offset = offset

    def reindex(self):
        last = self.series[-1]
        try:
            offset = last + (self.offset * last)
        except TypeError:
            offset = None
        self.append(offset)


class Slope(SeriesIndex):
    """ Slope values as an index.

    """
    params = [
        ('series', dict(type='line')),
    ]

    def reindex(self):
        try:
            Y1, Y2 = self.series[-2], self.series[-1]
            slope = Y2-Y1 ## X1-X2 is always 1
        except (IndexError, TypeError):
            slope = None
        self.append(slope)


class DifferenceIndex(SeriesIndex):
    """

    """
    params = [
        ('series', dict(type='line')),
        ('other', dict(type='line')),
    ]

    def __init__(self, series, other):
        SeriesIndex.__init__(self, series)
        self.other = other

    def reindex(self):
        try:
            diff = self.series[-1] - self.other[-1]
        except:
            diff = None
        self.append(diff)


# Unfinished Indexes


class RSI(MovingAverageIndex):
    """ Relative Strength Index - needs work.

    """
    params = [
        ('series', dict(type='line')),
        ('periods', dict(type='int', min=1)),
        ('change_line', dict(type='line')),
    ]

    def __init__(self, series, periods, change_line):
        MovingAverageIndex.__init__(self, series, periods)
        self.change_line = change_line
        self._prevs = []

    def get_avgs(self):
        thisdata = self.series[-self.periods:]
        thischange = self.change_line[-self.periods:]
        gains = filter(lambda x: x>=0, thischange)
        losses = filter(lambda x: x<0, thischange)
        avggain = gains / float(self.periods)
        avgloss = losses / float(self.periods)
        return avggain, avgloss

    def reindex(self):
        if len(self.series) < self.periods:
            rsi = None
        elif len(self.series) == self.periods:
            avggain, avgloss = self.get_avgs()
            self._prevs.append((avggain, avgloss))
            rsi = avggain  / avgloss
        else:
            periods = self.periods
            pavggain, pavgloss = self._prevs.pop()
            rsi = None
        self.append(rsi)


class LoPassFilter(SeriesIndex):
    params = [
        ('series', dict(type='line')),
        ('cutoff', dict(type='float')),
    ]

    def __init__(self, series, cutoff):
        self.series = series
        self.cutoff = cutoff

    def reindex(self):
        v = self.series[-1]
        if v is not None and v > self.cutoff:
            v = self.cutoff
        self.append(v)


class HiPassFilter(SeriesIndex):
    params = [
        ('series', dict(type='line')),
        ('cutoff', dict(type='float')),
    ]

    def __init__(self, series, cutoff):
        self.series = series
        self.cutoff = cutoff

    def reindex(self):
        v = self.series[-1]
        if v is not None and v < self.cutoff:
            v = self.cutoff
        self.append(v)


class BandPassFilter(SeriesIndex):
    params = [
        ('series', dict(type='line')),
        ('hi', dict(type='float')),
        ('low', dict(type='float')),
    ]

    def __init__(self, series, hi, low):
        self.series = series
        self.hi = hi
        self.low = low

    def reindex(self):
        v = self.series[-1]
        if v is None:
            pass
        if v > self.hi:
            v = self.hi
        if v < self.low:
            v = self.low
        self.append(v)


class UpMovement(SeriesIndex):
    params = [
        ('series', dict(type='line')),
    ]

    def reindex(self):
        try:
            prev, current = self.series[-2:]
            throw_away = prev + current
            up = current > prev
        except (IndexError, TypeError):
            up = 0
        self.append(int(up))


class DownMovement(SeriesIndex):
    params = [
        ('series', dict(type='line')),
    ]

    def reindex(self):
        try:
            prev, current = self.series[-2:]
            throw_away = prev + current
            dn = current < prev
        except (IndexError, TypeError):
            dn = 0
        self.append(int(dn))
