#!/usr/bin/env python3
"""
Stock Trading Analysis App

This app studies the market and recommends 10 stocks to invest in daily.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import openai
from twilio.rest import Client
from kiteconnect import KiteConnect
import os
from datetime import datetime

# Stock lists by region
STOCKS_BY_REGION = {
    'US': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'BABA', 'ORCL'],
    'India': ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'HINDUNILVR.NS', 'ITC.NS', 'KOTAKBANK.NS', 'LT.NS', 'BAJFINANCE.NS'],
    'Europe': ['ASML.AS', 'NOVO-B.CO', 'SAP.DE', 'MC.PA', 'OR.PA', 'ABN.AS', 'INGA.AS', 'SAN.PA', 'BAYN.DE', 'BMW.DE'],
    'Asia': ['000001.SS', '000002.SZ', '600036.SS', '000858.SZ', '600519.SS', '002142.SZ', '600276.SS', '000001.SZ', '600000.SS', '002415.SZ']  # China stocks
}

CURRENCY_BY_REGION = {
    'US': 'USD',
    'India': 'INR',
    'Europe': 'EUR',
    'Asia': 'CNY'
}

PHONE_EXAMPLE = {
    'US': '+1XXXXXXXXXX',
    'India': '+91XXXXXXXXXX',
    'Europe': '+44XXXXXXXXXX',  # Assuming UK, can adjust
    'Asia': '+86XXXXXXXXXX'  # China
}

def get_stock_data(ticker, period='1y'):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        info = stock.info
        return data, info
    except Exception as e:
        st.warning(f"Failed to fetch data for {ticker}: {str(e)}")
        return pd.DataFrame(), {}

def analyze_stock(ticker):
    """Basic analysis of the stock"""
    try:
        # Try 1 week first for Indian stocks, fallback to 1 month
        data, info = get_stock_data(ticker, '1wk')
        if data.empty:
            data, info = get_stock_data(ticker, '1mo')
        if data.empty:
            return None
        
        # Calculate returns
        returns = data['Close'].pct_change().dropna()
        if returns.empty or len(returns) < 2:
            return None
        avg_return = returns.mean()
        volatility = returns.std()
        
        # Current price and volume
        current_price = data['Close'].iloc[-1]
        avg_volume = data['Volume'].mean() if 'Volume' in data.columns else 0
        
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
    """Use OpenAI GPT for advanced buy/sell suggestions"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except (FileNotFoundError, KeyError):
            pass
    
    if not api_key:
        return "OpenAI API key not set. Please set the OPENAI_API_KEY environment variable or add it to Streamlit secrets."
    
    openai.api_key = api_key
    
    prompt = f"""
    You are an expert stock trader AI with deep knowledge of global markets, technical analysis, fundamental analysis, and trading strategies. Based on the following stock data from the last month, provide buy recommendations for today.

    Stocks data:
    {', '.join([f"{s['ticker']}: Price {currency}{s['current_price']:.2f}, Avg Return {s['avg_return']:.2%}, Volatility {s['volatility']:.2%}" for s in recommendations])}

    User has {currency}{investment_amount} to invest daily. Suggest which stocks to buy, how much to allocate to each, and potential returns based on historical trends. Provide reasoning and risk assessment. Note: This is not financial advice; markets are unpredictable.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        return response.choices[0].message.content
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

def initialize_kite():
    """Initialize Zerodha Kite connection"""
    api_key = os.getenv("ZERODHA_API_KEY")
    if not api_key:
        return None, "Zerodha API key not set. Please set ZERODHA_API_KEY environment variable."
    
    try:
        kite = KiteConnect(api_key=api_key)
        # Check if access token is available
        access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        if access_token:
            kite.set_access_token(access_token)
            return kite, None
        else:
            return None, "Zerodha access token not set. Please authenticate first."
    except Exception as e:
        return None, f"Error initializing Kite: {str(e)}"

def calculate_position_size(stock_price, investment_amount, currency):
    """Calculate number of shares to buy"""
    if stock_price <= 0:
        return 0
    try:
        quantity = int(investment_amount / stock_price)
        return max(1, quantity)  # Minimum 1 share
    except Exception as e:
        st.warning(f"Error calculating position size: {str(e)}")
        return 0

def place_trade_order(kite, ticker, quantity, price, order_type="BUY", exchange="NSE"):
    """Place a buy/sell order on Zerodha"""
    if not kite:
        return False, "Kite connection not established"
    
    try:
        # Place order
        order_id = kite.place_order(
            tradingsymbol=ticker,
            exchange=exchange,
            transaction_type=order_type,
            quantity=quantity,
            order_type=kite.ORDER_TYPE_MARKET,  # Market order for immediate execution
            price=0  # Market orders don't use price
        )
        return True, f"Order placed successfully! Order ID: {order_id}"
    except Exception as e:
        return False, f"Error placing order: {str(e)}"

def get_holdings(kite):
    """Get current holdings from Zerodha"""
    if not kite:
        return pd.DataFrame(), "Kite connection not established"
    
    try:
        holdings = kite.holdings()
        df = pd.DataFrame(holdings)
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"Error fetching holdings: {str(e)}"

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
    
    # Zerodha Trading Integration
    st.sidebar.header("🔐 Zerodha Trading")
    enable_trading = st.sidebar.checkbox("Enable Live Trading (Zerodha)")
    kite = None
    if enable_trading:
        st.sidebar.info("⚠️ Ensure ZERODHA_API_KEY and ZERODHA_ACCESS_TOKEN are set in environment variables")
        kite, error = initialize_kite()
        if error:
            st.sidebar.error(error)
        else:
            st.sidebar.success("✅ Zerodha Connected")
    
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
                
                # Trading Execution (Zerodha)
                if enable_trading and kite:
                    st.divider()
                    st.subheader("🎯 Execute Trade")
                    quantity = calculate_position_size(stock['current_price'], investment_amount, currency)
                    st.write(f"**Quantity to Buy:** {quantity} shares @ {currency}{stock['current_price']:.2f}")
                    st.write(f"**Total Investment:** {currency}{quantity * stock['current_price']:.2f}")
                    
                    # Determine exchange based on region
                    exchange = "NSE" if region == "India" else "NSE"
                    if region == "US":
                        exchange = "MCX"
                    
                    col_buy, col_skip = st.columns(2)
                    with col_buy:
                        if st.button(f"🛒 Buy {quantity} shares", key=f"buy_{stock['ticker']}"):
                            success, message = place_trade_order(kite, stock['ticker'], quantity, stock['current_price'], "BUY", exchange)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                    with col_skip:
                        if st.button(f"⏭️ Skip", key=f"skip_{stock['ticker']}"):
                            st.info(f"Skipped {stock['ticker']}")
        
        # AI Suggestions
        st.header("🤖 AI Trading Suggestions")
        st.write(ai_suggestions)
        
        # Send SMS if enabled
        if enable_notifications and phone_number:
            message = f"Daily Stock Recommendations ({datetime.now().strftime('%Y-%m-%d')}):\n{ai_suggestions[:500]}..."  # Truncate for SMS
            result = send_sms(message, phone_number)
            st.info(result)
    
    # Show Holdings if Zerodha is connected
    if enable_trading and kite:
        st.header("📊 Your Holdings (Zerodha)")
        holdings_df, error = get_holdings(kite)
        if error:
            st.error(error)
        elif not holdings_df.empty:
            # Display key columns from holdings
            display_columns = ['tradingsymbol', 'quantity', 'price', 'last_price']
            available_columns = [col for col in display_columns if col in holdings_df.columns]
            st.dataframe(holdings_df[available_columns], use_container_width=True)
        else:
            st.info("No holdings currently")
    
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