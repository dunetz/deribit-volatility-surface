#!/usr/bin/env python3
"""
CLI script for analyzing historical volatility surfaces.

Usage:
    python analyze_history.py --list
    python analyze_history.py --compare --dates 2025-10-01 2025-10-07
    python analyze_history.py --timeseries
    python analyze_history.py --event-study --date 2025-10-05 --days-before 3 --days-after 3
"""

import argparse
from datetime import datetime, timedelta
import sys
import matplotlib.pyplot as plt

from snapshot import SurfaceHistory
from visualizations import (plot_surface_comparison, plot_difference_surface,
                           plot_metrics_timeseries)


def list_snapshots(history_dir='vol_surface_history', currency=None):
    """List all available snapshots"""
    history = SurfaceHistory(storage_dir=history_dir)
    snapshots = history.load_all_snapshots(currency=currency)

    if not snapshots:
        print("No snapshots found")
        return

    print(f"\nFound {len(snapshots)} snapshot(s):")
    print("-" * 80)
    print(f"{'Date':<20} {'Currency':<10} {'Price':<15} {'DVOL':<10}")
    print("-" * 80)

    for snap in snapshots:
        dvol_str = f"{snap.dvol:.2f}%" if snap.dvol else "N/A"
        print(f"{snap.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<20} "
              f"{snap.currency:<10} "
              f"${snap.underlying_price:>12,.2f} "
              f"{dvol_str:<10}")

    print("-" * 80)


def compare_snapshots(date1_str, date2_str, history_dir='vol_surface_history',
                     currency=None, save_plots=False):
    """Compare two snapshots"""
    history = SurfaceHistory(storage_dir=history_dir)
    snapshots = history.load_all_snapshots(currency=currency)

    if len(snapshots) < 2:
        print("Need at least 2 snapshots for comparison")
        return

    # Parse dates
    try:
        date1 = datetime.fromisoformat(date1_str)
        date2 = datetime.fromisoformat(date2_str)
    except:
        print(f"Error parsing dates. Use format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
        return

    # Find closest snapshots
    snap1 = history.get_snapshot_by_date(date1)
    snap2 = history.get_snapshot_by_date(date2)

    if not snap1 or not snap2:
        print("Could not find snapshots for the specified dates")
        return

    print(f"\nComparing snapshots:")
    print(f"  Snapshot 1: {snap1.timestamp}")
    print(f"  Snapshot 2: {snap2.timestamp}")
    print(f"\nPrice change: ${snap1.underlying_price:,.2f} → ${snap2.underlying_price:,.2f} "
          f"({((snap2.underlying_price/snap1.underlying_price - 1) * 100):+.2f}%)")

    # Plot comparison
    save_path1 = 'comparison.png' if save_plots else None
    save_path2 = 'difference.png' if save_plots else None

    plot_surface_comparison(snap1, snap2,
                          title1=snap1.timestamp.strftime('%Y-%m-%d'),
                          title2=snap2.timestamp.strftime('%Y-%m-%d'),
                          save_path=save_path1)

    plot_difference_surface(snap1, snap2, save_path=save_path2)


def plot_timeseries(history_dir='vol_surface_history', currency=None, save_plots=False):
    """Plot time series of metrics"""
    history = SurfaceHistory(storage_dir=history_dir)
    snapshots = history.load_all_snapshots(currency=currency)

    if len(snapshots) < 2:
        print("Need at least 2 snapshots for time series analysis")
        return

    print(f"\nAnalyzing {len(snapshots)} snapshots...")

    save_path = 'timeseries.png' if save_plots else None
    plot_metrics_timeseries(history, save_path=save_path)


def event_study(event_date_str, days_before=5, days_after=5,
               history_dir='vol_surface_history', currency=None, save_plots=False):
    """Analyze surface changes around a specific event"""
    history = SurfaceHistory(storage_dir=history_dir)
    snapshots = history.load_all_snapshots(currency=currency)

    if len(snapshots) < 2:
        print("Need at least 2 snapshots for event study")
        return

    # Parse event date
    try:
        event_date = datetime.fromisoformat(event_date_str)
    except:
        print(f"Error parsing date. Use format: YYYY-MM-DD")
        return

    # Find snapshots in the window
    start_date = event_date - timedelta(days=days_before)
    end_date = event_date + timedelta(days=days_after)

    event_snapshots = [s for s in snapshots
                      if start_date <= s.timestamp <= end_date]

    if len(event_snapshots) < 2:
        print(f"Not enough snapshots around {event_date}")
        return

    # Find closest before and after
    before = max([s for s in event_snapshots if s.timestamp <= event_date],
                key=lambda x: x.timestamp, default=None)
    after = min([s for s in event_snapshots if s.timestamp > event_date],
               key=lambda x: x.timestamp, default=None)

    if not before or not after:
        print(f"Could not find snapshots both before and after {event_date}")
        return

    print(f"\nEvent Study: {event_date.strftime('%Y-%m-%d')}")
    print(f"Before: {before.timestamp.strftime('%Y-%m-%d %H:%M')}")
    print(f"After: {after.timestamp.strftime('%Y-%m-%d %H:%M')}")
    print(f"\nPrice change: ${before.underlying_price:,.0f} → ${after.underlying_price:,.0f} "
          f"({((after.underlying_price/before.underlying_price - 1) * 100):+.2f}%)")

    # Compare metrics
    print("\nMetric Changes:")
    for key in before.metrics:
        if key in after.metrics:
            val_before = before.metrics[key]
            val_after = after.metrics[key]
            if val_before is not None and val_after is not None:
                import numpy as np
                if not np.isnan(val_before) and not np.isnan(val_after):
                    change = (val_after - val_before) * 100
                    print(f"  {key}: {val_before*100:.2f}% → {val_after*100:.2f}% ({change:+.2f}pp)")

    # Create visualizations
    save_path1 = 'event_comparison.png' if save_plots else None
    save_path2 = 'event_difference.png' if save_plots else None

    plot_surface_comparison(before, after, 'Before Event', 'After Event', save_path=save_path1)
    plot_difference_surface(before, after, 'Event Impact', save_path=save_path2)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze historical volatility surfaces',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_history.py --list
  python analyze_history.py --list --currency BTC
  python analyze_history.py --compare --dates 2025-10-01 2025-10-07
  python analyze_history.py --timeseries
  python analyze_history.py --event-study --date 2025-10-05 --days-before 3 --days-after 3
  python analyze_history.py --timeseries --save-plots
        """
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available snapshots'
    )

    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare two snapshots'
    )

    parser.add_argument(
        '--dates',
        type=str,
        nargs=2,
        metavar=('DATE1', 'DATE2'),
        help='Two dates to compare (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)'
    )

    parser.add_argument(
        '--timeseries',
        action='store_true',
        help='Plot time series of metrics'
    )

    parser.add_argument(
        '--event-study',
        action='store_true',
        help='Analyze surface around an event date'
    )

    parser.add_argument(
        '--date',
        type=str,
        help='Event date for event study (format: YYYY-MM-DD)'
    )

    parser.add_argument(
        '--days-before',
        type=int,
        default=5,
        help='Days before event to analyze (default: 5)'
    )

    parser.add_argument(
        '--days-after',
        type=int,
        default=5,
        help='Days after event to analyze (default: 5)'
    )

    parser.add_argument(
        '--currency',
        type=str,
        choices=['BTC', 'ETH'],
        help='Filter by currency'
    )

    parser.add_argument(
        '--history-dir',
        type=str,
        default='vol_surface_history',
        help='Directory containing snapshots (default: vol_surface_history)'
    )

    parser.add_argument(
        '--save-plots',
        action='store_true',
        help='Save plots to files instead of displaying'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.compare and not args.dates:
        parser.error("--compare requires --dates DATE1 DATE2")

    if args.event_study and not args.date:
        parser.error("--event-study requires --date DATE")

    # Execute requested action
    try:
        if args.list:
            list_snapshots(args.history_dir, args.currency)

        elif args.compare:
            compare_snapshots(args.dates[0], args.dates[1], args.history_dir,
                            args.currency, args.save_plots)

        elif args.timeseries:
            plot_timeseries(args.history_dir, args.currency, args.save_plots)

        elif args.event_study:
            event_study(args.date, args.days_before, args.days_after,
                       args.history_dir, args.currency, args.save_plots)

        else:
            parser.print_help()

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
