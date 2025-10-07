"""
Visualization functions for volatility surfaces.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata, RegularGridInterpolator
from datetime import timedelta

plt.style.use('seaborn-v0_8-darkgrid')


def plot_volatility_surface(log_moneyness_mesh, tte_mesh, iv_surface,
                            underlying_price, title='Implied Volatility Surface',
                            save_path=None):
    """Plot 3D volatility surface"""

    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_subplot(111, projection='3d')

    strike_mesh = underlying_price * np.exp(log_moneyness_mesh)

    surf = ax.plot_surface(
        strike_mesh,
        tte_mesh * 365,
        iv_surface * 100,
        cmap='viridis',
        alpha=0.8,
        edgecolor='none'
    )

    ax.set_xlabel('Strike Price ($)', fontsize=12, labelpad=10)
    ax.set_ylabel('Days to Expiration', fontsize=12, labelpad=10)
    ax.set_zlabel('Implied Volatility (%)', fontsize=12, labelpad=10)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, pad=0.1)

    ax.view_init(elev=25, azim=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()

    return fig, ax


def plot_volatility_smile(df, expirations=None, save_path=None):
    """Plot volatility smile for specific expirations"""

    if expirations is None:
        all_exp = sorted(df['tte_days'].unique())
        if len(all_exp) >= 4:
            indices = [0, len(all_exp)//3, 2*len(all_exp)//3, -1]
        else:
            indices = range(len(all_exp))
        expirations = [all_exp[i] for i in indices]

    fig, ax = plt.subplots(figsize=(14, 8))

    colors = plt.cm.plasma(np.linspace(0, 0.9, len(expirations)))

    for tte_days, color in zip(expirations, colors):
        slice_df = df[np.abs(df['tte_days'] - tte_days) < 1].copy()
        slice_df = slice_df.sort_values('moneyness')

        ax.plot(
            slice_df['moneyness'],
            slice_df['mark_iv'] * 100,
            marker='o',
            label=f'{tte_days:.0f} days',
            linewidth=2.5,
            markersize=7,
            color=color
        )

    ax.set_xlabel('Moneyness (Strike/Spot)', fontsize=13)
    ax.set_ylabel('Implied Volatility (%)', fontsize=13)
    ax.set_title('Volatility Smile by Expiration', fontsize=16, fontweight='bold')
    ax.axvline(x=1.0, color='red', linestyle='--', alpha=0.5, label='ATM', linewidth=2)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()

    return fig, ax


def plot_term_structure(df, moneyness_levels=[0.9, 1.0, 1.1], save_path=None):
    """Plot volatility term structure"""

    fig, ax = plt.subplots(figsize=(14, 8))

    colors = ['blue', 'green', 'red']

    for m, color in zip(moneyness_levels, colors):
        subset = df[np.abs(df['moneyness'] - m) < 0.03].copy()
        subset = subset.sort_values('tte_days')

        label = f'Moneyness = {m:.1f}'
        if m == 1.0:
            label += ' (ATM)'
        elif m < 1.0:
            label += ' (OTM Put/ITM Call)'
        else:
            label += ' (ITM Put/OTM Call)'

        ax.plot(
            subset['tte_days'],
            subset['mark_iv'] * 100,
            marker='o',
            label=label,
            linewidth=2.5,
            markersize=7,
            color=color
        )

    ax.set_xlabel('Days to Expiration', fontsize=13)
    ax.set_ylabel('Implied Volatility (%)', fontsize=13)
    ax.set_title('Volatility Term Structure', fontsize=16, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()

    return fig, ax


def plot_heatmap(log_moneyness_mesh, tte_mesh, iv_surface, underlying_price, save_path=None):
    """Plot volatility surface as a heatmap"""

    fig, ax = plt.subplots(figsize=(14, 8))

    strike_mesh = underlying_price * np.exp(log_moneyness_mesh)

    c = ax.contourf(
        strike_mesh,
        tte_mesh * 365,
        iv_surface * 100,
        levels=20,
        cmap='RdYlGn_r'
    )

    ax.set_xlabel('Strike Price ($)', fontsize=13)
    ax.set_ylabel('Days to Expiration', fontsize=13)
    ax.set_title('Implied Volatility Heatmap', fontsize=16, fontweight='bold')

    cbar = fig.colorbar(c, ax=ax)
    cbar.set_label('Implied Volatility (%)', fontsize=12)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()

    return fig, ax


def plot_surface_comparison(snapshot1, snapshot2, title1='Surface 1', title2='Surface 2', save_path=None):
    """Compare two volatility surfaces side by side"""

    fig = plt.figure(figsize=(20, 8))

    # First surface
    ax1 = fig.add_subplot(121, projection='3d')
    log_m1, tte1, iv1 = snapshot1.surface_data
    strike1 = snapshot1.underlying_price * np.exp(log_m1)

    surf1 = ax1.plot_surface(strike1, tte1 * 365, iv1 * 100,
                             cmap='viridis', alpha=0.8, edgecolor='none')
    ax1.set_xlabel('Strike ($)', fontsize=11)
    ax1.set_ylabel('Days to Exp', fontsize=11)
    ax1.set_zlabel('IV (%)', fontsize=11)
    ax1.set_title(f"{title1}\n{snapshot1.timestamp.strftime('%Y-%m-%d %H:%M')}\nSpot: ${snapshot1.underlying_price:,.0f}",
                  fontsize=12, fontweight='bold')
    ax1.view_init(elev=25, azim=45)

    # Second surface
    ax2 = fig.add_subplot(122, projection='3d')
    log_m2, tte2, iv2 = snapshot2.surface_data
    strike2 = snapshot2.underlying_price * np.exp(log_m2)

    surf2 = ax2.plot_surface(strike2, tte2 * 365, iv2 * 100,
                             cmap='viridis', alpha=0.8, edgecolor='none')
    ax2.set_xlabel('Strike ($)', fontsize=11)
    ax2.set_ylabel('Days to Exp', fontsize=11)
    ax2.set_zlabel('IV (%)', fontsize=11)
    ax2.set_title(f"{title2}\n{snapshot2.timestamp.strftime('%Y-%m-%d %H:%M')}\nSpot: ${snapshot2.underlying_price:,.0f}",
                  fontsize=12, fontweight='bold')
    ax2.view_init(elev=25, azim=45)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()

    return fig


def plot_difference_surface(snapshot1, snapshot2, title='IV Change', save_path=None):
    """Plot the difference between two surfaces"""

    # Need to interpolate to common grid
    log_m1, tte1, iv1 = snapshot1.surface_data
    log_m2, tte2, iv2 = snapshot2.surface_data

    # Use snapshot2's grid
    # Interpolate snapshot1 to snapshot2's grid
    interp1 = RegularGridInterpolator(
        (tte1[:, 0], log_m1[0, :]),
        iv1,
        bounds_error=False,
        fill_value=None
    )

    # Create mesh from snapshot2
    points = np.array([tte2.ravel(), log_m2.ravel()]).T
    iv1_interp = interp1(points).reshape(iv2.shape)

    # Calculate difference
    iv_diff = (iv2 - iv1_interp) * 100  # Convert to percentage points

    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_subplot(111, projection='3d')

    strike2 = snapshot2.underlying_price * np.exp(log_m2)

    # Use diverging colormap
    surf = ax.plot_surface(strike2, tte2 * 365, iv_diff,
                          cmap='RdBu_r', alpha=0.8, edgecolor='none',
                          vmin=-np.nanpercentile(np.abs(iv_diff), 95),
                          vmax=np.nanpercentile(np.abs(iv_diff), 95))

    ax.set_xlabel('Strike ($)', fontsize=12)
    ax.set_ylabel('Days to Expiration', fontsize=12)
    ax.set_zlabel('IV Change (pp)', fontsize=12)
    ax.set_title(f"{title}\n{snapshot1.timestamp.strftime('%Y-%m-%d')} → {snapshot2.timestamp.strftime('%Y-%m-%d')}",
                 fontsize=14, fontweight='bold')
    ax.view_init(elev=25, azim=45)

    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='IV Change (pp)')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()

    return fig


def plot_metrics_timeseries(history, save_path=None):
    """Plot time series of key volatility metrics"""

    df = history.get_metrics_timeseries()

    if len(df) == 0:
        print("No data to plot")
        return None

    fig, axes = plt.subplots(3, 2, figsize=(16, 12))

    # ATM volatilities
    ax = axes[0, 0]
    for col in ['atm_iv_7d', 'atm_iv_30d', 'atm_iv_90d', 'atm_iv_180d']:
        if col in df.columns:
            ax.plot(df.index, df[col] * 100, marker='o', label=col, linewidth=2)
    ax.set_ylabel('IV (%)', fontsize=11)
    ax.set_title('ATM Implied Volatility by Tenor', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # DVOL vs ATM 30d
    ax = axes[0, 1]
    if 'dvol' in df.columns and 'atm_iv_30d' in df.columns:
        ax.plot(df.index, df['dvol'], marker='o', label='DVOL', linewidth=2)
        ax.plot(df.index, df['atm_iv_30d'] * 100, marker='s', label='ATM 30d', linewidth=2)
        ax.set_ylabel('Volatility (%)', fontsize=11)
        ax.set_title('DVOL vs ATM 30d IV', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

    # 25-delta skew
    ax = axes[1, 0]
    if 'skew_25d' in df.columns:
        ax.plot(df.index, df['skew_25d'] * 100, marker='o', color='purple', linewidth=2)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_ylabel('Skew (pp)', fontsize=11)
        ax.set_title('25-Delta Put-Call Skew', fontweight='bold')
        ax.grid(True, alpha=0.3)

    # Term structure slope
    ax = axes[1, 1]
    if 'term_structure_slope' in df.columns:
        ax.plot(df.index, df['term_structure_slope'] * 100, marker='o', color='green', linewidth=2)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_ylabel('Slope (pp)', fontsize=11)
        ax.set_title('Term Structure Slope (90d - 30d)', fontweight='bold')
        ax.grid(True, alpha=0.3)

    # Underlying price
    ax = axes[2, 0]
    if 'underlying_price' in df.columns:
        ax.plot(df.index, df['underlying_price'], marker='o', color='orange', linewidth=2)
        ax.set_ylabel('Price ($)', fontsize=11)
        ax.set_title('Underlying Price', fontweight='bold')
        ax.grid(True, alpha=0.3)

    # IV dispersion (std)
    ax = axes[2, 1]
    if 'iv_std' in df.columns:
        ax.plot(df.index, df['iv_std'] * 100, marker='o', color='red', linewidth=2)
        ax.set_ylabel('Std Dev (pp)', fontsize=11)
        ax.set_title('IV Surface Dispersion', fontweight='bold')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()

    return fig


def plot_greeks_surface_3d(df, underlying_price, greek='delta', save_path=None, grid_size=50):
    """
    Plot 3D surface of Greeks (delta, gamma, vega, theta, rho).
    """
    if greek not in df.columns:
        print(f"Greek '{greek}' not available in DataFrame")
        return None, None

    # Create points and values for interpolation
    points = df[['log_moneyness', 'tte_years']].values
    values = df[greek].values

    # Create regular grid
    log_moneyness_grid = np.linspace(
        df['log_moneyness'].min(),
        df['log_moneyness'].max(),
        grid_size
    )
    tte_grid = np.linspace(
        df['tte_years'].min(),
        df['tte_years'].max(),
        grid_size
    )

    log_moneyness_mesh, tte_mesh = np.meshgrid(log_moneyness_grid, tte_grid)

    # Interpolate the greek values
    greek_surface = griddata(
        points,
        values,
        (log_moneyness_mesh, tte_mesh),
        method='cubic'
    )

    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_subplot(111, projection='3d')

    strike_mesh = underlying_price * np.exp(log_moneyness_mesh)

    surf = ax.plot_surface(
        strike_mesh,
        tte_mesh * 365,
        greek_surface,
        cmap='viridis',
        alpha=0.8,
        edgecolor='none'
    )

    ax.set_xlabel('Strike Price ($)', fontsize=12, labelpad=10)
    ax.set_ylabel('Days to Expiration', fontsize=12, labelpad=10)
    ax.set_zlabel(greek.capitalize(), fontsize=12, labelpad=10)
    ax.set_title(f'{greek.capitalize()} Surface', fontsize=16, fontweight='bold', pad=20)

    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, pad=0.1)

    ax.view_init(elev=25, azim=45)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")
    else:
        plt.show()

    return fig, ax
