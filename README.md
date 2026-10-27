# Digital Twin

A geospatial digital twin that processes Landsat imagery in Google Earth Engine, predicts land cover and urban heat hotspots with XGBoost, stores results in PostGIS, and serves them through GeoServer and a FastAPI backend to a CesiumJS frontend.

## Architecture

| Tier | Components |
|------|-----------|
| Engine | Earth Engine, Python ML pipeline, Rasterio, GeoPandas |
| Backend | PostgreSQL + PostGIS, GeoServer (WMS/WFS), FastAPI |
| Frontend | React, CesiumJS |

## Status

- [x] Earth Engine export of NDVI, LST, and land cover
- [x] ML classification and hotspot detection
- [x] Vectorization and PostGIS loading
- [x] Database schema
- [ ] GeoServer publishing
- [ ] FastAPI endpoints
- [ ] Frontend
- [ ] Deployment

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/<your-username>/digital-twin.git
cd digital-twin
cp .env.example .env   # then edit .env with your values
```

### 2. Start the database

```bash
docker compose up -d db
docker compose exec db psql -U postgres -d twin -c "CREATE EXTENSION IF NOT EXISTS postgis;"
docker compose exec -T db psql -U postgres -d twin < api/schema.sql
```

### 3. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r ingestion/requirements.txt
```

GDAL and rasterio can be hard to install with pip on Windows. If that fails, use conda: `conda install -c conda-forge rasterio gdal geopandas`.

### 4. Run the pipeline

```bash
# Export from Earth Engine (runs in Earth Engine; download the result from Drive to data/)
python ingestion/compute_indices.py

# Train and predict
python ingestion/ml_pipeline.py --input data/ndvi_lst_latest.tif --output-dir data

# Vectorize hotspots
python ingestion/vectorize_hotspots.py --cog data/ml_outputs_cog.tif --out data/heat_hotspots.geojson

# Load into PostGIS
python ingestion/load_to_postgis.py --geojson data/heat_hotspots.geojson --table heat_hotspots
```

### Google Earth Engine authentication

Run `earthengine authenticate` once on your machine, or in Colab run `ee.Authenticate()`. Set `GCP_PROJECT_ID` in `.env` to a project registered for Earth Engine.

## Notes

- Data files (`*.tif`, `*.geojson`) and secrets (`.env`, service account keys) are excluded from Git.
- Colab can run the ingestion scripts, but it can't host the database. Use Colab for Earth Engine and ML work, and run the database locally or on a hosted service.

## License

Choose a license before publishing (MIT is a common default for open projects).
