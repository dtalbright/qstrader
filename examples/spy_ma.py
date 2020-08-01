import os

import pandas as pd
import pytz

from qstrader.alpha_model.fixed_signals import FixedSignalsAlphaModel
from qstrader.alpha_model.time_signals import TimeSignalsAlphaModel
from qstrader.asset.equity import Equity
from qstrader.asset.universe.static import StaticUniverse
from qstrader.data.backtest_data_handler import BacktestDataHandler
from qstrader.data.daily_bar_csv import CSVDailyBarDataSource
from qstrader.statistics.tearsheet_long import TearsheetStatistics
from qstrader.trading.backtest import BacktestTradingSession

def apply_sma_strategy(row):
    if row['EQ:SPY'] >= row['MA:SPY']:
        return 'aggressive'
    else:
        return 'defensive'


if __name__ == "__main__":
    start_dt = pd.Timestamp('2004-12-28 14:30:00', tz=pytz.UTC)
    end_dt = pd.Timestamp('2020-06-25 23:59:00', tz=pytz.UTC)

    # Construct the symbols and assets necessary for the backtest
    strategy_symbols = ['SPY', 'AGG']
    strategy_assets = ['EQ:%s' % symbol for symbol in strategy_symbols]
    strategy_universe = StaticUniverse(strategy_assets)

    # To avoid loading all CSV files in the directory, set the
    # data source to load only those provided symbols
    csv_dir = os.environ.get('QSTRADER_CSV_DATA_DIR', '.')
    data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=strategy_symbols)
    #DADebug
    #with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.expand_frame_repr", False):
    #    for asset, df in data_source.asset_bid_ask_frames.items():
    #        print("ASSET: " + asset)
    #        print(df)
    data_handler = BacktestDataHandler(strategy_universe, data_sources=[data_source])

    df = data_handler.get_assets_historical_range_close_price(start_dt - pd.Timedelta(days=202), end_dt, ['EQ:SPY'], True)
    #print(df.head())
    #df['SPY:MA'] = df.groupby('Date')['EQ:SPY'].transform(lambda x: x.rolling(window=10).mean())
    df['MA:SPY'] = df['EQ:SPY'].rolling(window=200).mean()
    df['strategy'] = df.apply(lambda row: apply_sma_strategy(row), axis=1)
    #with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.expand_frame_repr", False):
    #    print(df)

    # Construct an Alpha Model that simply provides
    # static allocations to a universe of assets
    # In this case 60% SPY ETF, 40% AGG ETF,
    # rebalanced at the end of each month
    defensive_alloc = {'EQ:SPY': 0.4, 'EQ:AGG': 0.6} 
    aggressive_alloc = {'EQ:SPY': 0.6, 'EQ:AGG': 0.4} 
    strategy_signal = {'defensive' : defensive_alloc, 'aggressive' : aggressive_alloc}
    strategy_alpha_model = TimeSignalsAlphaModel(strategy_signal, df)
    strategy_backtest = BacktestTradingSession(
        start_dt,
        end_dt,
        strategy_universe,
        strategy_alpha_model,
        rebalance='end_of_month',
        long_only=True,
        cash_buffer_percentage=0.01,
        data_handler=data_handler,
        rebalance_weekday='FRI'
    )
    strategy_backtest.run()

    ## Construct benchmark assets (buy & hold SPY)
    #benchmark_assets = ['EQ:SPY']
    #benchmark_universe = StaticUniverse(benchmark_assets)
    benchmark_symbols = ['SPY', 'AGG']
    benchmark_data_source = CSVDailyBarDataSource(csv_dir, Equity, csv_symbols=benchmark_symbols)
    benchmark_assets = ['EQ:SPY', 'EQ:AGG']
    benchmark_universe = StaticUniverse(benchmark_assets)
    benchmark_data_handler = BacktestDataHandler(strategy_universe, data_sources=[benchmark_data_source])

    # Construct a benchmark Alpha Model that provides
    # 100% static allocation to the SPY ETF, with no rebalance
    #benchmark_alpha_model = FixedSignalsAlphaModel({'EQ:SPY': 1.0})
    benchmark_alpha_model = FixedSignalsAlphaModel({'EQ:SPY': 0.6, 'EQ:AGG': 0.4})
    benchmark_backtest = BacktestTradingSession(
        start_dt,
        end_dt,
        benchmark_universe,
        benchmark_alpha_model,
        #rebalance='buy_and_hold',
        rebalance='end_of_month',
        long_only=True,
        cash_buffer_percentage=0.01,
        data_handler=benchmark_data_handler
    )
    benchmark_backtest.run()

    # Performance Output
    tearsheet = TearsheetStatistics(
        strategy_equity=strategy_backtest.get_equity_curve(),
        benchmark_equity=benchmark_backtest.get_equity_curve(),
        title='Time Signal US Equities/Cash'
    )
    tearsheet.plot_results()
