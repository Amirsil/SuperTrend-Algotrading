import pandas as pd
import numpy as np


def calculate_true_range(df):
    high_low = df['high'] - df['low']
    high_close_prev = np.abs(df['high'] - df['close'].shift(1))
    low_close_prev = np.abs(df['low'] - df['close'].shift(1))
    
    return pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)


def calculate_atr(df, period=10):
    tr = calculate_true_range(df)
    return tr.rolling(window=period).mean()


def calculate_supertrend(df, period=10, multiplier=3.0):
    df = df.copy()
    
    df['tr'] = calculate_true_range(df)
    df['atr'] = calculate_atr(df, period)
    
    hl2 = (df['high'] + df['low']) / 2
    
    up_band = hl2 - (multiplier * df['atr'])
    dn_band = hl2 + (multiplier * df['atr'])
    
    up_band_final = pd.Series(index=df.index, dtype=float)
    dn_band_final = pd.Series(index=df.index, dtype=float)
    
    for i in range(len(df)):
        if i == 0:
            up_band_final.iloc[i] = up_band.iloc[i]
            dn_band_final.iloc[i] = dn_band.iloc[i]
        else:
            prev_up = up_band_final.iloc[i-1]
            prev_dn = dn_band_final.iloc[i-1]
            prev_close = df['close'].iloc[i-1]
            
            if prev_close > prev_up:
                up_band_final.iloc[i] = max(up_band.iloc[i], prev_up)
            else:
                up_band_final.iloc[i] = up_band.iloc[i]
                
            if prev_close < prev_dn:
                dn_band_final.iloc[i] = min(dn_band.iloc[i], prev_dn)
            else:
                dn_band_final.iloc[i] = dn_band.iloc[i]
    
    trend = pd.Series(index=df.index, dtype=int)
    
    if len(df) > 0:
        first_close = df['close'].iloc[0]
        first_up = up_band_final.iloc[0]
        first_dn = dn_band_final.iloc[0]
        
        if first_close > first_up:
            trend.iloc[0] = 1
        elif first_close < first_dn:
            trend.iloc[0] = -1
        else:
            trend.iloc[0] = 1
    
    for i in range(1, len(df)):
        prev_trend = trend.iloc[i-1]
        current_close = df['close'].iloc[i]
        prev_up = up_band_final.iloc[i-1]
        prev_dn = dn_band_final.iloc[i-1]
        
        if prev_trend == -1 and current_close > prev_dn:
            trend.iloc[i] = 1
        elif prev_trend == 1 and current_close < prev_up:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = prev_trend
    
    supertrend = pd.Series(index=df.index, dtype=float)
    for i in range(len(df)):
        if trend.iloc[i] == 1:
            supertrend.iloc[i] = up_band_final.iloc[i]
        else:
            supertrend.iloc[i] = dn_band_final.iloc[i]
    
    supertrend_up = pd.Series(index=df.index, dtype=float)
    supertrend_dn = pd.Series(index=df.index, dtype=float)
    
    for i in range(len(df)):
        if trend.iloc[i] == 1:
            supertrend_up.iloc[i] = up_band_final.iloc[i]
            supertrend_dn.iloc[i] = np.nan
        else:
            supertrend_up.iloc[i] = np.nan
            supertrend_dn.iloc[i] = dn_band_final.iloc[i]
    
    # Generate buy/sell signals based on trend changes
    buy_signal = (trend == 1) & (trend.shift(1) == -1)
    sell_signal = (trend == -1) & (trend.shift(1) == 1)
    
    # Note: Initial position is now handled in the backtest algorithm based on price vs supertrend up line
    # No need to generate initial buy signal here
    
    df['supertrend'] = supertrend
    df['trend'] = trend
    df['buy_signal'] = buy_signal
    df['sell_signal'] = sell_signal
    df['up_band'] = up_band_final
    df['dn_band'] = dn_band_final
    df['supertrend_up'] = supertrend_up
    df['supertrend_dn'] = supertrend_dn
    
    return df
