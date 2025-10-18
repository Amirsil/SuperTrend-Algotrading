import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from .strategy import generate_signals


def _check_initial_position_from_supertrend(df_with_supertrend):
    """Check if we should start with a position when supertrend line becomes valid"""
    initial_position = False
    initial_position_date = None
    
    # Find the first row where supertrend line is valid (not NaN)
    for i, (timestamp, row) in enumerate(df_with_supertrend.iterrows()):
        if not pd.isna(row['supertrend_up']):
            # Supertrend line is now valid, check if we should start with position
            current_price = row['close']
            supertrend_up = row['supertrend_up']
            trend = row['trend']
            
            if (current_price > supertrend_up) or trend == 1:
                initial_position = True
                initial_position_date = timestamp
                print(f"Supertrend line becomes valid at {timestamp}, price above supertrend up, starting with position")
            else:
                print(f"Supertrend line becomes valid at {timestamp}, price below supertrend up, starting with cash")
            break
    
    return initial_position, initial_position_date


def run_backtest(df, initial_capital=10000, period=10, multiplier=3.0, df_with_signals=None, start_with_buy=True, start_date=None, historical_df=None):
    if df_with_signals is not None:
        df_with_supertrend = df_with_signals
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
    else:
        signals, df_with_supertrend = generate_signals(df, period, multiplier)
    
    # Check if we should start with a position based on last signal before backtest period
    initial_position = False
    initial_position_date = None
    
    if start_date is not None and historical_df is not None:
        # Check for the last signal before start_date using historical data
        try:
            # Generate signals for historical data to find the last signal before start_date
            historical_signals, _ = generate_signals(historical_df, period, multiplier)
            
            # Filter signals that occurred before start_date
            signals_before_start = [s for s in historical_signals if s['timestamp'] < start_date]
            
            if signals_before_start:
                # Get the last signal before start_date
                last_signal = signals_before_start[-1]
                if last_signal['signal'] == 'BUY':
                    initial_position = True
                    initial_position_date = start_date
                    print(f"Last signal before backtest was BUY at {last_signal['timestamp']}, starting with position")
                else:
                    print(f"Last signal before backtest was SELL at {last_signal['timestamp']}, starting with cash")
            else:
                print("No signals found before backtest start date, using fallback logic")
                # Fallback to checking when supertrend line becomes valid
                initial_position, initial_position_date = _check_initial_position_from_supertrend(df_with_supertrend)
        except Exception as e:
            print(f"Error checking historical signals: {e}, using fallback logic")
            # Fallback to checking when supertrend line becomes valid
            initial_position, initial_position_date = _check_initial_position_from_supertrend(df_with_supertrend)
    elif start_with_buy and len(df_with_supertrend) > 0:
        # Check when supertrend line becomes valid and if we should start with position
        initial_position, initial_position_date = _check_initial_position_from_supertrend(df_with_supertrend)
    
    if not signals and not initial_position:
        equity_series = pd.Series([initial_capital] * len(df_with_supertrend), index=df_with_supertrend.index)
        return {
            'total_return': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'sharpe_ratio': 0,
            'num_trades': 0,
            'avg_trade_duration': 0,
            'equity_curve': equity_series,
            'trades': [],
            'df_with_signals': df_with_supertrend
        }
    
    equity = initial_capital
    position = 0
    entry_price = 0
    entry_date = None
    trades = []
    equity_curve = []
    equity_dates = []
    
    # Initialize position when supertrend line becomes valid and condition is met
    if initial_position and len(df_with_supertrend) > 0:
        # Find the row at the initial_position_date
        if initial_position_date is not None:
            position_row = df_with_supertrend.loc[initial_position_date]
            position_price = position_row['close']
            entry_price = position_price
            entry_date = initial_position_date
        else:
            # Fallback to first row
            position_row = df_with_supertrend.iloc[0]
            position_price = position_row['close']
            entry_price = position_price
            entry_date = df_with_supertrend.index[0]
        
        position = equity / position_price
        
        # Add buy signal to the dataframe for visualization
        df_with_supertrend.loc[entry_date, 'buy_signal'] = True
        
        # Add buy signal to the signals array for proper display
        signals.append({
            'timestamp': entry_date,
            'signal': 'BUY',
            'price': position_price
        })
        
        # Update equity to reflect the initial position
        equity = position * position_price
    
    for i, (timestamp, row) in enumerate(df_with_supertrend.iterrows()):
        current_signal = None
        current_price = row['close']
        
        # Skip signal processing for the first row if we already have an initial position
        if not (initial_position and i == 0):
            for signal in signals:
                if signal['timestamp'] == timestamp:
                    current_signal = signal['signal']
                    break
        
        if current_signal == 'BUY' and position == 0:
            position = equity / current_price
            entry_price = current_price
            entry_date = timestamp
            # Don't change equity here - it will be updated below
            
        elif current_signal == 'SELL' and position > 0:
            exit_price = current_price
            trade_return = (exit_price - entry_price) / entry_price
            equity = position * exit_price
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': timestamp,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'return': trade_return,
                'duration': (timestamp - entry_date).days
            })
            
            position = 0
            entry_price = 0
            entry_date = None
        
        # Update equity based on current position
        if position > 0:
            equity = position * current_price
        # If no position, equity remains at current value (cash)
        
        equity_curve.append(equity)
        equity_dates.append(timestamp)
    
    if position > 0:
        final_price = df_with_supertrend.iloc[-1]['close']
        trade_return = (final_price - entry_price) / entry_price
        equity = position * final_price
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': df_with_supertrend.index[-1],
            'entry_price': entry_price,
            'exit_price': final_price,
            'return': trade_return,
            'duration': (df_with_supertrend.index[-1] - entry_date).days
        })
    
    equity_series = pd.Series(equity_curve, index=equity_dates)
    
    total_return = (equity - initial_capital) / initial_capital * 100
    
    peak = equity_series.expanding().max()
    drawdown = (equity_series - peak) / peak * 100
    max_drawdown = drawdown.min()
    
    if trades:
        winning_trades = [t for t in trades if t['return'] > 0]
        win_rate = len(winning_trades) / len(trades) * 100
        avg_trade_duration = np.mean([t['duration'] for t in trades])
        
        returns = [t['return'] for t in trades]
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(52)
        else:
            sharpe_ratio = 0
    else:
        win_rate = 0
        avg_trade_duration = 0
        sharpe_ratio = 0
    
    return {
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'sharpe_ratio': sharpe_ratio,
        'num_trades': len(trades),
        'avg_trade_duration': avg_trade_duration,
        'equity_curve': equity_series,
        'trades': trades,
        'df_with_signals': df_with_supertrend
    }


def calculate_buy_and_hold_return(df, initial_capital=10000):
    first_price = df.iloc[0]['close']
    last_price = df.iloc[-1]['close']
    
    shares = initial_capital / first_price
    final_value = shares * last_price
    
    return (final_value - initial_capital) / initial_capital * 100


def plot_backtest_results(results, df, symbol, save_path=None):
    fig, axes = plt.subplots(3, 1, figsize=(15, 12))
    
    df_with_signals = results['df_with_signals']
    
    axes[0].plot(df.index, df['close'], label='Price', color='black', linewidth=1)
    axes[0].plot(df_with_signals.index, df_with_signals['supertrend_up'], 
                 label='Supertrend Up', color='green', alpha=0.7, linewidth=2)
    axes[0].plot(df_with_signals.index, df_with_signals['supertrend_dn'], 
                 label='Supertrend Down', color='red', alpha=0.7, linewidth=2)
    
    buy_signals = df_with_signals[df_with_signals['buy_signal']]
    sell_signals = df_with_signals[df_with_signals['sell_signal']]
    
    axes[0].scatter(buy_signals.index, buy_signals['close'], 
                    color='green', marker='^', s=100, label='Buy Signal', zorder=5)
    axes[0].scatter(sell_signals.index, sell_signals['close'], 
                    color='red', marker='v', s=100, label='Sell Signal', zorder=5)
    
    axes[0].set_title(f'{symbol} - Price Chart with Supertrend Signals')
    axes[0].set_ylabel('Price ($)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    buy_hold_return = calculate_buy_and_hold_return(df)
    buy_hold_curve = df['close'] / df['close'].iloc[0] * 10000
    
    axes[1].plot(results['equity_curve'].index, results['equity_curve'], 
                 label=f'Supertrend Strategy ({results["total_return"]:.1f}%)', 
                 color='blue', linewidth=2)
    axes[1].plot(buy_hold_curve.index, buy_hold_curve, 
                 label=f'Buy & Hold ({buy_hold_return:.1f}%)', 
                 color='orange', linewidth=2)
    
    axes[1].set_title('Equity Curve Comparison')
    axes[1].set_ylabel('Portfolio Value ($)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    peak = results['equity_curve'].expanding().max()
    drawdown = (results['equity_curve'] - peak) / peak * 100
    
    axes[2].fill_between(drawdown.index, drawdown, 0, 
                         color='red', alpha=0.3, label='Drawdown')
    axes[2].plot(drawdown.index, drawdown, color='red', linewidth=1)
    axes[2].set_title('Drawdown')
    axes[2].set_ylabel('Drawdown (%)')
    axes[2].set_xlabel('Date')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()


def print_backtest_summary(results, symbol):
    print(f"\n{'='*50}")
    print(f"BACKTEST RESULTS FOR {symbol}")
    print(f"{'='*50}")
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"Win Rate: {results['win_rate']:.1f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Number of Trades: {results['num_trades']}")
    print(f"Average Trade Duration: {results['avg_trade_duration']:.1f} days")
    print(f"{'='*50}\n")
