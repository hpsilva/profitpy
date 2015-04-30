# What is ProfitPy? #

ProfitPy is a set of libraries and tools for the development, testing, and execution of automated stock trading systems Specifically, ProfitPy is a collection of Python packages, modules, and scripts that work together to help you implement an automated stock trading program (or programs). The package features:

  * A library with classes for accounts, orders, tickers, and more
  * A GUI program for executing and plotting trades in real-time
  * A GUI tool to collect ticker data for off-line use
  * A CLI tool to back-test trading strategies
  * Dozens of technical indicators and plotting widgets to display them
  * An X11 keystroke tool for automating the TWS application

# No, really, what is it? #

ProfitPy is my trading toolkit. I use its collector tool to gather data from IB TWS. Using this data, I run the coverage tool to test my trading strategies. Once I'm happy with a strategy, it gets executed with the main GUI program.

I don't include any trading strategies that work -- those are for you to write.

This toolkit only works with one broker, Interactive Brokers. Their TWS application and its API, along with crazy-low commissions and fees, make for many, many trading opportunities.