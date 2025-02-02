1. Get query from the user
2. Retrieve data from yfinance
3. Match up the query with the correct strategies
4. Execute the strategies
5. Return the result (total returns) and plot

### Note
- We exclude microcaps because they are so volatile that it's not guaranteed to provide a good analysis

### Build instructions
- pyinstaller trading_app.py
- pyinstaller trading_app.spec
- Run the trading_app.exe file within dist directory