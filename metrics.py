"""
Surface metrics calculation functions.
"""

import numpy as np


def calculate_surface_metrics(df, underlying_price):
    """Calculate key metrics from the volatility surface"""

    metrics = {}

    # ATM volatilities for different tenors
    for tenor in [7, 30, 60, 90, 180]:
        tenor_df = df[(df['tte_days'] >= tenor - 5) & (df['tte_days'] <= tenor + 5)]
        atm_df = tenor_df[(tenor_df['moneyness'] >= 0.98) & (tenor_df['moneyness'] <= 1.02)]

        if len(atm_df) > 0:
            metrics[f'atm_iv_{tenor}d'] = atm_df['mark_iv'].mean()
        else:
            metrics[f'atm_iv_{tenor}d'] = np.nan

    # 25-delta skew (typical measure)
    # Approximate 25-delta as ~10% OTM for both puts and calls
    put_25d = df[(df['option_type'] == 'put') &
                 (df['moneyness'] >= 0.88) & (df['moneyness'] <= 0.92) &
                 (df['tte_days'] >= 25) & (df['tte_days'] <= 35)]

    call_25d = df[(df['option_type'] == 'call') &
                  (df['moneyness'] >= 1.08) & (df['moneyness'] <= 1.12) &
                  (df['tte_days'] >= 25) & (df['tte_days'] <= 35)]

    if len(put_25d) > 0 and len(call_25d) > 0:
        metrics['skew_25d'] = put_25d['mark_iv'].mean() - call_25d['mark_iv'].mean()
    else:
        metrics['skew_25d'] = np.nan

    # Term structure slope (30d vs 90d ATM)
    if not np.isnan(metrics.get('atm_iv_30d', np.nan)) and not np.isnan(metrics.get('atm_iv_90d', np.nan)):
        metrics['term_structure_slope'] = metrics['atm_iv_90d'] - metrics['atm_iv_30d']
    else:
        metrics['term_structure_slope'] = np.nan

    # Overall surface statistics
    metrics['iv_mean'] = df['mark_iv'].mean()
    metrics['iv_median'] = df['mark_iv'].median()
    metrics['iv_std'] = df['mark_iv'].std()
    metrics['iv_min'] = df['mark_iv'].min()
    metrics['iv_max'] = df['mark_iv'].max()

    return metrics
