"""
Black-Scholes Greeks calculation using smoothed implied volatility surface.
"""

import numpy as np
from scipy.stats import norm
from scipy.interpolate import RegularGridInterpolator


def calculate_d1_d2(S, K, T, r, sigma):
    """
    Calculate d1 and d2 for Black-Scholes formula.

    Parameters:
    -----------
    S : float or array
        Underlying price
    K : float or array
        Strike price
    T : float or array
        Time to expiration (years)
    r : float
        Risk-free rate
    sigma : float or array
        Implied volatility

    Returns:
    --------
    d1, d2 : float or array
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return d1, d2


def black_scholes_price(S, K, T, r, sigma, option_type='call'):
    """
    Calculate Black-Scholes option price.

    Parameters:
    -----------
    S : float or array
        Underlying price
    K : float or array
        Strike price
    T : float or array
        Time to expiration (years)
    r : float
        Risk-free rate
    sigma : float or array
        Implied volatility
    option_type : str
        'call' or 'put'

    Returns:
    --------
    price : float or array
    """
    d1, d2 = calculate_d1_d2(S, K, T, r, sigma)

    if option_type.lower() == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:  # put
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return price


def calculate_delta(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option delta.

    Parameters:
    -----------
    S : float or array
        Underlying price
    K : float or array
        Strike price
    T : float or array
        Time to expiration (years)
    r : float
        Risk-free rate
    sigma : float or array
        Implied volatility
    option_type : str
        'call' or 'put'

    Returns:
    --------
    delta : float or array
    """
    d1, _ = calculate_d1_d2(S, K, T, r, sigma)

    if option_type.lower() == 'call':
        delta = norm.cdf(d1)
    else:  # put
        delta = norm.cdf(d1) - 1

    return delta


def calculate_gamma(S, K, T, r, sigma):
    """
    Calculate option gamma (same for calls and puts).

    Parameters:
    -----------
    S : float or array
        Underlying price
    K : float or array
        Strike price
    T : float or array
        Time to expiration (years)
    r : float
        Risk-free rate
    sigma : float or array
        Implied volatility

    Returns:
    --------
    gamma : float or array
    """
    d1, _ = calculate_d1_d2(S, K, T, r, sigma)
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    return gamma


def calculate_vega(S, K, T, r, sigma):
    """
    Calculate option vega (same for calls and puts).

    Parameters:
    -----------
    S : float or array
        Underlying price
    K : float or array
        Strike price
    T : float or array
        Time to expiration (years)
    r : float
        Risk-free rate
    sigma : float or array
        Implied volatility

    Returns:
    --------
    vega : float or array
        Vega (per 1% change in volatility)
    """
    d1, _ = calculate_d1_d2(S, K, T, r, sigma)
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Divide by 100 for 1% change
    return vega


def calculate_theta(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option theta.

    Parameters:
    -----------
    S : float or array
        Underlying price
    K : float or array
        Strike price
    T : float or array
        Time to expiration (years)
    r : float
        Risk-free rate
    sigma : float or array
        Implied volatility
    option_type : str
        'call' or 'put'

    Returns:
    --------
    theta : float or array
        Theta (per day)
    """
    d1, d2 = calculate_d1_d2(S, K, T, r, sigma)

    term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))

    if option_type.lower() == 'call':
        term2 = -r * K * np.exp(-r * T) * norm.cdf(d2)
        theta = term1 + term2
    else:  # put
        term2 = r * K * np.exp(-r * T) * norm.cdf(-d2)
        theta = term1 + term2

    # Convert to per-day theta
    theta = theta / 365

    return theta


def calculate_rho(S, K, T, r, sigma, option_type='call'):
    """
    Calculate option rho.

    Parameters:
    -----------
    S : float or array
        Underlying price
    K : float or array
        Strike price
    T : float or array
        Time to expiration (years)
    r : float
        Risk-free rate
    sigma : float or array
        Implied volatility
    option_type : str
        'call' or 'put'

    Returns:
    --------
    rho : float or array
        Rho (per 1% change in interest rate)
    """
    _, d2 = calculate_d1_d2(S, K, T, r, sigma)

    if option_type.lower() == 'call':
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:  # put
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

    return rho


def calculate_greeks_from_surface(df, log_moneyness_mesh, tte_mesh, iv_surface,
                                  underlying_price, risk_free_rate=0.0):
    """
    Calculate Greeks for all options using the smoothed IV surface.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with option data (must have 'strike', 'tte_years', 'option_type' columns)
    log_moneyness_mesh : np.ndarray
        Log-moneyness mesh from surface
    tte_mesh : np.ndarray
        Time-to-expiration mesh from surface
    iv_surface : np.ndarray
        Implied volatility surface
    underlying_price : float
        Current underlying price
    risk_free_rate : float
        Risk-free rate (default: 0.0)

    Returns:
    --------
    df : pd.DataFrame
        DataFrame with added columns: bs_delta, bs_gamma, bs_vega, bs_theta, bs_rho
    """
    # Create interpolator for the IV surface
    # Need unique sorted values for interpolator
    log_m_unique = np.unique(log_moneyness_mesh.ravel())
    tte_unique = np.unique(tte_mesh.ravel())

    # Reshape IV surface to match the grid
    # Assume log_moneyness varies along axis 0, tte along axis 1
    n_log_m = len(log_m_unique)
    n_tte = len(tte_unique)

    # Create regular grid IV surface
    iv_grid = np.zeros((n_log_m, n_tte))
    for i, log_m in enumerate(log_m_unique):
        for j, tte in enumerate(tte_unique):
            # Find closest point in mesh
            mask = (log_moneyness_mesh == log_m) & (tte_mesh == tte)
            if mask.any():
                iv_grid[i, j] = iv_surface[mask][0]

    # Create interpolator
    interpolator = RegularGridInterpolator(
        (log_m_unique, tte_unique),
        iv_grid,
        method='linear',
        bounds_error=False,
        fill_value=None  # Use nearest neighbor for extrapolation
    )

    # Calculate log-moneyness for each option
    df['log_moneyness_calc'] = np.log(df['strike'] / underlying_price)

    # Get smoothed IV for each option from the surface
    points = np.column_stack([df['log_moneyness_calc'].values, df['tte_years'].values])

    # Handle points outside the domain by clipping
    points[:, 0] = np.clip(points[:, 0], log_m_unique.min(), log_m_unique.max())
    points[:, 1] = np.clip(points[:, 1], tte_unique.min(), tte_unique.max())

    smoothed_iv = interpolator(points)

    # Replace any NaN values with original mark_iv
    mask_nan = np.isnan(smoothed_iv)
    if mask_nan.any():
        smoothed_iv[mask_nan] = df.loc[mask_nan, 'mark_iv'].values

    df['smoothed_iv'] = smoothed_iv

    # Calculate Greeks using smoothed IV
    S = underlying_price
    K = df['strike'].values
    T = df['tte_years'].values
    sigma = smoothed_iv

    # Filter out very short-dated options (< 1 hour) to avoid numerical issues
    valid_mask = T > (1/24/365)

    # Initialize arrays
    df['bs_delta'] = np.nan
    df['bs_gamma'] = np.nan
    df['bs_vega'] = np.nan
    df['bs_theta'] = np.nan
    df['bs_rho'] = np.nan

    # Calculate for calls
    call_mask = valid_mask & (df['option_type'] == 'call')
    if call_mask.any():
        df.loc[call_mask, 'bs_delta'] = calculate_delta(S, K[call_mask], T[call_mask],
                                                         risk_free_rate, sigma[call_mask], 'call')
        df.loc[call_mask, 'bs_gamma'] = calculate_gamma(S, K[call_mask], T[call_mask],
                                                         risk_free_rate, sigma[call_mask])
        df.loc[call_mask, 'bs_vega'] = calculate_vega(S, K[call_mask], T[call_mask],
                                                       risk_free_rate, sigma[call_mask])
        df.loc[call_mask, 'bs_theta'] = calculate_theta(S, K[call_mask], T[call_mask],
                                                         risk_free_rate, sigma[call_mask], 'call')
        df.loc[call_mask, 'bs_rho'] = calculate_rho(S, K[call_mask], T[call_mask],
                                                     risk_free_rate, sigma[call_mask], 'call')

    # Calculate for puts
    put_mask = valid_mask & (df['option_type'] == 'put')
    if put_mask.any():
        df.loc[put_mask, 'bs_delta'] = calculate_delta(S, K[put_mask], T[put_mask],
                                                        risk_free_rate, sigma[put_mask], 'put')
        df.loc[put_mask, 'bs_gamma'] = calculate_gamma(S, K[put_mask], T[put_mask],
                                                        risk_free_rate, sigma[put_mask])
        df.loc[put_mask, 'bs_vega'] = calculate_vega(S, K[put_mask], T[put_mask],
                                                      risk_free_rate, sigma[put_mask])
        df.loc[put_mask, 'bs_theta'] = calculate_theta(S, K[put_mask], T[put_mask],
                                                        risk_free_rate, sigma[put_mask], 'put')
        df.loc[put_mask, 'bs_rho'] = calculate_rho(S, K[put_mask], T[put_mask],
                                                    risk_free_rate, sigma[put_mask], 'put')

    return df
