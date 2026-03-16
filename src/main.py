#!/usr/bin/env python3
"""
Stock Trading Analysis App

This app studies the market and recommends 10 stocks to invest in daily.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import anthropic
from twilio.rest import Client
import os
from datetime import datetime

# Stock lists by region
STOCKS_BY_REGION = {
    'US': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'BABA', 'ORCL'],
    'India': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'HINDUNILVR.NS', 'ITC.NS', 'KOTAKBANK.NS', 'LT.NS', 'BAJFINANCE.NS'],
    'Europe': ['ASML.AS', 'NOVO-B.CO', 'SAP.DE', 'MC.PA', 'OR.PA', 'ABN.AS', 'INGA.AS', 'SAN.PA', 'BAYN.DE', 'BMW.DE'],
    'Asia': ['000001.SS', '000002.SZ', '600036.SS', '000858.SZ', '600519.SS', '002142.SZ', '600276.SS', '000001.SZ', '600000.SS', '002415.SZ']  # China stocks
}

PHONE_EXAMPLE = {
    'US': '+1XXXXXXXXXX',
    'India': '+91XXXXXXXXXX',
    'Europe': '+44XXXXXXXXXX',  # Assuming UK, can adjust
    'Asia': '+86XXXXXXXXXX'  # China
}

def get_stock_data(ticker, period='1y'):
    """Fetch stock data using yfinance"""
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data, stock.info

def analyze_stock(ticker):
    """Basic analysis of the stock"""
    try:
        data, info = get_stock_data(ticker, '1mo')  # Last month for quick analysis
        if data.empty:
            return None
        
        # Calculate returns
        returns = data['Close'].pct_change().dropna()
        if returns.empty:
            return None
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
            'market_cap': info.get('marketCap', 'N/A') if info else 'N/A',
            'pe_ratio': info.get('trailingPE', 'N/A') if info else 'N/A',
            'data': data
        }
    except Exception as e:
        st.warning(f"Error analyzing {ticker}: {str(e)}")
        return None

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

def get_llm_suggestions(recommendations, investment_amount, currency):
    """Use Anthropic Claude for advanced buy/sell suggestions"""
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
    if not api_key:
        return "Anthropic API key not set. Please configure it to get AI suggestions."
    
    prompt = f"""
    You are an expert stock trader AI with deep knowledge of global markets, technical analysis, fundamental analysis, and trading strategies. Based on the following stock data from the last month, provide buy recommendations for today.

    Stocks data:
    {', '.join([f"{s['ticker']}: Price {currency}{s['current_price']:.2f}, Avg Return {s['avg_return']:.2%}, Volatility {s['volatility']:.2%}" for s in recommendations])}

    User has {currency}{investment_amount} to invest daily. Suggest which stocks to buy, how much to allocate to each, and potential returns based on historical trends. Provide reasoning and risk assessment. Note: This is not financial advice; markets are unpredictable.
    """
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error getting AI suggestions: {str(e)}"

def send_sms(message, phone_number):
    """Send SMS using Twilio"""
    account_sid = st.secrets.get("TWILIO_ACCOUNT_SID", os.getenv("TWILIO_ACCOUNT_SID"))
    auth_token = st.secrets.get("TWILIO_AUTH_TOKEN", os.getenv("TWILIO_AUTH_TOKEN"))
    twilio_number = st.secrets.get("TWILIO_PHONE_NUMBER", os.getenv("TWILIO_PHONE_NUMBER"))
    
    if not all([account_sid, auth_token, twilio_number]):
        return "Twilio credentials not set. Please configure them for SMS notifications."
    
    client = Client(account_sid, auth_token)
    try:
        client.messages.create(
            body=message,
            from_=twilio_number,
            to=phone_number
        )
        return "SMS sent successfully!"
    except Exception as e:
        return f"Error sending SMS: {str(e)}"

def main():
    st.title("📈 Stock-ala-carte: AI-Powered Stock Recommendations")
    st.write("Get personalized daily stock picks with AI analysis for selective investing.")
    
    # Sidebar for settings
    st.sidebar.header("Settings")
    region = st.sidebar.selectbox("Select Market Region", list(STOCKS_BY_REGION.keys()))
    currency = CURRENCY_BY_REGION[region]
    investment_amount = st.sidebar.number_input(f"Daily Investment Amount ({currency})", min_value=100, max_value=10000, value=1000, step=100)
    phone_number = st.sidebar.text_input(f"Phone Number for SMS ({PHONE_EXAMPLE[region]})", "")
    enable_notifications = st.sidebar.checkbox("Enable SMS Notifications")
    
    stocks_list = STOCKS_BY_REGION[region]
    
    if st.button("Get AI-Powered Recommendations"):
        with st.spinner("Analyzing market with AI..."):
            recommendations = recommend_stocks(stocks_list)
            if not recommendations:
                st.error("Unable to fetch data for any stocks. Please try again later.")
                return
            ai_suggestions = get_llm_suggestions(recommendations, investment_amount, currency)
        
        st.success(f"AI Recommendations for {region} market ({currency}{investment_amount} investment):")
        
        # Display basic recommendations
        for i, stock in enumerate(recommendations, 1):
            with st.expander(f"{i}. {stock['ticker']} - {currency}{stock['current_price']:.2f}"):
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
                fig.update_layout(xaxis_title="Date", yaxis_title=f"Price ({currency})")
                st.plotly_chart(fig, use_container_width=True)
        
        # AI Suggestions
        st.header("🤖 AI Trading Suggestions")
        st.write(ai_suggestions)
        
        # Send SMS if enabled
        if enable_notifications and phone_number:
            message = f"Daily Stock Recommendations ({datetime.now().strftime('%Y-%m-%d')}):\n{ai_suggestions[:500]}..."  # Truncate for SMS
            result = send_sms(message, phone_number)
            st.info(result)
    
    # Trading Guide Section
    st.header("💡 How to Use This Data for Trading")
    st.markdown("""
    **Understanding the AI Suggestions:**
    - The AI analyzes market trends, news, and historical data to provide personalized buy recommendations.
    - Allocations are based on your investment amount and risk assessment.
    - Potential returns are estimates; actual results vary.
    
    **Trading Strategies:**
    - **Diversification**: Spread investments across recommended stocks.
    - **Risk Management**: Never invest more than you can afford to lose.
    - **Long-term Holding**: Based on AI signals for sustainable growth.
    
    **Where to Trade:**
    - **US Markets**: Robinhood, Fidelity, E*TRADE, TD Ameritrade
    - **India Markets**: Zerodha, Upstox, Groww, Angel One
    - **Europe/Asia**: Interactive Brokers for global access
    
    **Daily Notifications**: Set up your phone number and enable SMS for morning alerts.
    
    **Risk Warning**: This uses AI for insights but is not a substitute for professional advice. Markets can be volatile.
    """)

if __name__ == "__main__":
    main()