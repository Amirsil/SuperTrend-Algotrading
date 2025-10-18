import time
import json
import pandas as pd
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from .data_fetcher import get_alpaca_trading_client, get_latest_alpaca_bar, load_config
from .strategy import get_current_signal


class AlpacaTrader:
    def __init__(self, config_path='config.json'):
        self.config = load_config(config_path)
        self.client = get_alpaca_trading_client(config_path)
        self.symbol = self.config.get('symbol', 'AAPL')
        self.position_size_pct = self.config.get('position_size_pct', 100)
        self.atr_period = self.config.get('atr_period', 10)
        self.atr_multiplier = self.config.get('atr_multiplier', 3.0)
        self.check_interval = self.config.get('check_interval_seconds', 3600)
        
    def get_account_info(self):
        account = self.client.get_account()
        return {
            'equity': float(account.equity),
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value)
        }
    
    def get_current_position(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
            
        try:
            position = self.client.get_open_position(symbol)
            return {
                'symbol': position.symbol,
                'qty': float(position.qty),
                'side': position.side,
                'market_value': float(position.market_value),
                'cost_basis': float(position.cost_basis),
                'unrealized_pl': float(position.unrealized_pl),
                'unrealized_plpc': float(position.unrealized_plpc)
            }
        except:
            return None
    
    def calculate_position_size(self, price):
        account_info = self.get_account_info()
        equity = account_info['equity']
        position_value = equity * (self.position_size_pct / 100)
        return int(position_value / price)
    
    def place_market_order(self, symbol, side, qty):
        try:
            market_order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            
            order = self.client.submit_order(order_data=market_order_data)
            return {
                'success': True,
                'order_id': order.id,
                'symbol': order.symbol,
                'side': order.side,
                'qty': order.qty,
                'status': order.status
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_buy_signal(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
            
        latest_bar = get_latest_alpaca_bar(symbol, 'config.json')
        if not latest_bar:
            return {'success': False, 'error': 'Could not fetch latest price data'}
        
        current_price = latest_bar['close']
        qty = self.calculate_position_size(current_price)
        
        if qty <= 0:
            return {'success': False, 'error': 'Insufficient buying power'}
        
        result = self.place_market_order(symbol, OrderSide.BUY, qty)
        if result['success']:
            print(f"BUY order placed: {qty} shares of {symbol} at ~${current_price:.2f}")
        
        return result
    
    def execute_sell_signal(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
            
        position = self.get_current_position(symbol)
        if not position:
            return {'success': False, 'error': 'No position to sell'}
        
        qty = abs(int(position['qty']))
        result = self.place_market_order(symbol, OrderSide.SELL, qty)
        
        if result['success']:
            print(f"SELL order placed: {qty} shares of {symbol}")
        
        return result
    
    def check_and_execute_signals(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
            
        try:
            latest_bar = get_latest_alpaca_bar(symbol, 'config.json')
            if not latest_bar:
                print(f"Could not fetch latest data for {symbol}")
                return
            
            df = pd.DataFrame([latest_bar]).set_index('datetime')
            
            signal, price = get_current_signal(df, self.atr_period, self.atr_multiplier)
            current_position = self.get_current_position(symbol)
            
            print(f"Signal: {signal}, Price: ${price:.2f}, Position: {current_position['qty'] if current_position else 0}")
            
            if signal == 'BUY' and (not current_position or current_position['qty'] <= 0):
                self.execute_buy_signal(symbol)
            elif signal == 'SELL' and current_position and current_position['qty'] > 0:
                self.execute_sell_signal(symbol)
            else:
                print("No action needed")
                
        except Exception as e:
            print(f"Error checking signals: {e}")
    
    def run_trading_loop(self, symbol=None, check_interval=None):
        if symbol is None:
            symbol = self.symbol
        if check_interval is None:
            check_interval = self.check_interval
            
        print(f"Starting trading loop for {symbol}")
        print(f"Check interval: {check_interval} seconds")
        print(f"Position size: {self.position_size_pct}% of equity")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.check_and_execute_signals(symbol)
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\nTrading loop stopped by user")
        except Exception as e:
            print(f"Trading loop error: {e}")
    
    def get_trading_summary(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
            
        account_info = self.get_account_info()
        position = self.get_current_position(symbol)
        
        print(f"\n{'='*50}")
        print(f"TRADING SUMMARY FOR {symbol}")
        print(f"{'='*50}")
        print(f"Account Equity: ${account_info['equity']:,.2f}")
        print(f"Cash: ${account_info['cash']:,.2f}")
        print(f"Buying Power: ${account_info['buying_power']:,.2f}")
        
        if position:
            print(f"Position: {position['qty']} shares")
            print(f"Market Value: ${position['market_value']:,.2f}")
            print(f"Unrealized P&L: ${position['unrealized_pl']:,.2f} ({position['unrealized_plpc']:.2%})")
        else:
            print("No current position")
        
        print(f"{'='*50}\n")
