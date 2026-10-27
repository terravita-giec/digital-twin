"""Convert the hotspot band of the COG into a WGS84 GeoJSON of polygons.

Usage:
    python vectorize_hotspots.py --cog data/ml_outputs_cog.tif --out data/heat_hotspots.geojson
"""
import argparse

import geopandas as gpd
import rasterio
from rasterio import features
from shapely.geometry import shape

MIN_AREA_M2 = 900  # drop fragments under ~10 pixels at 30 m


def vectorize(cog_path, out_path):
    with rasterio.open(cog_path) as src:
        hotspot = src.read(2)  # band 2: 1 = hotspot, 0 = not
        transform = src.transform
        crs = src.crs

    records = [
        {"hotspot": int(v), "geometry": shape(geom)}
        for geom, v in features.shapes(hotspot, mask=(hotspot == 1), transform=transform)
    ]

    gdf = gpd.GeoDataFrame(records, crs=crs)
    gdf = gdf[gdf.geometry.area >= MIN_AREA_M2].reset_index(drop=True)
    gdf = gdf.to_crs(epsg=4326)
    gdf.to_file(out_path, driver="GeoJSON")
    print("Hotspot polygons:", len(gdf))
    return gdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cog", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    vectorize(args.cog, args.out)


if __name__ == "__main__":
    main()
