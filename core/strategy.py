import pandas as pd
from .supertrend import calculate_supertrend


def generate_signals(df, period=10, multiplier=3.0):
    df_with_supertrend = calculate_supertrend(df, period, multiplier)
    
    signals = []
    
    for i, (timestamp, row) in enumerate(df_with_supertrend.iterrows()):
        if row['buy_signal']:
            signals.append({
                'timestamp': timestamp,
                'signal': 'BUY',
                'price': row['close']
            })
        elif row['sell_signal']:
            signals.append({
                'timestamp': timestamp,
                'signal': 'SELL',
                'price': row['close']
            })
    
    return signals, df_with_supertrend


def get_current_signal(df, period=10, multiplier=3.0):
    df_with_supertrend = calculate_supertrend(df, period, multiplier)
    
    latest_row = df_with_supertrend.iloc[-1]
    
    if latest_row['buy_signal']:
        return 'BUY', latest_row['close']
    elif latest_row['sell_signal']:
        return 'SELL', latest_row['close']
    else:
        return 'HOLD', latest_row['close']


def should_buy(df, period=10, multiplier=3.0):
    signal, price = get_current_signal(df, period, multiplier)
    return signal == 'BUY'


def should_sell(df, period=10, multiplier=3.0):
    signal, price = get_current_signal(df, period, multiplier)
    return signal == 'SELL'
