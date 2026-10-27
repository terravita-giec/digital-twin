"""Load a GeoJSON file into PostGIS. Replaces the ogr2ogr step.

Usage:
    python load_to_postgis.py --geojson data/heat_hotspots.geojson --table heat_hotspots
"""
import argparse
import os

import geopandas as gpd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def load(geojson_path, table):
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Set DATABASE_URL in your .env file or environment.")

    engine = create_engine(url)
    gdf = gpd.read_file(geojson_path)
    gdf.to_postgis(table, engine, if_exists="replace", index=False)
    print(f"Loaded {len(gdf)} rows into {table}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--geojson", required=True)
    parser.add_argument("--table", default="heat_hotspots")
    args = parser.parse_args()
    load(args.geojson, args.table)


if __name__ == "__main__":
    main()
