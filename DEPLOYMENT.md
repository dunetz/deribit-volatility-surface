# Deployment Guide

## Data Persistence on Streamlit Cloud

### ⚠️ Important Limitation

**Streamlit Cloud uses ephemeral storage:**
- Containers restart periodically (every few days or on redeployment)
- Files saved to disk are **temporary** and will be lost
- `vol_surface_history/` and `plots/` directories won't persist

### Current Behavior (Updated)

The app now automatically detects if it's running on Streamlit Cloud and:
- ✅ **Local**: Full snapshot saving enabled
- ❌ **Cloud**: Snapshot saving disabled with warning message
- 📊 All visualizations work normally in both environments

## Deployment Options

### Option 1: Display-Only Deployment (Current - No Setup Required)

**What works:**
- ✅ Build real-time volatility surfaces
- ✅ View all visualizations
- ✅ Download plots manually from browser
- ❌ No historical snapshots
- ❌ No comparison features

**Deploy to Streamlit Cloud:**
```bash
# Push to GitHub
git add .
git commit -m "Add Streamlit app"
git push origin main

# Then go to: https://share.streamlit.io
# Connect your GitHub repo
# Deploy app.py
```

### Option 2: Add Cloud Storage (AWS S3)

Store snapshots in AWS S3 for persistence.

**Install boto3:**
```bash
pip install boto3
```

**Add to requirements.txt:**
```
boto3>=1.28.0
```

**Update `snapshot.py` to support S3:**
```python
import boto3
import os

class SurfaceHistory:
    def __init__(self, storage_dir='vol_surface_history', use_s3=False, bucket_name=None):
        self.use_s3 = use_s3 or os.getenv('USE_S3_STORAGE') == 'true'
        self.bucket_name = bucket_name or os.getenv('S3_BUCKET_NAME')

        if self.use_s3:
            self.s3_client = boto3.client('s3')
        else:
            self.storage_dir = Path(storage_dir)
            self.storage_dir.mkdir(exist_ok=True)
```

**Set Streamlit Secrets:**
In Streamlit Cloud dashboard, add:
```toml
USE_S3_STORAGE = "true"
S3_BUCKET_NAME = "your-bucket-name"
AWS_ACCESS_KEY_ID = "your-access-key"
AWS_SECRET_ACCESS_KEY = "your-secret-key"
AWS_DEFAULT_REGION = "us-east-1"
```

### Option 3: Add Database Storage (PostgreSQL/MongoDB)

Store snapshots in a database for persistence.

**PostgreSQL Example:**
```bash
pip install psycopg2-binary sqlalchemy
```

**MongoDB Example:**
```bash
pip install pymongo
```

**Modify `snapshot.py` to serialize to database instead of files**

**Use free hosting:**
- PostgreSQL: [Supabase](https://supabase.com) (free tier)
- MongoDB: [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (free tier)

### Option 4: Hybrid Approach (Recommended)

**For Public Demo:**
- Deploy to Streamlit Cloud (display-only)
- Users can build surfaces and view visualizations
- No historical data

**For Personal Use:**
- Run locally: `streamlit run app.py`
- Full snapshot and historical analysis features
- Or deploy to your own server

### Option 5: Self-Hosted with Persistent Storage

**Deploy to your own server with Docker:**

**Create `Dockerfile`:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create persistent volume mount points
RUN mkdir -p /app/vol_surface_history /app/plots

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Run with Docker:**
```bash
docker build -t deribit-vol-surface .
docker run -p 8501:8501 \
  -v $(pwd)/vol_surface_history:/app/vol_surface_history \
  -v $(pwd)/plots:/app/plots \
  deribit-vol-surface
```

**Deploy to:**
- DigitalOcean App Platform
- AWS ECS/Fargate
- Google Cloud Run
- Heroku
- Your own VPS

## Recommended Approach

### For Quick Demo/Portfolio:
```bash
# Just deploy current version to Streamlit Cloud
# Works great for demonstrations
# No persistence needed
```

### For Production Use:
```bash
# Option A: Add S3 storage (best for cloud deployment)
# Option B: Self-host with Docker (best for full control)
# Option C: Run locally (simplest for personal use)
```

## Current Setup Summary

**As pushed to GitHub:**
- ✅ Works locally with full features
- ✅ Deploys to Streamlit Cloud with display-only mode
- ✅ Automatic detection of cloud environment
- ✅ Warning message when snapshots unavailable
- ✅ No setup required for basic deployment

**To enable persistence on cloud, choose one:**
1. Add S3 integration (~1 hour setup)
2. Add database integration (~2 hours setup)
3. Self-host with Docker (~30 min setup)
