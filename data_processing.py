"""
Data cleaning and processing functions.
"""

import pandas as pd
import numpy as np


def clean_iv_data(df, min_tte_days=1, moneyness_range=(0.7, 1.3)):
    """Clean and filter IV data"""
    print(f"\nStarting with {len(df)} options")

    # Remove options with missing IV
    df = df.dropna(subset=['mark_iv'])
    print(f"After removing missing IV: {len(df)}")

    # Remove zero or negative IV
    df = df[df['mark_iv'] > 0]
    print(f"After removing zero/negative IV: {len(df)}")

    # Remove very short-dated options
    df = df[df['tte_days'] >= min_tte_days]
    print(f"After removing options with < {min_tte_days} days: {len(df)}")

    # Remove deep ITM/OTM options
    df = df[(df['moneyness'] >= moneyness_range[0]) &
            (df['moneyness'] <= moneyness_range[1])]
    print(f"After filtering moneyness ({moneyness_range[0]}-{moneyness_range[1]}): {len(df)}")

    # Convert IV from percentage to decimal if needed
    if df['mark_iv'].max() > 10:  # Likely in percentage
        df['mark_iv'] = df['mark_iv'] / 100
        df['bid_iv'] = df['bid_iv'] / 100
        df['ask_iv'] = df['ask_iv'] / 100

    return df


def separate_by_type(df):
    """Separate calls and puts"""
    calls = df[df['option_type'] == 'call'].copy()
    puts = df[df['option_type'] == 'put'].copy()

    print(f"\nCalls: {len(calls)}, Puts: {len(puts)}")
    return calls, puts


def check_call_put_parity(calls, puts, tolerance=0.05):
    """Check for put-call parity violations in IV"""

    merged = calls.merge(
        puts,
        on=['strike', 'expiration'],
        suffixes=('_call', '_put')
    )

    merged['iv_diff'] = abs(merged['mark_iv_call'] - merged['mark_iv_put'])
    violations = merged[merged['iv_diff'] > tolerance]

    print(f"\nCall-Put Parity Check:")
    print(f"Total strike/expiration pairs: {len(merged)}")
    print(f"Violations (|IV_call - IV_put| > {tolerance}): {len(violations)}")

    if len(violations) > 0:
        print("\nTop 5 violations:")
        print(violations.nlargest(5, 'iv_diff')[
            ['strike', 'expiration', 'mark_iv_call', 'mark_iv_put', 'iv_diff']
        ])

    return violations


def summarize_data(df):
    """Print summary statistics of the data"""

    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)

    print(f"\nTotal options: {len(df)}")
    print(f"Unique strikes: {df['strike'].nunique()}")
    print(f"Unique expirations: {df['expiration'].nunique()}")
    print(f"Date range: {df['expiration'].min().date()} to {df['expiration'].max().date()}")

    print(f"\nTime to expiration:")
    print(f"  Min: {df['tte_days'].min():.1f} days")
    print(f"  Max: {df['tte_days'].max():.1f} days")
    print(f"  Mean: {df['tte_days'].mean():.1f} days")

    print(f"\nStrike range:")
    print(f"  Min: ${df['strike'].min():,.0f}")
    print(f"  Max: ${df['strike'].max():,.0f}")
    print(f"  Spot: ${df['underlying_price'].iloc[0]:,.0f}")

    print(f"\nImplied Volatility:")
    print(f"  Min: {df['mark_iv'].min()*100:.1f}%")
    print(f"  Max: {df['mark_iv'].max()*100:.1f}%")
    print(f"  Mean: {df['mark_iv'].mean()*100:.1f}%")
    print(f"  Median: {df['mark_iv'].median()*100:.1f}%")

    print("\n" + "="*60)
