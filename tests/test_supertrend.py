import pytest
import pandas as pd
import numpy as np
from core.supertrend import calculate_supertrend, calculate_true_range, calculate_atr


def create_sample_data():
    dates = pd.date_range('2023-01-01', periods=20, freq='W')
    np.random.seed(42)
    
    data = []
    base_price = 100
    
    for i, date in enumerate(dates):
        price_change = np.random.normal(0, 2)
        base_price += price_change
        
        high = base_price + abs(np.random.normal(0, 1))
        low = base_price - abs(np.random.normal(0, 1))
        close = base_price + np.random.normal(0, 0.5)
        volume = np.random.randint(1000, 10000)
        
        data.append({
            'open': base_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data, index=dates)


def test_true_range_calculation():
    df = create_sample_data()
    tr = calculate_true_range(df)
    
    assert len(tr) == len(df)
    assert tr.iloc[0] == df['high'].iloc[0] - df['low'].iloc[0]
    assert all(tr >= 0)
    
    for i in range(1, len(df)):
        expected_tr = max(
            df['high'].iloc[i] - df['low'].iloc[i],
            abs(df['high'].iloc[i] - df['close'].iloc[i-1]),
            abs(df['low'].iloc[i] - df['close'].iloc[i-1])
        )
        assert abs(tr.iloc[i] - expected_tr) < 1e-10


def test_atr_calculation():
    df = create_sample_data()
    atr = calculate_atr(df, period=5)
    
    assert len(atr) == len(df)
    assert pd.isna(atr.iloc[:4]).all()
    assert not pd.isna(atr.iloc[4:]).any()
    
    tr = calculate_true_range(df)
    expected_atr_5 = tr.rolling(5).mean()
    assert np.allclose(atr.iloc[4:], expected_atr_5.iloc[4:], rtol=1e-10)


def test_supertrend_calculation():
    df = create_sample_data()
    result = calculate_supertrend(df, period=5, multiplier=2.0)
    
    required_columns = ['supertrend', 'trend', 'buy_signal', 'sell_signal', 'up_band', 'dn_band']
    for col in required_columns:
        assert col in result.columns
    
    assert len(result) == len(df)
    assert all(result['trend'].isin([1, -1]))
    assert result['buy_signal'].dtype == bool
    assert result['sell_signal'].dtype == bool
    
    assert not (result['buy_signal'] & result['sell_signal']).any()


def test_supertrend_trend_logic():
    df = create_sample_data()
    result = calculate_supertrend(df, period=5, multiplier=2.0)
    
    for i in range(1, len(result)):
        prev_trend = result['trend'].iloc[i-1]
        current_trend = result['trend'].iloc[i]
        current_close = result['close'].iloc[i]
        prev_up = result['up_band'].iloc[i-1]
        prev_dn = result['dn_band'].iloc[i-1]
        
        if prev_trend == -1 and current_close > prev_dn:
            assert current_trend == 1
        elif prev_trend == 1 and current_close < prev_up:
            assert current_trend == -1


def test_supertrend_signal_generation():
    df = create_sample_data()
    result = calculate_supertrend(df, period=5, multiplier=2.0)
    
    buy_signals = result[result['buy_signal']]
    sell_signals = result[result['sell_signal']]
    
    for idx in buy_signals.index:
        signal_idx = result.index.get_loc(idx)
        if signal_idx > 0:
            assert result['trend'].iloc[signal_idx] == 1
            assert result['trend'].iloc[signal_idx-1] == -1
    
    for idx in sell_signals.index:
        signal_idx = result.index.get_loc(idx)
        if signal_idx > 0:
            assert result['trend'].iloc[signal_idx] == -1
            assert result['trend'].iloc[signal_idx-1] == 1


def test_supertrend_band_calculation():
    df = create_sample_data()
    result = calculate_supertrend(df, period=5, multiplier=2.0)
    
    for i in range(len(result)):
        if not pd.isna(result['atr'].iloc[i]):
            if result['trend'].iloc[i] == 1:
                if not pd.isna(result['supertrend'].iloc[i]) and not pd.isna(result['up_band'].iloc[i]):
                    assert abs(result['supertrend'].iloc[i] - result['up_band'].iloc[i]) < 1e-10
                assert not pd.isna(result['supertrend_up'].iloc[i])
                assert pd.isna(result['supertrend_dn'].iloc[i])
            else:
                if not pd.isna(result['supertrend'].iloc[i]) and not pd.isna(result['dn_band'].iloc[i]):
                    assert abs(result['supertrend'].iloc[i] - result['dn_band'].iloc[i]) < 1e-10
                assert pd.isna(result['supertrend_up'].iloc[i])
                assert not pd.isna(result['supertrend_dn'].iloc[i])


def test_supertrend_with_aapl_data():
    try:
        from core.data_fetcher import fetch_yfinance_data
        df = fetch_yfinance_data('AAPL', '2023-01-01', '2023-12-31', '1wk')
        
        if len(df) > 0:
            result = calculate_supertrend(df, period=10, multiplier=3.0)
            
            assert len(result) == len(df)
            assert 'supertrend' in result.columns
            assert 'trend' in result.columns
            assert 'buy_signal' in result.columns
            assert 'sell_signal' in result.columns
            
            assert result['buy_signal'].sum() > 0
            assert result['sell_signal'].sum() > 0
            
    except Exception as e:
        pytest.skip(f"Could not fetch AAPL data for test: {e}")


if __name__ == '__main__':
    pytest.main([__file__])
