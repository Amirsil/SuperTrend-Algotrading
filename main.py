#!/usr/bin/env python3

import argparse
import sys
from datetime import datetime
from core.data_fetcher import fetch_yfinance_data, fetch_alpaca_data
from core.backtest import run_backtest, print_backtest_summary, plot_backtest_results
from core.compare import compare_strategy_vs_buy_hold
from core.alpaca_trader import AlpacaTrader


def parse_arguments():
    parser = argparse.ArgumentParser(description='Supertrend Trading Bot')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest')
    backtest_parser.add_argument('symbol', help='Stock symbol (e.g., AAPL)')
    backtest_parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('end_date', help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--config', default='config.json', help='Config file path')
    backtest_parser.add_argument('--period', type=int, default=10, help='ATR period')
    backtest_parser.add_argument('--multiplier', type=float, default=3.0, help='ATR multiplier')
    backtest_parser.add_argument('--capital', type=int, default=10000, help='Initial capital')
    backtest_parser.add_argument('--plot', action='store_true', help='Show plots')
    
    compare_parser = subparsers.add_parser('compare', help='Compare strategy vs buy-and-hold')
    compare_parser.add_argument('symbol', help='Stock symbol (e.g., AAPL)')
    compare_parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
    compare_parser.add_argument('end_date', help='End date (YYYY-MM-DD)')
    compare_parser.add_argument('--config', default='config.json', help='Config file path')
    compare_parser.add_argument('--period', type=int, default=10, help='ATR period')
    compare_parser.add_argument('--multiplier', type=float, default=3.0, help='ATR multiplier')
    compare_parser.add_argument('--capital', type=int, default=10000, help='Initial capital')
    
    paper_parser = subparsers.add_parser('paper', help='Run paper trading')
    paper_parser.add_argument('symbol', help='Stock symbol (e.g., AAPL)')
    paper_parser.add_argument('--config', default='config.json', help='Config file path')
    paper_parser.add_argument('--interval', type=int, default=3600, help='Check interval in seconds')
    
    live_parser = subparsers.add_parser('live', help='Run live trading')
    live_parser.add_argument('symbol', help='Stock symbol (e.g., AAPL)')
    live_parser.add_argument('--config', default='config.json', help='Config file path')
    live_parser.add_argument('--interval', type=int, default=3600, help='Check interval in seconds')
    
    return parser.parse_args()


def run_backtest_command(args):
    print(f"Running backtest for {args.symbol} from {args.start_date} to {args.end_date}")
    
    try:
        df = fetch_yfinance_data(args.symbol, args.start_date, args.end_date, '1wk')
        print(f"Loaded {len(df)} weekly bars")
        
        results = run_backtest(df, args.capital, args.period, args.multiplier, start_with_buy=True)
        print_backtest_summary(results, args.symbol)
        
        if args.plot:
            plot_backtest_results(results, df, args.symbol)
            
    except Exception as e:
        print(f"Error running backtest: {e}")
        sys.exit(1)


def run_compare_command(args):
    print(f"Comparing strategy vs buy-and-hold for {args.symbol} from {args.start_date} to {args.end_date}")
    
    try:
        df = fetch_yfinance_data(args.symbol, args.start_date, args.end_date, '1wk')
        print(f"Loaded {len(df)} weekly bars")
        
        compare_strategy_vs_buy_hold(df, args.symbol, args.capital, args.period, args.multiplier)
            
    except Exception as e:
        print(f"Error running comparison: {e}")
        sys.exit(1)


def run_paper_trading(args):
    print(f"Starting paper trading for {args.symbol}")
    
    try:
        trader = AlpacaTrader(args.config)
        trader.symbol = args.symbol
        trader.check_interval = args.interval
        
        trader.get_trading_summary(args.symbol)
        trader.run_trading_loop(args.symbol, args.interval)
        
    except Exception as e:
        print(f"Error running paper trading: {e}")
        sys.exit(1)


def run_live_trading(args):
    print(f"Starting LIVE trading for {args.symbol}")
    print("WARNING: This will use real money!")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Live trading cancelled")
        return
    
    try:
        trader = AlpacaTrader(args.config)
        trader.symbol = args.symbol
        trader.check_interval = args.interval
        
        trader.get_trading_summary(args.symbol)
        trader.run_trading_loop(args.symbol, args.interval)
        
    except Exception as e:
        print(f"Error running live trading: {e}")
        sys.exit(1)


def main():
    args = parse_arguments()
    
    if not args.command:
        print("Please specify a command. Use --help for available options.")
        sys.exit(1)
    
    if args.command == 'backtest':
        run_backtest_command(args)
    elif args.command == 'compare':
        run_compare_command(args)
    elif args.command == 'paper':
        run_paper_trading(args)
    elif args.command == 'live':
        run_live_trading(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
