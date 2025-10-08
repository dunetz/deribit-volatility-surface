# Data Storage Summary

## Where Data is Saved

### Running Locally

When you run `streamlit run app.py` or `python main.py` on your local machine:

**Snapshots:**
```
/Users/alandunetz/ML/deribit/vol_surface_history/
├── BTC_20251007_161841.json          # Surface metadata & data
└── BTC_20251007_161841_raw.pkl       # Raw options data (if --save-raw)
```

**Plots:**
```
/Users/alandunetz/ML/deribit/plots/
└── BTC_20251007_161841/
    ├── BTC_volatility_surface_3d_rbf.png
    ├── BTC_volatility_smile.png
    ├── BTC_term_structure.png
    ├── BTC_volatility_heatmap.png
    ├── BTC_delta_surface_3d.png
    ├── BTC_gamma_surface_3d.png
    └── BTC_vega_surface_3d.png
```

✅ **Persists:** Forever (until you delete)
✅ **Location:** Your local filesystem
✅ **Features:** Full historical analysis available

### Deployed on Streamlit Cloud (share.streamlit.io)

When deployed to Streamlit Cloud:

**What happens when you click "Build Surface":**

1. **Data Fetching:** ✅ Works normally
   - Fetches live data from Deribit API
   - Processes and cleans data
   - Builds volatility surface

2. **Visualizations:** ✅ Works normally
   - All plots display in browser
   - Interactive matplotlib figures
   - Can right-click to save images

3. **Snapshots:** ⚠️ **TEMPORARY ONLY**
   - Saved to `/app/vol_surface_history/` on container
   - **Lost when container restarts** (every few days or on redeploy)
   - App now shows warning: "⚠️ Snapshot saving disabled on Streamlit Cloud"

4. **Historical Analysis:** ❌ Disabled
   - No persistent storage = no historical snapshots
   - Comparison features won't work
   - Time series analysis unavailable

**Container Lifecycle:**
```
Deploy → Run → Build Surface → Save (temp) → Container Restarts → Data Lost
```

### Current App Behavior

The app automatically detects where it's running:

**Local Environment:**
- Shows "Save Snapshot" checkbox ✅
- Shows "Save Raw Data" checkbox ✅
- All features enabled

**Streamlit Cloud:**
- Shows warning message: "⚠️ Snapshot saving disabled on Streamlit Cloud"
- Checkboxes hidden
- Only real-time surface building available

## Solutions for Cloud Persistence

### Option 1: Use Local App for Historical Analysis

**Best for:** Personal use, development

```bash
# Run locally for full features
streamlit run app.py

# Deploy to cloud for demos/sharing (display only)
```

### Option 2: Add AWS S3 Storage

**Best for:** Production deployment, team use

- Snapshots saved to S3 bucket instead of local filesystem
- Persists forever
- Requires AWS account and credentials
- ~1 hour to implement

### Option 3: Self-Host with Docker

**Best for:** Full control, custom deployment

- Deploy to your own server (DigitalOcean, AWS, etc.)
- Mount persistent volumes
- Full features available
- Requires server management

## Recommendation

**For your use case:**

1. **Quick Demo:** Deploy current version to Streamlit Cloud
   - No changes needed
   - Perfect for portfolio/demonstrations
   - Users can build surfaces and see all visualizations
   - No historical analysis, but that's fine for demos

2. **Personal Analysis:** Run locally
   - Use `streamlit run app.py` on your machine
   - Full snapshot and historical features
   - All data saved to your local filesystem

3. **Production (if needed later):** Add S3 integration
   - See DEPLOYMENT.md for implementation guide
   - Enables cloud deployment with persistence

## What Gets Pushed to GitHub

Your `.gitignore` excludes:
- ❌ `vol_surface_history/` (snapshots)
- ❌ `plots/` (generated plots)
- ✅ Source code only

This is correct! You don't want to commit generated data to git.

## Summary

| Feature | Local | Streamlit Cloud | With S3 |
|---------|-------|-----------------|---------|
| Build Surfaces | ✅ | ✅ | ✅ |
| View Plots | ✅ | ✅ | ✅ |
| Save Snapshots | ✅ | ❌ | ✅ |
| Historical Analysis | ✅ | ❌ | ✅ |
| Persistence | ✅ Forever | ❌ Temporary | ✅ Forever |
| Setup Required | None | None | AWS Setup |
