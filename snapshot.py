"""
Historical volatility surface snapshot management.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path


class SurfaceSnapshot:
    """Container for a single volatility surface snapshot"""

    def __init__(self, timestamp, currency, underlying_price, dvol,
                 surface_data, raw_options, metrics):
        self.timestamp = timestamp
        self.currency = currency
        self.underlying_price = underlying_price
        self.dvol = dvol
        self.surface_data = surface_data  # (log_m_mesh, tte_mesh, iv_surf)
        self.raw_options = raw_options
        self.metrics = metrics

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'currency': self.currency,
            'underlying_price': self.underlying_price,
            'dvol': self.dvol,
            'surface_data': {
                'log_moneyness_mesh': self.surface_data[0].tolist(),
                'tte_mesh': self.surface_data[1].tolist(),
                'iv_surface': self.surface_data[2].tolist()
            },
            'metrics': self.metrics
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        timestamp = datetime.fromisoformat(data['timestamp'])
        surface_data = (
            np.array(data['surface_data']['log_moneyness_mesh']),
            np.array(data['surface_data']['tte_mesh']),
            np.array(data['surface_data']['iv_surface'])
        )

        return cls(
            timestamp=timestamp,
            currency=data['currency'],
            underlying_price=data['underlying_price'],
            dvol=data['dvol'],
            surface_data=surface_data,
            raw_options=None,  # Don't store raw data in JSON
            metrics=data['metrics']
        )


class SurfaceHistory:
    """Manages historical volatility surface snapshots"""

    def __init__(self, storage_dir='vol_surface_history'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.snapshots = []

    def save_snapshot(self, snapshot, save_raw=False):
        """Save a snapshot to disk"""

        # Save metadata as JSON
        filename = f"{snapshot.currency}_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.storage_dir / filename

        with open(filepath, 'w') as f:
            json.dump(snapshot.to_dict(), f, indent=2)

        # Optionally save raw options data as pickle (larger files)
        if save_raw and snapshot.raw_options is not None:
            raw_filename = f"{snapshot.currency}_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}_raw.pkl"
            raw_filepath = self.storage_dir / raw_filename
            snapshot.raw_options.to_pickle(raw_filepath)

        print(f"Snapshot saved: {filepath}")

    def load_snapshot(self, filepath):
        """Load a snapshot from disk"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        return SurfaceSnapshot.from_dict(data)

    def load_all_snapshots(self, currency=None):
        """Load all snapshots for a currency"""
        snapshots = []

        for filepath in sorted(self.storage_dir.glob('*.json')):
            if currency and not filepath.stem.startswith(currency):
                continue

            snapshot = self.load_snapshot(filepath)
            snapshots.append(snapshot)

        self.snapshots = sorted(snapshots, key=lambda x: x.timestamp)
        print(f"Loaded {len(self.snapshots)} snapshots")
        return self.snapshots

    def get_snapshot_by_date(self, target_date):
        """Get snapshot closest to a specific date"""
        if not self.snapshots:
            return None

        closest = min(self.snapshots,
                     key=lambda x: abs((x.timestamp - target_date).total_seconds()))
        return closest

    def load_raw_data(self, snapshot):
        """Load raw options data from pickle file for a given snapshot"""
        raw_filename = f"{snapshot.currency}_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}_raw.pkl"
        raw_filepath = self.storage_dir / raw_filename

        if raw_filepath.exists():
            print(f"Loading raw data from: {raw_filepath}")
            try:
                snapshot.raw_options = pd.read_pickle(raw_filepath)
                print("Raw data loaded successfully.")
            except Exception as e:
                print(f"Error loading raw data: {e}")
                snapshot.raw_options = None
        else:
            print(f"Raw data file not found: {raw_filepath}")
            snapshot.raw_options = None

        return snapshot.raw_options

    def get_metrics_timeseries(self):
        """Extract time series of all metrics"""
        if not self.snapshots:
            return pd.DataFrame()

        data = []
        for snap in self.snapshots:
            row = {
                'timestamp': snap.timestamp,
                'underlying_price': snap.underlying_price,
                'dvol': snap.dvol
            }
            row.update(snap.metrics)
            data.append(row)

        return pd.DataFrame(data).set_index('timestamp')
