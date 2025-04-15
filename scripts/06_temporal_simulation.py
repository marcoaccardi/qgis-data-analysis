#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 6: Temporal Simulation (Optional)
---------------------------------------
Scan the raster along a path and extract time series data for sonification.

This script:
1. Generates a path across the raster (left-to-right, top-to-bottom, or diagonal)
2. For each point on the path:
   - Extracts values from each feature raster
   - Calculates moving averages/windows
3. Outputs a time series CSV suitable for:
   - Amplitude envelopes
   - Frequency modulation
   - Rhythmic/tempo control

Usage:
    python 06_temporal_simulation.py --input_dir <input_directory> --output_dir <output_directory> 
                                    [--direction <direction>] [--num_points <num_points>] [--window_size <window_size>]
"""

import os
import sys
import argparse
import logging
import json
import csv
import numpy as np
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility modules
from utils.qgis_utils import initialize_qgis, cleanup_qgis
from utils.raster_utils import load_raster, generate_path_across_raster, extract_raster_along_path, create_clean_raster_for_sonification
from utils.config_utils import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_feature_time_series(feature_paths, path_points, output_dir):
    """
    Extract time series data for each feature along a path.
    
    Args:
        feature_paths (dict): Dictionary of feature paths
        path_points (list): List of (x, y) coordinates defining the path
        output_dir (str): Directory to save the output CSVs
        
    Returns:
        dict: Dictionary of output paths for each feature
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Results dictionary
    results = {}
    
    # Extract time series for each feature
    for feature_name, feature_path in feature_paths.items():
        logger.info(f"Extracting time series for {feature_name}...")
        
        # Load the feature raster
        feature_layer = load_raster(feature_path)
        if not feature_layer:
            logger.error(f"Failed to load feature raster: {feature_path}")
            continue
        
        # Output CSV path
        output_path = os.path.join(output_dir, f"{feature_name}_time_series.csv")
        
        # Extract values along the path
        result_path = extract_raster_along_path(feature_layer, path_points, output_path)
        
        if result_path:
            logger.info(f"Saved time series for {feature_name} to: {result_path}")
            results[feature_name] = result_path
        else:
            logger.error(f"Failed to extract time series for {feature_name}")
    
    return results

def calculate_moving_averages(time_series_paths, window_sizes, output_dir):
    """
    Calculate moving averages for time series data.
    
    Args:
        time_series_paths (dict): Dictionary of time series CSV paths
        window_sizes (list): List of window sizes
        output_dir (str): Directory to save the output CSVs
        
    Returns:
        dict: Dictionary of output paths for each feature and window size
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Results dictionary
    results = {}
    
    # Process each time series
    for feature_name, csv_path in time_series_paths.items():
        feature_results = {}
        
        # Read the CSV file
        indices = []
        x_values = []
        y_values = []
        values = []
        
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                indices.append(int(row['Index']))
                x_values.append(float(row['X']))
                y_values.append(float(row['Y']))
                # Handle different types of missing values
                val = row['Value']
                if val == '' or val == 'None' or val is None:
                    values.append(np.nan)
                else:
                    try:
                        values.append(float(val))
                    except ValueError:
                        # If conversion fails, use NaN
                        values.append(np.nan)
        
        # Convert to numpy array for easier processing
        values_array = np.array(values)
        
        # Calculate moving averages for each window size
        for window_size in window_sizes:
            try:
                # Use pandas for moving average calculation
                import pandas as pd
                
                # Create a pandas Series
                series = pd.Series(values_array)
                
                # Calculate moving average
                if not np.isnan(series).all():  # Check if all values are NaN
                    moving_avg = series.rolling(window=window_size, center=True).mean()
                    
                    # Save to CSV
                    output_path = os.path.join(output_dir, f"{feature_name}_window_{window_size}.csv")
                    
                    with open(output_path, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Index', 'X', 'Y', 'Value', 'MovingAvg'])
                        
                        for i in range(len(indices)):
                            avg_value = moving_avg[i] if i < len(moving_avg) else np.nan
                            writer.writerow([
                                indices[i], 
                                x_values[i], 
                                y_values[i], 
                                values[i] if not np.isnan(values[i]) else 'None', 
                                avg_value if not np.isnan(avg_value) else 'None'
                            ])
                            
                    logger.info(f"Saved moving average (window={window_size}) for {feature_name} to: {output_path}")
                    feature_results[window_size] = output_path
                else:
                    logger.warning(f"All values are NaN for {feature_name}. Skipping moving average calculation.")
            except Exception as e:
                logger.error(f"Error calculating moving average for {feature_name} with window size {window_size}: {str(e)}")
        
        if feature_results:
            results[feature_name] = feature_results
    
    return results

def create_combined_time_series(time_series_paths, output_path):
    """
    Create a combined time series CSV with all features.
    
    Args:
        time_series_paths (dict): Dictionary of time series CSV paths
        output_path (str): Path to save the combined CSV
        
    Returns:
        str: Path to the combined CSV
    """
    try:
        # Check if there are any time series to combine
        if not time_series_paths:
            logger.error("No time series files to combine")
            return None
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Read all time series data
        feature_data = {}
        max_points = 0
        
        for feature_name, csv_path in time_series_paths.items():
            if not os.path.exists(csv_path):
                logger.warning(f"Time series file not found: {csv_path}")
                continue
                
            # Read CSV data
            with open(csv_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                # Skip empty files
                if not rows:
                    logger.warning(f"Time series file is empty: {csv_path}")
                    continue
                    
                # Store data
                feature_data[feature_name] = rows
                max_points = max(max_points, len(rows))
                
        if not feature_data:
            logger.error("No valid time series data found")
            return None
            
        # Prepare combined data structure
        combined_data = []
        
        # Find the first file to use as the spatial reference
        reference_feature = next(iter(feature_data.keys()))
        reference_rows = feature_data[reference_feature]
        
        # Create a row for each point in the reference file
        for i in range(len(reference_rows)):
            row = {
                'Index': reference_rows[i]['Index'],
                'X': reference_rows[i]['X'],
                'Y': reference_rows[i]['Y']
            }
            
            # Add values for each feature
            for feature_name, rows in feature_data.items():
                if i < len(rows):
                    # Get the value, ensuring it's numeric when possible
                    value = rows[i].get('Value', '')
                    if value == '':
                        row[feature_name] = None
                    else:
                        try:
                            # Try to convert to float for numerical operations
                            row[feature_name] = float(value)
                        except (ValueError, TypeError):
                            # If conversion fails, keep as string
                            row[feature_name] = value
                else:
                    # If this feature has fewer points than the reference,
                    # use None to indicate missing data
                    row[feature_name] = None
                    
            combined_data.append(row)
            
        # Write the combined CSV
        with open(output_path, 'w', newline='') as csvfile:
            # Determine all field names
            fieldnames = ['Index', 'X', 'Y'] + list(feature_data.keys())
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write data rows
            for row in combined_data:
                writer.writerow(row)
                
        logger.info(f"Created combined time series with {len(combined_data)} points and {len(feature_data)} features")
        
        # Verify the output exists
        if os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Failed to create combined time series file: {output_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating combined time series: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main(args=None):
    """Main function to parse arguments and execute temporal simulation."""
    if args is None:
        parser = argparse.ArgumentParser(description='Create time series simulation for sonification')
        parser.add_argument('--input_dir', required=True, help='Input directory containing feature rasters')
        parser.add_argument('--output_dir', required=True, help='Output directory for time series files')
        parser.add_argument('--direction', default='left_to_right', 
                            choices=['left_to_right', 'top_to_bottom', 'diagonal'],
                            help='Direction to generate the path across the raster')
        parser.add_argument('--num_points', type=int, default=100, help='Number of points along the path')
        parser.add_argument('--window_size', type=int, default=5, help='Window size for moving averages')
        args = parser.parse_args()
    
    # Initialize QGIS
    qgs = initialize_qgis()
    
    try:
        # Check if config file exists and load it
        config_manager = ConfigManager()
        
        # Get window sizes from config or use command line
        window_sizes = config_manager.config.get('window_sizes', [args.window_size])
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Find feature rasters
        features_dir = os.path.join(args.input_dir, "features")
        if not os.path.exists(features_dir):
            # Try the input directory if features subdirectory doesn't exist
            features_dir = args.input_dir
        
        # Get all feature rasters
        feature_paths = {}
        for root, dirs, files in os.walk(features_dir):
            for file in files:
                if file.endswith('.tif') and 'mask' not in file.lower():
                    feature_name = os.path.splitext(file)[0]
                    feature_paths[feature_name] = os.path.join(root, file)
                    logger.info(f"Found feature: {feature_name}")
        
        if not feature_paths:
            logger.error("No feature rasters found. Cannot continue.")
            sys.exit(1)
        
        # Create time series directory
        time_series_dir = os.path.join(args.output_dir, "time_series")
        os.makedirs(time_series_dir, exist_ok=True)
        
        # Create moving averages directory
        moving_avg_dir = os.path.join(args.output_dir, "moving_averages")
        os.makedirs(moving_avg_dir, exist_ok=True)
        
        # Create clean rasters directory for sonification (with no NoData values)
        sonification_dir = os.path.join(args.output_dir, "sonification_rasters")
        os.makedirs(sonification_dir, exist_ok=True)
        
        # Create clean versions of all feature rasters for sonification
        clean_feature_paths = {}
        for feature_name, feature_path in feature_paths.items():
            output_path = os.path.join(sonification_dir, f"{feature_name}_clean.tif")
            clean_path = create_clean_raster_for_sonification(feature_path, output_path)
            if clean_path:
                clean_feature_paths[feature_name] = clean_path
                logger.info(f"Created clean version of {feature_name} for sonification")
        
        # Generate a path across the raster
        # We can use any feature raster as the reference for the path
        reference_feature = next(iter(feature_paths.values()))
        reference_layer = load_raster(reference_feature)
        
        if not reference_layer:
            logger.error(f"Failed to load reference feature: {reference_feature}")
            sys.exit(1)
        
        logger.info(f"Generating path across raster: {args.direction} with {args.num_points} points")
        path_points = generate_path_across_raster(
            reference_layer, 
            direction=args.direction, 
            num_points=args.num_points
        )
        
        # Save the path to a CSV file
        path_csv = os.path.join(args.output_dir, "path_points.csv")
        with open(path_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Index', 'X', 'Y'])
            
            for i, (x, y) in enumerate(path_points):
                writer.writerow([i, x, y])
        
        logger.info(f"Saved path points to: {path_csv}")
        
        # Extract time series for each feature
        time_series_paths = extract_feature_time_series(
            feature_paths, 
            path_points, 
            time_series_dir
        )
        
        if not time_series_paths:
            logger.error("Failed to extract time series. Exiting.")
            sys.exit(1)
        
        # Calculate moving averages
        moving_avg_paths = calculate_moving_averages(
            time_series_paths, 
            window_sizes, 
            moving_avg_dir
        )
        
        # Create combined time series
        combined_csv = os.path.join(args.output_dir, "combined_time_series.csv")
        combined_path = create_combined_time_series(time_series_paths, combined_csv)
        
        # Also create a separate combined time series from clean feature rasters for sonification
        logger.info("Creating time series from clean rasters for sonification...")
        
        # Extract time series from clean rasters
        clean_time_series_paths = extract_feature_time_series(
            clean_feature_paths, 
            path_points, 
            os.path.join(sonification_dir, "time_series")
        )
        
        # Create combined clean time series
        clean_combined_csv = os.path.join(sonification_dir, "combined_time_series_clean.csv")
        clean_combined_path = create_combined_time_series(clean_time_series_paths, clean_combined_csv)
        
        # Save metadata
        metadata = {
            "path": path_csv,
            "direction": args.direction,
            "num_points": args.num_points,
            "window_sizes": window_sizes,
            "time_series": time_series_paths,
            "moving_averages": moving_avg_paths,
            "combined": combined_path,
            "sonification": {
                "clean_rasters": clean_feature_paths,
                "clean_time_series": clean_time_series_paths,
                "clean_combined": clean_combined_path
            }
        }
        
        metadata_path = os.path.join(args.output_dir, "temporal_simulation_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        logger.info(f"Saved temporal simulation metadata to: {metadata_path}")
        logger.info(f"Created clean rasters and time series for sonification in: {sonification_dir}")
        logger.info("Note: The clean rasters and time series have NO NoData values and are ready for direct sonification.")
        
    except Exception as e:
        logger.error(f"Error during temporal simulation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
