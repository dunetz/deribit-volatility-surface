# Deribit Volatility Surface Analysis

Build and analyze cryptocurrency implied volatility surfaces using options data from the Deribit exchange.

## Features

- Real-time volatility surface construction for BTC and ETH
- Multiple interpolation methods (RBF, cubic, SVI parametrization)
- Historical snapshot management and comparison
- Comprehensive visualizations (3D surfaces, smiles, term structures, Greeks)
- Event study analysis for before/after comparisons
- Time series analysis of volatility metrics

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Streamlit Web App (Recommended)

Launch the interactive web application:

```bash
streamlit run app.py
```

This will open a browser window with an interactive interface where you can:
- Build volatility surfaces in real-time
- Visualize all plots interactively
- Compare historical snapshots
- Analyze metrics time series
- No command-line arguments needed!

### Command Line Interface

### Build a Volatility Surface

```bash
# Build BTC surface (plots automatically saved to plots/BTC_YYYYMMDD_HHMMSS/)
python main.py --currency BTC --method rbf

# Build and save snapshot with raw data for historical analysis
python main.py --currency BTC --method rbf --save --save-raw

# Build ETH surface without displaying visualizations (still saves plots)
python main.py --currency ETH --method svi --save --no-viz

# Use custom plots directory
python main.py --currency BTC --plots-dir my_analysis

# Skip saving plots
python main.py --currency BTC --no-save-plots
```

**Note:** By default, all plots are automatically saved to timestamped subdirectories in `plots/`. Each run creates a folder like `plots/BTC_20251007_161841/` with descriptively named PNG files.

### Analyze Historical Data

```bash
# List all saved snapshots
python analyze_history.py --list

# Compare two specific dates
python analyze_history.py --compare --dates 2025-10-01 2025-10-07

# Plot time series of volatility metrics
python analyze_history.py --timeseries

# Event study around a specific date
python analyze_history.py --event-study --date 2025-10-05 --days-before 3 --days-after 3
```

## Project Structure

- `app.py` - **Streamlit web app (recommended)**
- `main.py` - Main CLI for building volatility surfaces
- `analyze_history.py` - CLI for historical analysis
- `deribit_api.py` - Deribit API data collection
- `data_processing.py` - Data cleaning and validation
- `surface_builder.py` - Surface interpolation methods
- `metrics.py` - Metrics calculation
- `snapshot.py` - Snapshot management classes
- `visualizations.py` - Plotting functions
- `requirements.txt` - Python dependencies

## Surface Construction Methods

1. **RBF (Recommended)**: Radial basis function interpolation with thin plate spline
2. **Simple**: Scipy griddata with cubic interpolation
3. **SVI**: Stochastic Volatility Inspired parametrization

## Visualizations

- 3D volatility surfaces
- Volatility smiles by expiration
- Volatility term structures
- 2D heatmaps
- Greek surfaces (delta, gamma, vega)
- Surface comparisons and differences
- Metrics time series

## Data Storage

Snapshots are saved in `vol_surface_history/`:
- `{CURRENCY}_{YYYYMMDD_HHMMSS}.json` - Snapshot metadata
- `{CURRENCY}_{YYYYMMDD_HHMMSS}_raw.pkl` - Raw options data (optional)

## Documentation

See [CLAUDE.md](CLAUDE.md) for detailed architecture and API reference.

## Legacy Notebook

The original Jupyter notebook (`Deribit_Vol_Surface_2.ipynb`) is preserved for reference.
