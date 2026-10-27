"""Export Landsat NDVI, LST, and ESA WorldCover land cover from Google Earth Engine to Google Drive."""
import os

import ee
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
START, END = "2025-06-01", "2025-09-30"
SCALE = 30  # Landsat native resolution (meters)

# Area of interest: [west, south, east, north]. Replace with your own bounding box.
AOI = ee.Geometry.Rectangle([73.80, 18.50, 73.90, 18.60])


def mask_clouds(img):
    """Mask clouds and cloud shadows using the Landsat QA_PIXEL band."""
    qa = img.select("QA_PIXEL")
    cloud = qa.bitwiseAnd(1 << 3).neq(0)
    shadow = qa.bitwiseAnd(1 << 4).neq(0)
    return img.updateMask(cloud.Or(shadow).Not())


def load_landsat():
    """Merge Landsat 8 and 9 Collection 2 Level 2 data."""
    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    return (l8.merge(l9)
            .filterBounds(AOI)
            .filterDate(START, END)
            .map(mask_clouds))


def compute_ndvi(img):
    """NDVI = (NIR - Red) / (NIR + Red). SR_B5 is NIR and SR_B4 is Red for Landsat 8/9."""
    sr = img.select(["SR_B4", "SR_B5"]).multiply(0.0000275).add(-0.2)
    return sr.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")


def compute_lst(img):
    """Land surface temperature in Celsius from ST_B10. Emissivity correction not included."""
    kelvin = img.select("ST_B10").multiply(0.00341802).add(149.0)
    return kelvin.subtract(273.15).rename("LST_C")


def get_landcover():
    """ESA WorldCover (10 m) land cover, used as training labels."""
    return (ee.ImageCollection("ESA/WorldCover/v200")
            .first().select("Map").rename("LC").clip(AOI))


def run():
    if not PROJECT_ID:
        raise SystemExit("Set GCP_PROJECT_ID in your .env file or environment.")

    ee.Initialize(project=PROJECT_ID)
    collection = load_landsat()

    ndvi = collection.map(compute_ndvi).median().clip(AOI)
    lst = collection.map(compute_lst).median().clip(AOI)
    lc = get_landcover()

    # Band order in the exported GeoTIFF: NDVI, LST_C, LC
    stack = ndvi.addBands(lst).addBands(lc).toFloat()

    task = ee.batch.Export.image.toDrive(
        image=stack,
        description="digital_twin_ndvi_lst_lc",
        folder="digital-twin-exports",
        fileNamePrefix="ndvi_lst_latest",
        region=AOI,
        scale=SCALE,
        maxPixels=1e9,
        fileFormat="GeoTIFF",
    )
    task.start()
    print("Export started. Check progress at https://code.earthengine.google.com/tasks")


if __name__ == "__main__":
    run()
