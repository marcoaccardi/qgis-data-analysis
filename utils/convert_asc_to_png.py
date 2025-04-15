#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert ASC files to PNG images for visualization
-------------------------------------------------
This script converts ASC raster files to PNG images for easier visualization.
It can process all ASC files in a directory or a single file.
"""

import os
import sys
import argparse
import logging
import glob
from osgeo import gdal
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_color_relief(input_file, output_file, color_table=None):
    """
    Create a color relief PNG image from an ASC file using a custom color table.
    
    Args:
        input_file (str): Path to the input ASC file
        output_file (str): Path to the output PNG file
        color_table (str): Optional path to a color table file
    """
    try:
        # If no color table is provided, create a temporary one
        if color_table is None:
            # Open the input file to get min/max values
            ds = gdal.Open(input_file)
            if ds is None:
                logger.error(f"Could not open {input_file}")
                return False
                
            band = ds.GetRasterBand(1)
            stats = band.GetStatistics(0, 1)
            min_val = stats[0]
            max_val = stats[1]
            range_val = max_val - min_val
            
            # Close dataset
            ds = None
            
            # Create a color table with blue-green-red gradient
            color_table_path = os.path.join(os.path.dirname(output_file), "temp_color_table.txt")
            with open(color_table_path, "w") as f:
                f.write(f"{min_val} 0 0 255\n")
                f.write(f"{min_val + range_val * 0.25} 0 128 255\n")
                f.write(f"{min_val + range_val * 0.5} 0 255 0\n")
                f.write(f"{min_val + range_val * 0.75} 255 255 0\n")
                f.write(f"{max_val} 255 0 0\n")
        else:
            color_table_path = color_table
        
        # Run gdal_translate to convert to PNG
        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a color relief using gdaldem
        relief_cmd = f"gdaldem color-relief {input_file} {color_table_path} {output_file} -of PNG"
        logger.info(f"Running: {relief_cmd}")
        os.system(relief_cmd)
        
        # Remove temporary color table
        if color_table is None and os.path.exists(color_table_path):
            os.remove(color_table_path)
            
        if os.path.exists(output_file):
            logger.info(f"Created {output_file}")
            return True
        else:
            logger.error(f"Failed to create {output_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating color relief: {str(e)}")
        return False

def create_hillshade(input_file, output_file, z_factor=1.0):
    """
    Create a hillshade PNG image from an ASC file.
    
    Args:
        input_file (str): Path to the input ASC file
        output_file (str): Path to the output PNG file
        z_factor (float): Vertical exaggeration factor
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        # Run gdaldem to create hillshade
        hillshade_cmd = f"gdaldem hillshade {input_file} {output_file} -z {z_factor} -of PNG"
        logger.info(f"Running: {hillshade_cmd}")
        os.system(hillshade_cmd)
        
        if os.path.exists(output_file):
            logger.info(f"Created {output_file}")
            return True
        else:
            logger.error(f"Failed to create {output_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating hillshade: {str(e)}")
        return False

def create_standard_png(input_file, output_file):
    """
    Create a standard PNG image from an ASC file using gdal_translate.
    
    Args:
        input_file (str): Path to the input ASC file
        output_file (str): Path to the output PNG file
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        # Run gdal_translate to convert to PNG with auto-scaling
        translate_cmd = f"gdal_translate -of PNG -scale {input_file} {output_file}"
        logger.info(f"Running: {translate_cmd}")
        os.system(translate_cmd)
        
        if os.path.exists(output_file):
            logger.info(f"Created {output_file}")
            return True
        else:
            logger.error(f"Failed to create {output_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating standard PNG: {str(e)}")
        return False

def process_file(input_file, output_dir, visualization_type="all", z_factor=1.0):
    """
    Process a single ASC file and convert to PNG.
    
    Args:
        input_file (str): Path to the input ASC file
        output_dir (str): Directory to save output PNGs
        visualization_type (str): Type of visualization (relief, hillshade, standard, all)
        z_factor (float): Vertical exaggeration for hillshade
    """
    try:
        filename = os.path.basename(input_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Get the original dataset name (extract from path or filename)
        original_name = None
        
        # Extract original dataset name from the path
        path_parts = input_file.split(os.sep)
        
        # Try to find a folder name that might contain a dataset identifier
        for part in path_parts:
            if part.endswith("-1m") or part.endswith("-5m") or part.endswith("-10m") or "UTM" in part:
                original_name = part
                break
                
        # If we couldn't find it in the path, try extracting from the filename
        if original_name is None:
            # Look for patterns like S0606, UTM16N, etc.
            import re
            match = re.search(r'(S\d+|UTM\d+\w+|-\d+m)', name_without_ext)
            if match:
                original_name = match.group(0)
            else:
                # Default to the first part of the filename
                original_name = name_without_ext.split('_')[0]
                
        # Create subfolder based on the original dataset name
        output_subdir = os.path.join(output_dir, original_name)
        os.makedirs(output_subdir, exist_ok=True)
        
        # Create a subfolder for the file type
        file_type = name_without_ext.replace(original_name, "").strip("_-")
        if file_type:
            output_subdir = os.path.join(output_subdir, file_type)
            os.makedirs(output_subdir, exist_ok=True)
        
        success = False
        
        if visualization_type in ["relief", "all"]:
            output_file = os.path.join(output_subdir, f"{name_without_ext}_relief.png")
            success = create_color_relief(input_file, output_file)
            
        if visualization_type in ["hillshade", "all"]:
            output_file = os.path.join(output_subdir, f"{name_without_ext}_hillshade.png")
            success = create_hillshade(input_file, output_file, z_factor)
            
        if visualization_type in ["standard", "all"]:
            output_file = os.path.join(output_subdir, f"{name_without_ext}_standard.png")
            success = create_standard_png(input_file, output_file)
            
        return success
        
    except Exception as e:
        logger.error(f"Error processing file {input_file}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Convert ASC files to PNG images for visualization")
    parser.add_argument("-i", "--input", help="Input ASC file or directory containing ASC files", required=True)
    parser.add_argument("-o", "--output", help="Output directory for PNG files", required=True)
    parser.add_argument("-t", "--type", choices=["relief", "hillshade", "standard", "all"], 
                        default="all", help="Type of visualization to create")
    parser.add_argument("-z", "--z-factor", type=float, default=1.0, 
                        help="Vertical exaggeration factor for hillshade (default: 1.0)")
    parser.add_argument("-r", "--recursive", action="store_true", 
                        help="Recursively process subdirectories")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Check if input is a file or directory
    if os.path.isfile(args.input):
        if args.input.lower().endswith((".asc", ".tif", ".tiff")):
            success = process_file(args.input, args.output, args.type, args.z_factor)
            if success:
                logger.info(f"Successfully converted {args.input} to PNG")
            else:
                logger.error(f"Failed to convert {args.input} to PNG")
        else:
            logger.error(f"Input file {args.input} is not an ASC or TIFF file")
    elif os.path.isdir(args.input):
        # Find all ASC files in the directory
        pattern = "**/*.asc" if args.recursive else "*.asc"
        asc_files = glob.glob(os.path.join(args.input, pattern), recursive=args.recursive)
        
        # Add TIF files
        pattern = "**/*.tif" if args.recursive else "*.tif"
        asc_files.extend(glob.glob(os.path.join(args.input, pattern), recursive=args.recursive))
        
        if not asc_files:
            logger.error(f"No ASC or TIFF files found in {args.input}")
            return
            
        logger.info(f"Found {len(asc_files)} files to process")
        
        for asc_file in asc_files:
            # Create output subdirectory structure if recursive
            if args.recursive:
                rel_path = os.path.relpath(os.path.dirname(asc_file), args.input)
                output_subdir = os.path.join(args.output, rel_path)
            else:
                output_subdir = args.output
                
            success = process_file(asc_file, output_subdir, args.type, args.z_factor)
            if success:
                logger.info(f"Successfully converted {asc_file} to PNG")
            else:
                logger.error(f"Failed to convert {asc_file} to PNG")
    else:
        logger.error(f"Input {args.input} is not a valid file or directory")

if __name__ == "__main__":
    main()
