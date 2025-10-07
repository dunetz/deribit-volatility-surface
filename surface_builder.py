"""
Volatility surface construction methods.
"""

import numpy as np
from scipy.interpolate import griddata, RBFInterpolator
from scipy.optimize import minimize


def create_simple_surface(df, method='cubic', grid_size=50):
    """Create surface using scipy griddata"""

    # Create points and values for interpolation
    points = df[['log_moneyness', 'tte_years']].values
    values = df['mark_iv'].values

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

    # Interpolate
    iv_surface = griddata(
        points,
        values,
        (log_moneyness_mesh, tte_mesh),
        method=method
    )

    return log_moneyness_mesh, tte_mesh, iv_surface


def create_rbf_surface(df, grid_size=50):
    """Create surface using RBF interpolation"""

    points = df[['log_moneyness', 'tte_years']].values
    values = df['mark_iv'].values

    # Create RBF interpolator
    rbf = RBFInterpolator(points, values, kernel='thin_plate_spline')

    # Create grid
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
    grid_points = np.column_stack([
        log_moneyness_mesh.ravel(),
        tte_mesh.ravel()
    ])

    # Interpolate
    iv_surface = rbf(grid_points).reshape(log_moneyness_mesh.shape)

    return log_moneyness_mesh, tte_mesh, iv_surface


def svi_parametrization(k, a, b, rho, m, sigma):
    """
    SVI formula for variance (IV^2 * T)
    k: log-moneyness
    a, b, rho, m, sigma: SVI parameters
    """
    return a + b * (rho * (k - m) + np.sqrt((k - m)**2 + sigma**2))


def fit_svi_slice(strikes_log, ivs, tte):
    """Fit SVI to a single expiration slice"""

    # Total variance = IV^2 * T
    total_var = (ivs ** 2) * tte

    def objective(params):
        a, b, rho, m, sigma = params
        predicted_var = svi_parametrization(strikes_log, a, b, rho, m, sigma)
        return np.sum((total_var - predicted_var) ** 2)

    # Initial guess
    x0 = [
        np.mean(total_var),
        0.1,
        0.0,
        0.0,
        0.1
    ]

    # Constraints
    bounds = [
        (0, None),
        (0, None),
        (-1, 1),
        (None, None),
        (0.01, None)
    ]

    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')

    return result.x


def create_svi_surface(df, grid_size=50):
    """Create surface by fitting SVI to each expiration"""

    expirations = df['tte_years'].unique()
    svi_params = {}

    print("\nFitting SVI model to each expiration slice...")

    for tte in sorted(expirations):
        slice_df = df[df['tte_years'] == tte]

        if len(slice_df) < 5:
            continue

        params = fit_svi_slice(
            slice_df['log_moneyness'].values,
            slice_df['mark_iv'].values,
            tte
        )
        svi_params[tte] = params

    print(f"Successfully fitted SVI to {len(svi_params)} expiration slices")

    # Create surface from fitted parameters
    log_moneyness_grid = np.linspace(
        df['log_moneyness'].min(),
        df['log_moneyness'].max(),
        grid_size
    )
    tte_grid = sorted(svi_params.keys())

    log_moneyness_mesh, tte_mesh = np.meshgrid(log_moneyness_grid, tte_grid)
    iv_surface = np.zeros_like(log_moneyness_mesh)

    for i, tte in enumerate(tte_grid):
        params = svi_params[tte]
        total_var = svi_parametrization(log_moneyness_grid, *params)
        iv_surface[i, :] = np.sqrt(total_var / tte)

    return log_moneyness_mesh, tte_mesh, iv_surface, svi_params
