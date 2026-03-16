#!/usr/bin/env python3
"""
Stock Trading Analysis App

This app studies the market and recommends 10 stocks to invest in daily.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Stock lists by region
STOCKS_BY_REGION = {
    'US': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'BABA', 'ORCL'],
    'India': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'HINDUNILVR.NS', 'ITC.NS', 'KOTAKBANK.NS', 'LT.NS', 'BAJFINANCE.NS'],
    'Europe': ['ASML.AS', 'NOVO-B.CO', 'SAP.DE', 'MC.PA', 'OR.PA', 'ABN.AS', 'INGA.AS', 'SAN.PA', 'BAYN.DE', 'BMW.DE'],
    'Asia': ['000001.SS', '000002.SZ', '600036.SS', '000858.SZ', '600519.SS', '002142.SZ', '600276.SS', '000001.SZ', '600000.SS', '002415.SZ']  # China stocks
}

def get_stock_data(ticker, period='1y'):
    """Fetch stock data using yfinance"""
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data, stock.info

def analyze_stock(ticker):
    """Basic analysis of the stock"""
    data, info = get_stock_data(ticker, '1mo')  # Last month for quick analysis
    if data.empty:
        return None
    
    # Calculate returns
    returns = data['Close'].pct_change().dropna()
    avg_return = returns.mean()
    volatility = returns.std()
    
    # Current price and volume
    current_price = data['Close'].iloc[-1]
    avg_volume = data['Volume'].mean()
    
    return {
        'ticker': ticker,
        'current_price': current_price,
        'avg_return': avg_return,
        'volatility': volatility,
        'avg_volume': avg_volume,
        'market_cap': info.get('marketCap', 'N/A'),
        'pe_ratio': info.get('trailingPE', 'N/A'),
        'data': data
    }

def recommend_stocks(stocks_list):
    """Simple recommendation based on average returns and low volatility"""
    analyses = []
    for ticker in stocks_list:
        analysis = analyze_stock(ticker)
        if analysis:
            analyses.append(analysis)
    
    # Sort by average return descending, then by low volatility
    recommendations = sorted(analyses, key=lambda x: (x['avg_return'], -x['volatility']), reverse=True)
    return recommendations[:10]

def main():
    st.title("📈 Stock Trading Analysis App")
    st.write("Daily recommendations for 10 stocks to invest in. Study the market and make profitable trades.")
    
    # Region selection
    region = st.selectbox("Select Market Region", list(STOCKS_BY_REGION.keys()))
    stocks_list = STOCKS_BY_REGION[region]
    
    if st.button("Get Today's Recommendations"):
        with st.spinner("Analyzing market..."):
            recommendations = recommend_stocks(stocks_list)
        
        st.success(f"Top 10 recommendations for {region} market:")
        
        for i, stock in enumerate(recommendations, 1):
            with st.expander(f"{i}. {stock['ticker']} - ${stock['current_price']:.2f}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Avg Daily Return", f"{stock['avg_return']:.2%}")
                    st.metric("Volatility", f"{stock['volatility']:.2%}")
                    st.metric("Avg Volume", f"{stock['avg_volume']:.0f}")
                with col2:
                    st.metric("Market Cap", f"{stock['market_cap']}")
                    st.metric("P/E Ratio", f"{stock['pe_ratio']}")
                
                # Interactive price chart
                fig = px.line(stock['data'], x=stock['data'].index, y='Close', title=f"{stock['ticker']} Price Trend (Last Month)")
                fig.update_layout(xaxis_title="Date", yaxis_title="Price (USD)")
                st.plotly_chart(fig, use_container_width=True)
    
    # Trading Guide Section
    st.header("💡 How to Use This Data for Trading")
    st.markdown("""
    **Understanding the Metrics:**
    - **Avg Daily Return**: Higher positive values indicate better recent performance.
    - **Volatility**: Lower values suggest more stable stocks, higher for riskier opportunities.
    - **Market Cap & P/E Ratio**: Help assess company size and valuation.
    
    **Trading Strategies:**
    - **Long-term**: Invest in stocks with consistent positive returns and reasonable volatility.
    - **Short-term**: Look for high volatility stocks with recent uptrends for quick trades.
    - **Diversification**: Balance your portfolio across different sectors.
    
    **Where to Trade:**
    - **US Markets**: Robinhood, Fidelity, E*TRADE, TD Ameritrade
    - **India Markets**: Zerodha, Upstox, Groww, Angel One
    - **Europe/Asia**: Local brokers like Interactive Brokers for international access
    
    **Risk Warning**: This is for educational purposes. Always do your own research and consider consulting a financial advisor. Past performance doesn't guarantee future results.
    """)

if __name__ == "__main__":
    main()