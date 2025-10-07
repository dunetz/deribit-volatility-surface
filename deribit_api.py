"""
Deribit API data collection functions.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


def get_index_price(currency='BTC'):
    """Get current index price for the underlying"""
    url = "https://www.deribit.com/api/v2/public/get_index_price"
    params = {'index_name': f'{currency.lower()}_usd'}

    response = requests.get(url, params=params)
    return response.json()['result']['index_price']


def get_dvol_index(currency='BTC'):
    """Get current DVOL (volatility index) value"""
    try:
        url = "https://www.deribit.com/api/v2/public/ticker"
        params = {'instrument_name': f'{currency}VOL'}

        response = requests.get(url, params=params)
        return response.json()['result']['mark_price']
    except:
        return None


def get_all_options_data(currency='BTC'):
    """Get all active options for a currency"""
    url = "https://www.deribit.com/api/v2/public/get_instruments"
    params = {
        'currency': currency,
        'kind': 'option',
        'expired': "false"
    }

    response = requests.get(url, params=params)
    instruments = response.json()['result']

    return instruments


def get_option_iv_data(instruments, underlying_price):
    """Get IV and Greeks for each option"""
    iv_data = []

    print(f"Fetching data for {len(instruments)} options...")

    for i, inst in enumerate(instruments):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(instruments)}")

        ticker_url = "https://www.deribit.com/api/v2/public/ticker"
        params = {'instrument_name': inst['instrument_name']}

        try:
            response = requests.get(ticker_url, params=params)
            ticker = response.json()['result']
            greeks = ticker.get('greeks', {})

            # Calculate time to expiration in years
            expiration_ts = inst['expiration_timestamp'] / 1000
            now = datetime.now().timestamp()
            tte = (expiration_ts - now) / (365.25 * 24 * 3600)

            # Calculate moneyness
            strike = inst['strike']
            moneyness = strike / underlying_price
            log_moneyness = np.log(moneyness)

            iv_data.append({
                'instrument': inst['instrument_name'],
                'strike': strike,
                'expiration': datetime.fromtimestamp(expiration_ts),
                'expiration_timestamp': expiration_ts,
                'tte_days': tte * 365.25,
                'tte_years': tte,
                'option_type': inst['option_type'],
                'mark_iv': ticker.get('mark_iv', np.nan),
                'bid_iv': ticker.get('bid_iv', np.nan),
                'ask_iv': ticker.get('ask_iv', np.nan),
                'moneyness': moneyness,
                'log_moneyness': log_moneyness,
                'delta': greeks.get('delta', np.nan),
                'gamma': greeks.get('gamma', np.nan),
                'theta': greeks.get('theta', np.nan),
                'vega': greeks.get('vega', np.nan),
                'rho': greeks.get('rho', np.nan),
                'volume': ticker.get('stats', {}).get('volume', 0),
                'open_interest': ticker.get('open_interest', 0),
                'underlying_price': underlying_price
            })

        except Exception as e:
            print(f"Error fetching {inst['instrument_name']}: {e}")
            continue

    print("Data collection complete!")
    return pd.DataFrame(iv_data)
