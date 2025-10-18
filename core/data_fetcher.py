import pandas as pd
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import json


def load_config(config_path='config.json'):
    with open(config_path, 'r') as f:
        return json.load(f)


def fetch_yfinance_data(symbol, start_date, end_date, interval='1wk'):
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=start_date, end=end_date, interval=interval)
    
    if data.empty:
        raise ValueError(f"No data found for {symbol} from {start_date} to {end_date}")
    
    data = data.reset_index()
    data.columns = [col.lower() for col in data.columns]
    
    if 'date' in data.columns:
        data = data.rename(columns={'date': 'datetime'})
    
    data = data.set_index('datetime')
    
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Missing required column: {col}")
    
    return data[required_columns]


def fetch_alpaca_data(symbol, start_date, end_date, timeframe='1Week', config_path='config.json'):
    config = load_config(config_path)
    
    api_key = config['alpaca_api_key']
    secret_key = config['alpaca_secret_key']
    
    client = StockHistoricalDataClient(api_key, secret_key)
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    if timeframe == '1Week':
        tf = TimeFrame.Week
    elif timeframe == '1Day':
        tf = TimeFrame.Day
    elif timeframe == '1Hour':
        tf = TimeFrame.Hour
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    
    request_params = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=tf,
        start=start_dt,
        end=end_dt
    )
    
    bars = client.get_stock_bars(request_params)
    
    if not bars.data:
        raise ValueError(f"No data found for {symbol} from {start_date} to {end_date}")
    
    data_list = []
    for symbol_data in bars.data.values():
        for bar in symbol_data:
            data_list.append({
                'datetime': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': int(bar.volume)
            })
    
    df = pd.DataFrame(data_list)
    df = df.set_index('datetime')
    df = df.sort_index()
    
    return df


def get_latest_alpaca_bar(symbol, config_path='config.json'):
    config = load_config(config_path)
    
    api_key = config['alpaca_api_key']
    secret_key = config['alpaca_secret_key']
    
    client = StockHistoricalDataClient(api_key, secret_key)
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    request_params = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TimeFrame.Week,
        start=start_time,
        end=end_time
    )
    
    bars = client.get_stock_bars(request_params)
    
    if not bars.data or not bars.data.get(symbol):
        return None
    
    latest_bar = bars.data[symbol][-1]
    
    return {
        'datetime': latest_bar.timestamp,
        'open': float(latest_bar.open),
        'high': float(latest_bar.high),
        'low': float(latest_bar.low),
        'close': float(latest_bar.close),
        'volume': int(latest_bar.volume)
    }


def get_alpaca_trading_client(config_path='config.json'):
    config = load_config(config_path)
    
    api_key = config['alpaca_api_key']
    secret_key = config['alpaca_secret_key']
    base_url = config['base_url']
    
    return TradingClient(api_key, secret_key, paper=base_url == "https://paper-api.alpaca.markets")
