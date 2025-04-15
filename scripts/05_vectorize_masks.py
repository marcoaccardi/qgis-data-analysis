#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 5: Vectorize Masks
------------------------
Convert binary masks to vector polygons and optionally extract centroids.

This script:
1. Takes binary masks from stage 3
2. Converts them to vector polygons (shapefiles)
3. Optionally extracts centroids with IDs
4. Exports in both shapefile and GeoJSON formats
5. Creates a combined vector file with all masks

Usage:
    python 05_vectorize_masks.py --input_dir <input_directory> --output_dir <output_directory> [--extract_centroids]
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility modules
from utils.qgis_utils import initialize_qgis, cleanup_qgis, verify_output_exists
from utils.raster_utils import load_raster
from utils.vector_utils import load_vector, save_vector_as_geojson, extract_centroids, merge_vector_layers
from utils.config_utils import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def vectorize_mask(mask_path, output_shp, output_geojson=None):
    """
    Convert a binary mask raster to vector polygons.
    
    Args:
        mask_path (str): Path to the binary mask raster
        output_shp (str): Path to save the shapefile
        output_geojson (str): Path to save the GeoJSON file (optional)
        
    Returns:
        tuple: (shapefile_path, geojson_path)
    """
    try:
        import processing
        from qgis.core import QgsVectorLayer
        
        # Load the mask raster
        mask_layer = load_raster(mask_path)
        if not mask_layer:
            logger.error(f"Failed to load mask raster: {mask_path}")
            return None, None
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_shp), exist_ok=True)
        
        # Polygonize the mask raster
        logger.info(f"Polygonizing mask: {mask_path}")
        
        # Run the GDAL polygonize algorithm
        params = {
            'INPUT': mask_path,
            'BAND': 1,
            'FIELD': 'value',
            'EIGHT_CONNECTEDNESS': False,
            'OUTPUT': output_shp
        }
        
        result = processing.run("gdal:polygonize", params)
        
        if not verify_output_exists(output_shp):
            logger.error(f"Failed to create vector polygon: {output_shp}")
            return None, None
        
        logger.info(f"Created vector polygon: {output_shp}")
        
        # Convert to GeoJSON if requested
        geojson_path = None
        if output_geojson:
            # Load the created shapefile
            vector_layer = load_vector(output_shp)
            if vector_layer:
                geojson_path = save_vector_as_geojson(vector_layer, output_geojson)
                if geojson_path:
                    logger.info(f"Saved vector as GeoJSON: {geojson_path}")
                else:
                    logger.error(f"Failed to save as GeoJSON: {output_geojson}")
        
        return output_shp, geojson_path
        
    except Exception as e:
        logger.error(f"Error vectorizing mask: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def main():
    """Main function to parse arguments and execute mask vectorization."""
    parser = argparse.ArgumentParser(description='Vectorize binary masks')
    parser.add_argument('--input_dir', required=True, help='Input directory containing masks')
    parser.add_argument('--output_dir', required=True, help='Output directory for vectors')
    parser.add_argument('--extract_centroids', action='store_true', help='Extract centroids from polygons')
    
    args = parser.parse_args()
    
    # Initialize QGIS
    qgs = initialize_qgis()
    if not qgs:
        logger.error("Failed to initialize QGIS. Exiting.")
        sys.exit(1)
    
    try:
        # Check if input directory exists
        if not os.path.exists(args.input_dir):
            logger.error(f"Input directory not found: {args.input_dir}")
            sys.exit(1)
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Find mask rasters
        masks_dir = os.path.join(args.input_dir, "masks")
        if not os.path.exists(masks_dir):
            # Try the input directory if masks subdirectory doesn't exist
            masks_dir = args.input_dir
        
        # Get all mask TIFFs
        mask_paths = []
        for file in os.listdir(masks_dir):
            if file.endswith('.tif') and 'mask' in file.lower():
                mask_paths.append(os.path.join(masks_dir, file))
        
        if not mask_paths:
            logger.error(f"No mask files found in {masks_dir}")
            sys.exit(1)
        
        logger.info(f"Found {len(mask_paths)} mask files")
        
        # Create output directories
        shp_dir = os.path.join(args.output_dir, "shapefiles")
        os.makedirs(shp_dir, exist_ok=True)
        
        geojson_dir = os.path.join(args.output_dir, "geojson")
        os.makedirs(geojson_dir, exist_ok=True)
        
        if args.extract_centroids:
            centroid_dir = os.path.join(args.output_dir, "centroids")
            os.makedirs(centroid_dir, exist_ok=True)
        
        # Results for metadata
        results = {}
        vector_layers = []
        
        # Process each mask
        for mask_path in mask_paths:
            mask_name = os.path.splitext(os.path.basename(mask_path))[0]
            logger.info(f"Processing {mask_name}...")
            
            # Output paths
            output_shp = os.path.join(shp_dir, f"{mask_name}.shp")
            output_geojson = os.path.join(geojson_dir, f"{mask_name}.geojson")
            
            # Vectorize the mask
            shp_path, geojson_path = vectorize_mask(mask_path, output_shp, output_geojson)
            
            if not shp_path:
                logger.error(f"Failed to vectorize {mask_name}. Skipping...")
                continue
            
            # Load the shapefile for potential merge
            vector_layer = load_vector(shp_path)
            if vector_layer:
                vector_layers.append(vector_layer)
            
            # Save results
            results[mask_name] = {
                "shapefile": shp_path,
                "geojson": geojson_path
            }
            
            # Extract centroids if requested
            if args.extract_centroids:
                centroid_shp = os.path.join(centroid_dir, f"{mask_name}_centroids.shp")
                centroid_geojson = os.path.join(centroid_dir, f"{mask_name}_centroids.geojson")
                
                logger.info(f"Extracting centroids for {mask_name}...")
                
                centroid_layer = extract_centroids(vector_layer, centroid_shp)
                if centroid_layer:
                    logger.info(f"Created centroid shapefile: {centroid_shp}")
                    
                    # Save as GeoJSON
                    centroid_geojson_path = save_vector_as_geojson(centroid_layer, centroid_geojson)
                    if centroid_geojson_path:
                        logger.info(f"Saved centroids as GeoJSON: {centroid_geojson_path}")
                    
                    # Save in results
                    results[mask_name]["centroids_shapefile"] = centroid_shp
                    results[mask_name]["centroids_geojson"] = centroid_geojson_path
                else:
                    logger.error(f"Failed to extract centroids for {mask_name}")
        
        # Create merged vector if we have multiple layers
        if len(vector_layers) > 1:
            logger.info(f"Merging {len(vector_layers)} vector layers...")
            
            merged_shp = os.path.join(args.output_dir, "all_zones.shp")
            merged_layer = merge_vector_layers(vector_layers, merged_shp)
            
            if merged_layer:
                logger.info(f"Created merged vector layer: {merged_shp}")
                
                # Save as GeoJSON
                merged_geojson = os.path.join(args.output_dir, "all_zones.geojson")
                merged_geojson_path = save_vector_as_geojson(merged_layer, merged_geojson)
                
                if merged_geojson_path:
                    logger.info(f"Saved merged vector as GeoJSON: {merged_geojson_path}")
                
                # Save in results
                results["merged"] = {
                    "shapefile": merged_shp,
                    "geojson": merged_geojson_path
                }
                
                # Extract centroids if requested
                if args.extract_centroids:
                    merged_centroids_shp = os.path.join(centroid_dir, "all_zones_centroids.shp")
                    merged_centroids_geojson = os.path.join(centroid_dir, "all_zones_centroids.geojson")
                    
                    merged_centroids = extract_centroids(merged_layer, merged_centroids_shp)
                    if merged_centroids:
                        logger.info(f"Created merged centroids: {merged_centroids_shp}")
                        
                        # Save as GeoJSON
                        merged_centroids_geojson_path = save_vector_as_geojson(merged_centroids, merged_centroids_geojson)
                        
                        if merged_centroids_geojson_path:
                            logger.info(f"Saved merged centroids as GeoJSON: {merged_centroids_geojson_path}")
                        
                        # Save in results
                        results["merged"]["centroids_shapefile"] = merged_centroids_shp
                        results["merged"]["centroids_geojson"] = merged_centroids_geojson_path
            else:
                logger.error("Failed to merge vector layers")
        
        # Save metadata
        metadata_path = os.path.join(args.output_dir, "vector_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(results, f, indent=4)
        
        logger.info(f"Saved vector metadata to: {metadata_path}")
        
    except Exception as e:
        logger.error(f"Error during mask vectorization: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
