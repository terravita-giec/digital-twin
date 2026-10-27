"""Train a land cover classifier on the exported raster and write predictions and hotspots as a COG.

Usage:
    python ml_pipeline.py --input path/to/ndvi_lst_latest.tif --output-dir data/
"""
import argparse
import os

import numpy as np
import rasterio
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

HOTSPOT_PERCENTILE = 90


def load_raster(path):
    with rasterio.open(path) as src:
        data = src.read().astype("float32")  # (3, rows, cols): NDVI, LST_C, LC
        profile = src.profile.copy()
    ndvi, lst, lc = data
    valid = np.isfinite(ndvi) & np.isfinite(lst) & np.isfinite(lc) & (lc > 0)
    return ndvi, lst, lc, valid, profile


def train(ndvi, lst, lc, valid):
    X = np.column_stack([ndvi[valid], lst[valid]])
    classes, y = np.unique(lc[valid].astype(int), return_inverse=True)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                          eval_metric="mlogloss")
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)
    print("Test accuracy:", round(accuracy_score(y_te, y_pred), 3))
    print(classification_report(y_te, y_pred, target_names=[str(c) for c in classes],
                                zero_division=0))
    return model, classes, X


def predict(model, classes, X, ndvi, lst, valid):
    pred = np.zeros(ndvi.shape, dtype=np.uint8)
    pred[valid] = classes[model.predict(X)].astype(np.uint8)

    threshold = np.nanpercentile(lst[valid], HOTSPOT_PERCENTILE)
    hotspot = np.zeros(ndvi.shape, dtype=np.uint8)
    hotspot[valid] = (lst[valid] >= threshold).astype(np.uint8)
    print("Hotspot threshold (C):", round(float(threshold), 2))
    return pred, hotspot


def write_outputs(pred, hotspot, profile, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    raw_path = os.path.join(output_dir, "ml_outputs_raw.tif")
    cog_path = os.path.join(output_dir, "ml_outputs_cog.tif")

    out_profile = profile.copy()
    out_profile.update(count=2, dtype="uint8", nodata=0, driver="GTiff")
    with rasterio.open(raw_path, "w", **out_profile) as dst:
        dst.write(np.stack([pred, hotspot]))
        dst.set_band_description(1, "landcover_pred")
        dst.set_band_description(2, "heat_hotspot")

    cog_translate(raw_path, cog_path, cog_profiles.get("deflate"), in_memory=False)
    print("Saved:", cog_path)
    return cog_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to the exported GeoTIFF")
    parser.add_argument("--output-dir", default="data", help="Where to write outputs")
    args = parser.parse_args()

    ndvi, lst, lc, valid, profile = load_raster(args.input)
    print("Raster shape:", ndvi.shape, "| valid pixels:", int(valid.sum()))

    model, classes, X = train(ndvi, lst, lc, valid)
    pred, hotspot = predict(model, classes, X, ndvi, lst, valid)
    write_outputs(pred, hotspot, profile, args.output_dir)


if __name__ == "__main__":
    main()
