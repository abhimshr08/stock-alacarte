# Stock-ala-carte: AI-Powered Stock Recommendations

This application uses AI (Large Language Models) to study global markets and provide personalized buy recommendations with potential return estimates. It offers interactive charts, region-specific stock selection with dynamic currency support, and SMS notifications for daily alerts.

## Features

- AI-powered buy recommendations using OpenAI GPT-3.5-turbo
- **Live Trading Integration with Zerodha** for actionable execution
- Automatic position size calculation based on investment amount
- **One-click trade execution** directly from recommendations
- Interactive charts with Plotly
- Region-based stock analysis (US, India, Europe, Asia) with appropriate currencies (USD, INR, EUR, CNY)
- SMS notifications via Twilio
- Comprehensive trading guidance
- Error handling for robust operation
- Real-time holdings tracking from Zerodha

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up API keys (see Configuration)
4. Run the app: `streamlit run src/main.py`

## Configuration

Create a `.env` file or set environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for AI suggestions
- `ZERODHA_API_KEY`: Zerodha Kite API key (for live trading)
- `ZERODHA_ACCESS_TOKEN`: Zerodha access token (generate from Kite)
- `TWILIO_ACCOUNT_SID`: Twilio account SID for SMS
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number

Or use Streamlit secrets for deployment.

## Usage

Run the app and configure your settings in the sidebar. Select region, investment amount (in local currency), and enable notifications. Click "Get AI-Powered Recommendations" for personalized advice.

## Requirements

- Python 3.9+
- Dependencies: streamlit, yfinance, pandas, numpy, matplotlib, scikit-learn, plotly, openai, twilio, kiteconnect, python-dotenv

## Zerodha Live Trading Setup

To enable live trading with Zerodha:

1. **Create Zerodha Account**: Sign up at [zerodha.com](https://zerodha.com)
2. **Get API Keys**:
   - Login to Zerodha: https://kite.zerodha.com
   - Go to Settings → API Consents
   - Create a new application and get your API key
3. **Generate Access Token**:
   - Request an access token through the Kite Connect login process
   - Token expires after a specific duration; regenerate as needed
4. **Set Environment Variables**:
   ```bash
   export ZERODHA_API_KEY=your_api_key
   export ZERODHA_ACCESS_TOKEN=your_access_token
   ```

### How to Trade:
1. Start the app and enable "Enable Live Trading (Zerodha)"
2. Get AI recommendations by clicking "Get AI-Powered Recommendations"
3. For each stock, view the calculated position size (shares to buy)
4. Click "🛒 Buy" button to execute the trade immediately
5. View your holdings in the "📊 Your Holdings" section