# Streamlit App Guide

## Running the App

```bash
streamlit run app.py
```

The app will automatically open in your default browser at `http://localhost:8501`

## Features

### Mode 1: Build Current Surface

Build real-time volatility surfaces with live Deribit data.

**Steps:**
1. Select "Build Current Surface" in the sidebar
2. Choose currency (BTC or ETH)
3. Select interpolation method (rbf, simple, or svi)
4. Optionally enable "Save Snapshot" to save to disk
5. If saving, optionally enable "Save Raw Data" for historical analysis
6. Click "🚀 Build Surface" button

**What You'll See:**
- Market summary with current price, DVOL, and key metrics
- ATM implied volatility for different tenors
- 25-delta skew and term structure slope
- Interactive 3D volatility surface
- Volatility heatmap
- Volatility smile by expiration
- Term structure visualization
- Greek surfaces (Delta, Gamma, Vega) if available

### Mode 2: Analyze Historical Data

Analyze and compare saved volatility surface snapshots.

#### A) List Snapshots
- View all saved snapshots in a table
- Filter by currency (BTC, ETH, or All)
- See timestamp, currency, price, and DVOL for each snapshot

#### B) Compare Surfaces
- Select two snapshots to compare
- View side-by-side 3D surfaces
- See difference surface showing IV changes
- Compare metrics before and after
- Calculate price change between snapshots

#### C) Metrics Time Series
- Plot time series of all volatility metrics
- View ATM IV evolution across tenors
- Track DVOL vs ATM 30d IV
- Monitor 25-delta skew over time
- Analyze term structure slope changes
- Display underlying price movements
- Show IV surface dispersion
- Optionally view raw data table

## Tips

1. **First Time Use**: Build and save at least one surface with "Save Raw Data" enabled to unlock historical analysis features

2. **Performance**: The app fetches live data from Deribit, which may take 30-60 seconds depending on the number of available options

3. **Saving Data**: Enable "Save Snapshot" to build a historical database for trend analysis

4. **Interactive Plots**: All matplotlib plots support zoom, pan, and save functionality through the browser interface

5. **Comparing Snapshots**: For meaningful comparisons, select snapshots from the same currency

## Keyboard Shortcuts

- `R` - Rerun the app
- `C` - Clear cache
- `?` - Show keyboard shortcuts

## Troubleshooting

**App won't start:**
```bash
# Install/upgrade streamlit
pip install --upgrade streamlit

# Check if port is in use
lsof -i :8501
```

**Slow loading:**
- The app fetches real-time data from Deribit API
- Large option chains can take time to process
- Consider using shorter moneyness ranges in data_processing.py

**No historical data:**
- Run the app once and save a snapshot with "Save Raw Data" enabled
- Or use the CLI: `python main.py --currency BTC --save --save-raw`

## Architecture

The Streamlit app (`app.py`) imports all modules from the CLI tools:
- Uses the same data collection, processing, and surface building functions
- Stores results in Streamlit session state
- Reuses all visualization functions from `visualizations.py`
- Accesses the same snapshot system for historical analysis

This ensures consistency between the web app and CLI tools.
