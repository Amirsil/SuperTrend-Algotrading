import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from .backtest import run_backtest, calculate_buy_and_hold_return, plot_backtest_results


def compare_strategy_vs_buy_hold(df, symbol, initial_capital=10000, period=10, multiplier=3.0):
    strategy_results = run_backtest(df, initial_capital, period, multiplier, start_with_buy=True)
    buy_hold_return = calculate_buy_and_hold_return(df, initial_capital)
    
    comparison_data = {
        'Metric': [
            'Total Return (%)',
            'Max Drawdown (%)',
            'Win Rate (%)',
            'Sharpe Ratio',
            'Number of Trades',
            'Average Trade Duration (days)'
        ],
        'Supertrend Strategy': [
            f"{strategy_results['total_return']:.2f}",
            f"{strategy_results['max_drawdown']:.2f}",
            f"{strategy_results['win_rate']:.1f}",
            f"{strategy_results['sharpe_ratio']:.2f}",
            f"{strategy_results['num_trades']}",
            f"{strategy_results['avg_trade_duration']:.1f}"
        ],
        'Buy & Hold': [
            f"{buy_hold_return:.2f}",
            "N/A",
            "N/A",
            "N/A",
            "1",
            f"{(df.index[-1] - df.index[0]).days:.0f}"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    
    print(f"\n{'='*60}")
    print(f"STRATEGY COMPARISON: {symbol}")
    print(f"{'='*60}")
    print(comparison_df.to_string(index=False))
    print(f"{'='*60}\n")
    
    plot_backtest_results(strategy_results, df, symbol)
    
    return {
        'strategy_results': strategy_results,
        'buy_hold_return': buy_hold_return,
        'comparison_df': comparison_df
    }


def plot_comparison_chart(strategy_results, df, symbol, save_path=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    buy_hold_return = calculate_buy_and_hold_return(df)
    buy_hold_curve = df['close'] / df['close'].iloc[0] * 10000
    
    ax1.plot(strategy_results['equity_curve'].index, strategy_results['equity_curve'], 
             label=f'Supertrend Strategy ({strategy_results["total_return"]:.1f}%)', 
             color='blue', linewidth=2)
    ax1.plot(buy_hold_curve.index, buy_hold_curve, 
             label=f'Buy & Hold ({buy_hold_return:.1f}%)', 
             color='orange', linewidth=2)
    
    ax1.set_title(f'{symbol} - Strategy vs Buy & Hold Performance')
    ax1.set_ylabel('Portfolio Value ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    returns_comparison = pd.DataFrame({
        'Strategy': strategy_results['equity_curve'].pct_change().fillna(0),
        'Buy & Hold': df['close'].pct_change().fillna(0)
    })
    
    ax2.hist(returns_comparison['Strategy'], bins=30, alpha=0.7, 
             label='Strategy Returns', color='blue', density=True)
    ax2.hist(returns_comparison['Buy & Hold'], bins=30, alpha=0.7, 
             label='Buy & Hold Returns', color='orange', density=True)
    
    ax2.set_title('Return Distribution Comparison')
    ax2.set_xlabel('Weekly Returns')
    ax2.set_ylabel('Density')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    plt.show()


def calculate_risk_metrics(strategy_results, df):
    strategy_returns = strategy_results['equity_curve'].pct_change().fillna(0)
    buy_hold_returns = df['close'].pct_change().fillna(0)
    
    strategy_volatility = strategy_returns.std() * np.sqrt(52)
    buy_hold_volatility = buy_hold_returns.std() * np.sqrt(52)
    
    strategy_sharpe = strategy_results['sharpe_ratio']
    buy_hold_sharpe = buy_hold_returns.mean() / buy_hold_returns.std() * np.sqrt(52) if buy_hold_returns.std() > 0 else 0
    
    return {
        'strategy_volatility': strategy_volatility,
        'buy_hold_volatility': buy_hold_volatility,
        'strategy_sharpe': strategy_sharpe,
        'buy_hold_sharpe': buy_hold_sharpe
    }
