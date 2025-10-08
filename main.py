#!/usr/bin/env python3
"""
Main CLI script for building Deribit volatility surfaces.

Usage:
    python main.py --currency BTC --method rbf --save --save-raw
    python main.py --currency ETH --method svi --no-viz
"""

import argparse
from datetime import datetime
import sys

from deribit_api import get_index_price, get_dvol_index, get_all_options_data, get_option_iv_data
from data_processing import clean_iv_data, separate_by_type, check_call_put_parity, summarize_data
from surface_builder import create_simple_surface, create_rbf_surface, create_svi_surface
from metrics import calculate_surface_metrics
from snapshot import SurfaceSnapshot, SurfaceHistory
from visualizations import (plot_volatility_surface, plot_volatility_smile,
                           plot_term_structure, plot_heatmap, plot_greeks_surface_3d)
from greeks import calculate_greeks_from_surface


def build_volatility_surface(currency='BTC', method='rbf', save_snapshot=False,
                             save_raw=False, show_viz=True, output_dir='vol_surface_history',
                             save_plots=True, plots_dir='plots'):
    """
    Complete workflow to build volatility surface

    Parameters:
    -----------
    currency : str
        'BTC' or 'ETH'
    method : str
        'simple', 'rbf', or 'svi'
    save_snapshot : bool
        Whether to save this snapshot to disk
    save_raw : bool
        Whether to save raw options data (requires save_snapshot=True)
    show_viz : bool
        Whether to display visualizations
    output_dir : str
        Directory to save snapshots
    save_plots : bool
        Whether to save plots to files (default: True)
    plots_dir : str
        Directory to save plots (default: plots)
    """

    print("="*60)
    print(f"BUILDING {currency} VOLATILITY SURFACE")
    print("="*60)

    # Get current price and DVOL
    try:
        underlying_price = get_index_price(currency)
        dvol = get_dvol_index(currency)
    except Exception as e:
        print(f"Error fetching market data: {e}")
        sys.exit(1)

    print(f"\nCurrent {currency} price: ${underlying_price:,.2f}")
    if dvol:
        print(f"Current DVOL: {dvol:.2f}%")

    # Get all options
    try:
        instruments = get_all_options_data(currency)
        print(f"Found {len(instruments)} option instruments")
    except Exception as e:
        print(f"Error fetching options instruments: {e}")
        sys.exit(1)

    # Get IV data
    try:
        df = get_option_iv_data(instruments, underlying_price)
    except Exception as e:
        print(f"Error fetching IV data: {e}")
        sys.exit(1)

    # Clean data
    df = clean_iv_data(df)

    # Summarize
    summarize_data(df)

    # Separate calls and puts
    calls, puts = separate_by_type(df)

    # Check call-put parity
    violations = check_call_put_parity(calls, puts)

    # Calculate metrics
    metrics = calculate_surface_metrics(df, underlying_price)

    # Create surface using specified method
    print(f"\nBuilding surface using {method.upper()} method...")

    try:
        if method == 'simple':
            log_m_mesh, tte_mesh, iv_surf = create_simple_surface(calls, method='cubic')
            svi_params = None
        elif method == 'rbf':
            log_m_mesh, tte_mesh, iv_surf = create_rbf_surface(calls)
            svi_params = None
        elif method == 'svi':
            log_m_mesh, tte_mesh, iv_surf, svi_params = create_svi_surface(calls)
        else:
            raise ValueError("Method must be 'simple', 'rbf', or 'svi'")
    except Exception as e:
        print(f"Error building surface: {e}")
        sys.exit(1)

    # Calculate Greeks from smoothed surface
    print("\nCalculating Greeks from smoothed IV surface...")
    try:
        df = calculate_greeks_from_surface(
            df, log_m_mesh, tte_mesh, iv_surf,
            underlying_price, risk_free_rate=0.0
        )
        print("Greeks calculated successfully")
    except Exception as e:
        print(f"Warning: Error calculating Greeks: {e}")
        # Continue without Greeks

    # Create snapshot
    snapshot = SurfaceSnapshot(
        timestamp=datetime.now(),
        currency=currency,
        underlying_price=underlying_price,
        dvol=dvol,
        surface_data=(log_m_mesh, tte_mesh, iv_surf),
        raw_options=df,
        metrics=metrics
    )

    # Save if requested
    if save_snapshot:
        history = SurfaceHistory(storage_dir=output_dir)
        history.save_snapshot(snapshot, save_raw=save_raw)

    # Create visualizations
    if show_viz or save_plots:
        print("\nCreating visualizations...")

        # Setup plot directory if saving
        save_path_base = None
        if save_plots:
            from pathlib import Path
            plots_path = Path(plots_dir)
            plots_path.mkdir(exist_ok=True)

            # Create timestamped subdirectory
            timestamp_str = snapshot.timestamp.strftime('%Y%m%d_%H%M%S')
            plot_subdir = plots_path / f"{currency}_{timestamp_str}"
            plot_subdir.mkdir(exist_ok=True)
            print(f"Saving plots to: {plot_subdir}")
            save_path_base = plot_subdir

        # 3D Volatility Surface
        save_path = str(save_path_base / f"{currency}_volatility_surface_3d_{method}.png") if save_plots else None
        plot_volatility_surface(
            log_m_mesh, tte_mesh, iv_surf,
            underlying_price,
            f'{currency} Implied Volatility Surface ({method.upper()})',
            save_path=save_path
        )

        # Volatility Smile
        save_path = str(save_path_base / f"{currency}_volatility_smile.png") if save_plots else None
        plot_volatility_smile(calls, save_path=save_path)

        # Term Structure
        save_path = str(save_path_base / f"{currency}_term_structure.png") if save_plots else None
        plot_term_structure(calls, save_path=save_path)

        # Heatmap
        save_path = str(save_path_base / f"{currency}_volatility_heatmap.png") if save_plots else None
        plot_heatmap(log_m_mesh, tte_mesh, iv_surf, underlying_price, save_path=save_path)

        # Plot Greek surfaces - use calculated Greeks (bs_*) if available, otherwise Deribit data
        greek_mapping = {
            'delta': 'bs_delta' if 'bs_delta' in df.columns else 'delta',
            'gamma': 'bs_gamma' if 'bs_gamma' in df.columns else 'gamma',
            'vega': 'bs_vega' if 'bs_vega' in df.columns else 'vega'
        }

        for greek_name, greek_col in greek_mapping.items():
            if greek_col in df.columns and df[greek_col].notna().any():
                save_path = str(save_path_base / f"{currency}_{greek_name}_surface_3d.png") if save_plots else None
                plot_greeks_surface_3d(df, underlying_price, greek=greek_col, save_path=save_path)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)

    results = {
        'snapshot': snapshot,
        'df': df,
        'calls': calls,
        'puts': puts,
        'surface': (log_m_mesh, tte_mesh, iv_surf),
        'underlying_price': underlying_price,
        'violations': violations,
        'metrics': metrics
    }

    if svi_params is not None:
        results['svi_params'] = svi_params

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Build Deribit volatility surface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --currency BTC --method rbf --save --save-raw
  python main.py --currency ETH --method svi
  python main.py --currency BTC --no-viz --save
  python main.py --currency BTC --plots-dir my_plots
  python main.py --currency BTC --no-save-plots  # Skip saving plots
        """
    )

    parser.add_argument(
        '--currency',
        type=str,
        default='BTC',
        choices=['BTC', 'ETH'],
        help='Cryptocurrency to analyze (default: BTC)'
    )

    parser.add_argument(
        '--method',
        type=str,
        default='rbf',
        choices=['simple', 'rbf', 'svi'],
        help='Surface interpolation method (default: rbf)'
    )

    parser.add_argument(
        '--save',
        action='store_true',
        help='Save snapshot to disk'
    )

    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='Save raw options data (requires --save)'
    )

    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Skip visualization display'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='vol_surface_history',
        help='Directory to save snapshots (default: vol_surface_history)'
    )

    parser.add_argument(
        '--no-save-plots',
        action='store_true',
        help='Do not save plots to files (plots are saved by default)'
    )

    parser.add_argument(
        '--plots-dir',
        type=str,
        default='plots',
        help='Directory to save plots (default: plots)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.save_raw and not args.save:
        print("Warning: --save-raw requires --save. Enabling --save.")
        args.save = True

    # Run the analysis
    try:
        results = build_volatility_surface(
            currency=args.currency,
            method=args.method,
            save_snapshot=args.save,
            save_raw=args.save_raw,
            show_viz=not args.no_viz,
            output_dir=args.output_dir,
            save_plots=not args.no_save_plots,
            plots_dir=args.plots_dir
        )
        return 0
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
