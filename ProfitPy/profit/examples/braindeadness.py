import random   ## this is not a good sign!
import profit.lib.base as base
import profit.lib.series as series
import profit.lib.strategy as strategy



Reverse = base.Directions.Reverse
NoReverse = base.Directions.NoReverse
NoSignal = base.Directions.NoSignal

Short = base.Directions.Short
Long = base.Directions.Long
NoDirection = base.Directions.NoDirection

OpenCloseLookup = {
    NoReverse : 'O', 
    Reverse : 'C',
}


def braindead_strategy_factory(strategy_keys=[base.PriceTypes.Bid, ], **session):
    """ the purpose of the strategy builder is to add a strategy object to 
        each ticker.  each ticker is modified to include technical indicators
        as well.
    """
    tickers = session['tickers']
    style_func = base.set_plot_style
    targets = [(ticker, ser)
                    for ticker in tickers.values()
                        for (key, ser) in ticker.series.items()
                            if key in strategy_keys]

    for (ticker, ticker_series) in targets:
        index_func = ticker_series.index_map.set
        style_func(ticker_series, color='#aa0000')
        make_series_indexes(ticker_series, index_func, style_func)


def make_series_indexes(ser, set_index, set_plot):
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
       set_index('Strategy', BrainDeadRandomStrategy, ser=ser, trade_shares=100)
    set_plot(strategy, color='#b3b3b3', axis='main right', curve_type='strategy')



##
## strategy types must:
##      inherit from series.StrategyIndex
##      implement a reindex method to update itself
##


class BrainDeadRandomStrategy(strategy.StrategyIndex):
    def __init__(self, ser, trade_shares):
        strategy.StrategyIndex.__init__(self, ser, trade_shares)
        self.signals = [Short, Long, ] + [NoDirection ,] * 50
        random.shuffle(self.signals)

    def query(self):
        signal = random.choice(self.signals)
        return signal
