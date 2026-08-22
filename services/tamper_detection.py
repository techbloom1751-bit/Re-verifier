import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import os

def perform_ela(image_path, output_heatmap_path):
    temp_filename = "temp_ela.jpg"
    try:
        original = Image.open(image_path).convert('RGB')
        original.save(temp_filename, 'JPEG', quality=90)
        resaved = Image.open(temp_filename)
        
        ela_im = ImageChops.difference(original, resaved)
        extrema = ela_im.getextrema()
        max_diff = max([ex[1] for ex in extrema]) or 1
        
        ela_im = ImageEnhance.Brightness(ela_im).enhance((255.0 / max_diff) * 1.5)
        ela_im.save(output_heatmap_path)
        
        ela_cv = cv2.imread(output_heatmap_path, cv2.IMREAD_GRAYSCALE)
        _, std_val = cv2.meanStdDev(ela_cv)
        tamper_score = min(100, float(std_val[0][0] * 2.5))
        
        return {"tamper_score": round(tamper_score, 2), "suspicious": tamper_score > 45.0}
    finally:
        if os.path.exists(temp_filename): os.remove(temp_filename)