# Stock-ala-carte: AI-Powered Stock Recommendations

This application uses AI (Large Language Models) to study global markets and provide personalized buy recommendations with potential return estimates. It offers interactive charts, region-specific stock selection with dynamic currency support, and SMS notifications for daily alerts.

## Features

- AI-powered buy recommendations using OpenAI GPT-3.5-turbo
- Interactive charts with Plotly
- Region-based stock analysis (US, India, Europe, Asia) with appropriate currencies (USD, INR, EUR, CNY)
- Personalized investment allocations
- SMS notifications via Twilio
- Comprehensive trading guidance
- Error handling for robust operation

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up API keys (see Configuration)
4. Run the app: `streamlit run src/main.py`

## Configuration

Create a `.env` file or set environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for AI suggestions
- `TWILIO_ACCOUNT_SID`: Twilio account SID for SMS
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number

Or use Streamlit secrets for deployment.

## Usage

Run the app and configure your settings in the sidebar. Select region, investment amount (in local currency), and enable notifications. Click "Get AI-Powered Recommendations" for personalized advice.

## Requirements

- Python 3.9+
- Dependencies: streamlit, yfinance, pandas, numpy, matplotlib, scikit-learn, plotly, openai, twilio