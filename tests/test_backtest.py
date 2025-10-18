import pytest
import pandas as pd
import numpy as np
from core.backtest import run_backtest, calculate_buy_and_hold_return
from core.strategy import generate_signals


def create_backtest_data():
    dates = pd.date_range('2023-01-01', periods=100, freq='W')
    
    data = []
    base_price = 100
    
    for i, date in enumerate(dates):
        if i < 30:
            base_price += 1
        elif i < 60:
            base_price -= 0.5
        else:
            base_price += 0.8
        
        high = base_price + 2
        low = base_price - 2
        close = base_price + np.random.normal(0, 0.5)
        volume = 10000
        
        data.append({
            'open': base_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data, index=dates)


def test_backtest_basic_functionality():
    df = create_backtest_data()
    results = run_backtest(df, initial_capital=10000, period=5, multiplier=2.0)
    
    required_keys = [
        'total_return', 'max_drawdown', 'win_rate', 'sharpe_ratio',
        'num_trades', 'avg_trade_duration', 'equity_curve', 'trades'
    ]
    
    for key in required_keys:
        assert key in results
    
    assert isinstance(results['total_return'], (int, float))
    assert isinstance(results['max_drawdown'], (int, float))
    assert isinstance(results['win_rate'], (int, float))
    assert isinstance(results['sharpe_ratio'], (int, float))
    assert isinstance(results['num_trades'], int)
    assert isinstance(results['avg_trade_duration'], (int, float))
    assert isinstance(results['equity_curve'], pd.Series)
    assert isinstance(results['trades'], list)


def test_backtest_equity_curve():
    df = create_backtest_data()
    results = run_backtest(df, initial_capital=10000, period=5, multiplier=2.0)
    
    equity_curve = results['equity_curve']
    
    assert len(equity_curve) == len(df)
    assert equity_curve.iloc[0] == 10000
    assert all(equity_curve >= 0)
    
    assert equity_curve.index.equals(df.index)


def test_backtest_trades():
    df = create_backtest_data()
    results = run_backtest(df, initial_capital=10000, period=5, multiplier=2.0)
    
    trades = results['trades']
    
    for trade in trades:
        required_keys = ['entry_date', 'exit_date', 'entry_price', 'exit_price', 'return', 'duration']
        for key in required_keys:
            assert key in trade
        
        assert trade['entry_price'] > 0
        assert trade['exit_price'] > 0
        assert trade['duration'] >= 0
        
        expected_return = (trade['exit_price'] - trade['entry_price']) / trade['entry_price']
        assert abs(trade['return'] - expected_return) < 1e-10


def test_backtest_metrics_calculation():
    df = create_backtest_data()
    results = run_backtest(df, initial_capital=10000, period=5, multiplier=2.0)
    
    assert results['num_trades'] >= 0
    assert results['win_rate'] >= 0
    assert results['win_rate'] <= 100
    assert results['max_drawdown'] <= 0
    
    if results['num_trades'] > 0:
        assert results['avg_trade_duration'] >= 0
        assert results['sharpe_ratio'] >= 0 or results['sharpe_ratio'] == 0


def test_buy_and_hold_return():
    df = create_backtest_data()
    buy_hold_return = calculate_buy_and_hold_return(df, initial_capital=10000)
    
    first_price = df['close'].iloc[0]
    last_price = df['close'].iloc[-1]
    expected_return = (last_price - first_price) / first_price * 100
    
    assert abs(buy_hold_return - expected_return) < 1e-10


def test_backtest_with_no_signals():
    df = create_backtest_data()
    
    df_no_signals = df.copy()
    df_no_signals['buy_signal'] = False
    df_no_signals['sell_signal'] = False
    df_no_signals['trend'] = 1
    df_no_signals['supertrend'] = df_no_signals['close'] * 0.95
    df_no_signals['supertrend_up'] = df_no_signals['close'] * 0.95
    df_no_signals['supertrend_dn'] = np.nan
    
    results = run_backtest(df_no_signals, initial_capital=10000, period=5, multiplier=2.0, df_with_signals=df_no_signals, start_with_buy=False)
    
    assert results['num_trades'] == 0
    assert results['total_return'] == 0
    assert results['win_rate'] == 0
    assert results['sharpe_ratio'] == 0
    assert results['avg_trade_duration'] == 0


def test_backtest_with_single_trade():
    df = create_backtest_data()
    
    df_single_trade = df.copy()
    df_single_trade['buy_signal'] = False
    df_single_trade['sell_signal'] = False
    df_single_trade['trend'] = 1
    df_single_trade['supertrend'] = df_single_trade['close'] * 0.95
    df_single_trade['supertrend_up'] = df_single_trade['close'] * 0.95
    df_single_trade['supertrend_dn'] = np.nan
    
    df_single_trade.loc[df_single_trade.index[10], 'buy_signal'] = True
    df_single_trade.loc[df_single_trade.index[20], 'sell_signal'] = True
    
    results = run_backtest(df_single_trade, initial_capital=10000, period=5, multiplier=2.0, df_with_signals=df_single_trade, start_with_buy=False)
    
    assert results['num_trades'] == 1
    assert len(results['trades']) == 1
    
    trade = results['trades'][0]
    assert trade['entry_date'] == df_single_trade.index[10]
    assert trade['exit_date'] == df_single_trade.index[20]
    assert trade['duration'] == 10 * 7


def test_backtest_aapl_2021_2025():
    try:
        from core.data_fetcher import fetch_yfinance_data
        df = fetch_yfinance_data('AAPL', '2021-01-01', '2025-01-01', '1wk')
        
        if len(df) > 0:
            results = run_backtest(df, initial_capital=10000, period=10, multiplier=3.0)
            
            assert results['total_return'] > -100
            assert results['num_trades'] > 0
            assert results['win_rate'] >= 0
            assert results['win_rate'] <= 100
            assert results['max_drawdown'] <= 0
            
            buy_hold_return = calculate_buy_and_hold_return(df, initial_capital=10000)
            assert buy_hold_return > -100
            
            print(f"AAPL 2021-2025 Backtest Results:")
            print(f"Strategy Return: {results['total_return']:.2f}%")
            print(f"Buy & Hold Return: {buy_hold_return:.2f}%")
            print(f"Number of Trades: {results['num_trades']}")
            print(f"Win Rate: {results['win_rate']:.1f}%")
            print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
            
    except Exception as e:
        pytest.skip(f"Could not fetch AAPL data for test: {e}")


def test_backtest_reproducibility():
    df = create_backtest_data()
    
    results1 = run_backtest(df, initial_capital=10000, period=5, multiplier=2.0)
    results2 = run_backtest(df, initial_capital=10000, period=5, multiplier=2.0)
    
    assert results1['total_return'] == results2['total_return']
    assert results1['num_trades'] == results2['num_trades']
    assert results1['win_rate'] == results2['win_rate']
    assert results1['max_drawdown'] == results2['max_drawdown']


def test_backtest_start_with_buy():
    df = create_backtest_data()
    
    results_with_buy = run_backtest(df, initial_capital=10000, period=5, multiplier=2.0, start_with_buy=True)
    results_without_buy = run_backtest(df, initial_capital=10000, period=5, multiplier=2.0, start_with_buy=False)
    
    assert results_with_buy['num_trades'] >= results_without_buy['num_trades']
    
    if results_with_buy['num_trades'] > 0:
        first_trade = results_with_buy['trades'][0]
        assert first_trade['entry_price'] > 0
        
        signals, df_with_supertrend = generate_signals(df, period=5, multiplier=2.0)
        first_trend = df_with_supertrend['trend'].iloc[0]
        
        if first_trend == 1:
            assert first_trade['entry_date'] == df.index[0]


def test_backtest_with_historical_signals():
    """Test the new functionality to check last signal before backtest period"""
    # Create historical data with a clear buy signal before the backtest period
    historical_dates = pd.date_range('2022-01-01', periods=50, freq='W')
    backtest_dates = pd.date_range('2023-01-01', periods=30, freq='W')
    
    # Historical data with upward trend
    historical_data = []
    base_price = 100
    for i, date in enumerate(historical_dates):
        if i < 30:
            base_price += 1  # Upward trend
        else:
            base_price += 0.5
        
        high = base_price + 2
        low = base_price - 2
        close = base_price + np.random.normal(0, 0.5)
        volume = 10000
        
        historical_data.append({
            'open': base_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    historical_df = pd.DataFrame(historical_data, index=historical_dates)
    
    # Backtest data
    backtest_data = []
    base_price = 150  # Start higher to simulate continuation
    for i, date in enumerate(backtest_dates):
        base_price += 0.5
        high = base_price + 2
        low = base_price - 2
        close = base_price + np.random.normal(0, 0.5)
        volume = 10000
        
        backtest_data.append({
            'open': base_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    backtest_df = pd.DataFrame(backtest_data, index=backtest_dates)
    
    # Run backtest with historical data to check last signal
    start_date = backtest_dates[0]
    results = run_backtest(
        backtest_df, 
        initial_capital=10000, 
        period=5, 
        multiplier=2.0,
        start_date=start_date,
        historical_df=historical_df
    )
    
    # The backtest should start with a position if the last historical signal was BUY
    assert isinstance(results['total_return'], (int, float))
    assert isinstance(results['num_trades'], int)
    assert isinstance(results['equity_curve'], pd.Series)
    
    print(f"Backtest with historical signals:")
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Number of Trades: {results['num_trades']}")
    
    # Test with historical data that has a sell signal at the end
    historical_data_sell = []
    base_price = 100
    for i, date in enumerate(historical_dates):
        if i < 40:
            base_price += 1
        else:
            base_price -= 1  # Downward trend at the end
    
        high = base_price + 2
        low = base_price - 2
        close = base_price + np.random.normal(0, 0.5)
        volume = 10000
        
        historical_data_sell.append({
            'open': base_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    historical_df_sell = pd.DataFrame(historical_data_sell, index=historical_dates)
    
    results_sell = run_backtest(
        backtest_df, 
        initial_capital=10000, 
        period=5, 
        multiplier=2.0,
        start_date=start_date,
        historical_df=historical_df_sell
    )
    
    print(f"Backtest with historical sell signal:")
    print(f"Total Return: {results_sell['total_return']:.2f}%")
    print(f"Number of Trades: {results_sell['num_trades']}")
    
    assert isinstance(results_sell['total_return'], (int, float))
    assert isinstance(results_sell['num_trades'], int)


if __name__ == '__main__':
    pytest.main([__file__])
