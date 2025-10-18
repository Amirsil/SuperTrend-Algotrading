install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

backtest:
	python main.py --backtest AAPL 2021-01-01 2025-01-01

compare:
	python main.py --compare AAPL 2021-01-01 2025-01-01

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete