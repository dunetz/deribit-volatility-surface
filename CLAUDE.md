# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project builds and analyzes cryptocurrency (Bitcoin/Ethereum) implied volatility surfaces using options data from the Deribit exchange. The codebase includes both a Jupyter notebook and modular Python CLI tools for volatility surface construction, historical tracking, and comparative analysis.

## Project Structure

```
.
├── main.py                      # Main CLI for building vol surfaces
├── analyze_history.py           # CLI for historical analysis
├── deribit_api.py              # Deribit API data collection
├── data_processing.py          # Data cleaning and validation
├── surface_builder.py          # Surface interpolation methods
├── metrics.py                  # Metrics calculation
├── snapshot.py                 # Snapshot management (SurfaceSnapshot, SurfaceHistory)
├── visualizations.py           # All plotting functions
├── requirements.txt            # Python dependencies
├── Deribit_Vol_Surface_2.ipynb # Original notebook (legacy)
└── vol_surface_history/        # Snapshot storage (auto-created)
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Build Current Volatility Surface

```bash
# Basic usage - build and display BTC surface
python main.py --currency BTC --method rbf

# Build and save snapshot with raw data
python main.py --currency BTC --method rbf --save --save-raw

# Build without displaying visualizations
python main.py --currency ETH --method svi --save --no-viz
```

### Analyze Historical Data

```bash
# List all saved snapshots
python analyze_history.py --list

# Compare two dates
python analyze_history.py --compare --dates 2025-10-01 2025-10-07

# Plot metrics time series
python analyze_history.py --timeseries

# Event study (before/after analysis)
python analyze_history.py --event-study --date 2025-10-05 --days-before 3 --days-after 3

# Save plots to files instead of displaying
python analyze_history.py --timeseries --save-plots
```

## Architecture

### Data Flow

1. **Data Collection** (`deribit_api.py`): Fetches live options data from Deribit public API
   - `get_index_price()`: Current underlying price
   - `get_dvol_index()`: Deribit volatility index
   - `get_all_options_data()`: All active options for BTC/ETH
   - `get_option_iv_data()`: Implied volatility and Greeks for each option

2. **Data Processing** (`data_processing.py`): Filters and validates options data
   - `clean_iv_data()`: Removes invalid options, filters by TTE and moneyness
   - `separate_by_type()`: Splits calls and puts
   - `check_call_put_parity()`: Validates IV consistency
   - `summarize_data()`: Prints data statistics

3. **Surface Construction** (`surface_builder.py`): Three interpolation methods
   - `create_simple_surface()`: scipy griddata with cubic interpolation
   - `create_rbf_surface()`: Radial basis function (thin plate spline) - **recommended**
   - `create_svi_surface()`: SVI parametrization (fitted per expiration slice)

4. **Metrics** (`metrics.py`): Calculates surface metrics
   - `calculate_surface_metrics()`: ATM IVs, skew, term structure, statistics

5. **Snapshot Management** (`snapshot.py`): Historical data persistence
   - `SurfaceSnapshot`: Container for single snapshot with serialization
   - `SurfaceHistory`: Manages saving/loading, time series extraction

6. **Visualization** (`visualizations.py`): All plotting functions
   - Standard plots: 3D surface, smile, term structure, heatmap
   - Historical: surface comparison, difference surface, metrics time series
   - Greeks: 3D surfaces for delta, gamma, vega

### Key Classes

**SurfaceSnapshot** (`snapshot.py`):
- Container for single volatility surface snapshot
- Stores: timestamp, currency, price, DVOL, surface data, metrics, raw options
- Surface data stored as `(log_moneyness_mesh, tte_mesh, iv_surface)` tuples
- Serializes to/from JSON for metadata, pickle for raw data

**SurfaceHistory** (`snapshot.py`):
- Manages historical snapshot collection
- Methods:
  - `save_snapshot(snapshot, save_raw=False)`: Save to disk
  - `load_all_snapshots(currency=None)`: Load all snapshots
  - `get_snapshot_by_date(target_date)`: Find closest snapshot
  - `get_metrics_timeseries()`: Extract metrics DataFrame

### Data Representation

Volatility surfaces use **log-moneyness** (ln(Strike/Spot)) and **time-to-expiration in years** as coordinates. This provides better numerical stability for interpolation compared to raw strike prices.

## CLI Reference

### main.py

Build current volatility surface and optionally save snapshot.

**Arguments:**
- `--currency {BTC,ETH}`: Currency to analyze (default: BTC)
- `--method {simple,rbf,svi}`: Surface interpolation method (default: rbf)
- `--save`: Save snapshot to disk
- `--save-raw`: Save raw options data (requires --save)
- `--no-viz`: Skip visualization display
- `--output-dir DIR`: Snapshot directory (default: vol_surface_history)
- `--no-save-plots`: Do not save plots (plots are saved by default)
- `--plots-dir DIR`: Directory to save plots (default: plots)

**Note:** Plots are automatically saved to timestamped subdirectories in `plots/` by default. Each run creates a new subdirectory like `plots/BTC_20251007_161841/` containing all generated plots with descriptive names:
- `BTC_volatility_surface_3d_rbf.png` - 3D volatility surface
- `BTC_volatility_smile.png` - Volatility smile by expiration
- `BTC_term_structure.png` - Volatility term structure
- `BTC_volatility_heatmap.png` - 2D volatility heatmap
- `BTC_delta_surface_3d.png` - Delta Greek surface (if available)
- `BTC_gamma_surface_3d.png` - Gamma Greek surface (if available)
- `BTC_vega_surface_3d.png` - Vega Greek surface (if available)

**Examples:**
```bash
# Basic run - automatically saves plots to plots/BTC_YYYYMMDD_HHMMSS/
python main.py --currency BTC --method rbf --save --save-raw

# ETH surface with plots saved
python main.py --currency ETH --method svi

# Custom plots directory
python main.py --currency BTC --plots-dir my_custom_plots

# Skip saving plots
python main.py --currency BTC --no-save-plots
```

### analyze_history.py

Analyze historical volatility surfaces.

**Arguments:**
- `--list`: List all available snapshots
- `--compare`: Compare two snapshots (requires --dates)
- `--dates DATE1 DATE2`: Two dates to compare (YYYY-MM-DD format)
- `--timeseries`: Plot time series of metrics
- `--event-study`: Event study analysis (requires --date)
- `--date DATE`: Event date (YYYY-MM-DD)
- `--days-before N`: Days before event (default: 5)
- `--days-after N`: Days after event (default: 5)
- `--currency {BTC,ETH}`: Filter by currency
- `--history-dir DIR`: Snapshot directory (default: vol_surface_history)
- `--save-plots`: Save plots to files instead of displaying

**Examples:**
```bash
python analyze_history.py --list --currency BTC
python analyze_history.py --compare --dates 2025-10-01 2025-10-07
python analyze_history.py --timeseries --save-plots
python analyze_history.py --event-study --date 2025-10-05 --days-before 3
```

## API Details

### Deribit Public API Endpoints

Base URL: `https://www.deribit.com/api/v2/public/`

- `get_index_price?index_name={btc|eth}_usd`: Current index price
- `ticker?instrument_name={instrument}`: Option ticker with IV and Greeks
- `get_instruments?currency={BTC|ETH}&kind=option&expired=false`: Active options list

No authentication required for public endpoints. Rate limits apply.

## Data Storage

The `vol_surface_history/` directory (auto-created) contains:
- `{CURRENCY}_{YYYYMMDD_HHMMSS}.json`: Snapshot metadata and surface data
- `{CURRENCY}_{YYYYMMDD_HHMMSS}_raw.pkl`: Raw options DataFrame (if `save_raw=True`)

JSON files contain serialized numpy arrays for surface meshes. Pickle files store complete pandas DataFrames with all option details.

## Metrics Calculated

Surface metrics computed by `calculate_surface_metrics()`:
- **ATM IV**: At-the-money implied volatility for 7d, 30d, 60d, 90d, 180d tenors
- **25-delta skew**: IV difference between 25-delta puts and calls (approx 10% OTM)
- **Term structure slope**: Difference between 90d and 30d ATM IV
- **IV statistics**: Mean, median, std, min, max across entire surface

## Visualization Functions

All functions in `visualizations.py` support optional `save_path` parameter to save plots.

**Standard Plots:**
- `plot_volatility_surface()`: 3D surface plot
- `plot_volatility_smile()`: Smile for specific expirations
- `plot_term_structure()`: Term structure at specific moneyness levels
- `plot_heatmap()`: 2D contour heatmap
- `plot_greeks_surface_3d()`: 3D Greek surface (delta, gamma, vega)

**Historical Comparison:**
- `plot_surface_comparison()`: Side-by-side 3D surfaces
- `plot_difference_surface()`: IV change surface
- `plot_metrics_timeseries()`: Time series of key metrics

## Notes

- Default data filters: min TTE = 1 day, moneyness range = 0.7-1.3
- RBF method recommended for smooth surfaces; SVI for parametric modeling
- SVI fitting requires ≥5 data points per expiration
- Historical analysis requires snapshots saved with `--save-raw`
- The original Jupyter notebook (`Deribit_Vol_Surface_2.ipynb`) is preserved for reference
