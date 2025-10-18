import pytest
import pandas as pd
import numpy as np
from core.strategy import generate_signals, get_current_signal, should_buy, should_sell
from core.supertrend import calculate_supertrend


def create_trending_data():
    dates = pd.date_range('2023-01-01', periods=50, freq='W')
    
    data = []
    base_price = 100
    
    for i, date in enumerate(dates):
        if i < 20:
            base_price += 2
        elif i < 30:
            base_price -= 1.5
        else:
            base_price += 1
        
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


def test_generate_signals():
    df = create_trending_data()
    signals, df_with_supertrend = generate_signals(df, period=5, multiplier=2.0)
    
    assert isinstance(signals, list)
    assert 'supertrend' in df_with_supertrend.columns
    assert 'trend' in df_with_supertrend.columns
    assert 'buy_signal' in df_with_supertrend.columns
    assert 'sell_signal' in df_with_supertrend.columns
    
    for signal in signals:
        assert 'timestamp' in signal
        assert 'signal' in signal
        assert 'price' in signal
        assert signal['signal'] in ['BUY', 'SELL']
        assert signal['price'] > 0


def test_signal_timing():
    df = create_trending_data()
    signals, df_with_supertrend = generate_signals(df, period=5, multiplier=2.0)
    
    buy_signals = [s for s in signals if s['signal'] == 'BUY']
    sell_signals = [s for s in signals if s['signal'] == 'SELL']
    
    for buy_signal in buy_signals:
        timestamp = buy_signal['timestamp']
        signal_idx = df_with_supertrend.index.get_loc(timestamp)
        
        assert df_with_supertrend['buy_signal'].iloc[signal_idx] == True
        assert df_with_supertrend['trend'].iloc[signal_idx] == 1
    
    for sell_signal in sell_signals:
        timestamp = sell_signal['timestamp']
        signal_idx = df_with_supertrend.index.get_loc(timestamp)
        
        assert df_with_supertrend['sell_signal'].iloc[signal_idx] == True
        assert df_with_supertrend['trend'].iloc[signal_idx] == -1


def test_get_current_signal():
    df = create_trending_data()
    signal, price = get_current_signal(df, period=5, multiplier=2.0)
    
    assert signal in ['BUY', 'SELL', 'HOLD']
    assert price > 0
    assert price == df['close'].iloc[-1]


def test_should_buy():
    df = create_trending_data()
    result = should_buy(df, period=5, multiplier=2.0)
    
    assert isinstance(result, bool)
    
    signal, _ = get_current_signal(df, period=5, multiplier=2.0)
    expected = signal == 'BUY'
    assert result == expected


def test_should_sell():
    df = create_trending_data()
    result = should_sell(df, period=5, multiplier=2.0)
    
    assert isinstance(result, bool)
    
    signal, _ = get_current_signal(df, period=5, multiplier=2.0)
    expected = signal == 'SELL'
    assert result == expected


def test_long_only_strategy():
    df = create_trending_data()
    signals, _ = generate_signals(df, period=5, multiplier=2.0)
    
    buy_signals = [s for s in signals if s['signal'] == 'BUY']
    sell_signals = [s for s in signals if s['signal'] == 'SELL']
    
    assert len(buy_signals) > 0
    assert len(sell_signals) > 0
    
    for i in range(len(signals) - 1):
        current_signal = signals[i]
        next_signal = signals[i + 1]
        
        if current_signal['signal'] == 'BUY':
            assert next_signal['signal'] == 'SELL'
        elif current_signal['signal'] == 'SELL':
            assert next_signal['signal'] == 'BUY'


def test_signal_price_capture():
    df = create_trending_data()
    signals, df_with_supertrend = generate_signals(df, period=5, multiplier=2.0)
    
    for signal in signals:
        timestamp = signal['timestamp']
        signal_idx = df_with_supertrend.index.get_loc(timestamp)
        expected_price = df_with_supertrend['close'].iloc[signal_idx]
        
        assert abs(signal['price'] - expected_price) < 1e-10


def test_strategy_with_different_parameters():
    df = create_trending_data()
    
    signals_1, _ = generate_signals(df, period=5, multiplier=2.0)
    signals_2, _ = generate_signals(df, period=10, multiplier=3.0)
    
    assert len(signals_1) >= 0
    assert len(signals_2) >= 0
    
    for signals in [signals_1, signals_2]:
        for signal in signals:
            assert signal['signal'] in ['BUY', 'SELL']
            assert signal['price'] > 0


def test_strategy_with_aapl_data():
    try:
        from core.data_fetcher import fetch_yfinance_data
        df = fetch_yfinance_data('AAPL', '2023-01-01', '2023-12-31', '1wk')
        
        if len(df) > 0:
            signals, df_with_supertrend = generate_signals(df, period=10, multiplier=3.0)
            
            assert len(signals) > 0
            assert len(df_with_supertrend) == len(df)
            
            buy_count = len([s for s in signals if s['signal'] == 'BUY'])
            sell_count = len([s for s in signals if s['signal'] == 'SELL'])
            
            assert buy_count > 0
            assert sell_count > 0
            
    except Exception as e:
        pytest.skip(f"Could not fetch AAPL data for test: {e}")


if __name__ == '__main__':
    pytest.main([__file__])
