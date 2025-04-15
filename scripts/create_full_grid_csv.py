import pandas as pd
import numpy as np
import os
from PIL import Image

def create_full_grid_csv(dataset_path, png_filename):
    """
    Create a full grid CSV based on a PNG image, with one row per pixel.
    The rows are ordered column-by-column for scanline reading.
    
    Args:
        dataset_path: Path to the dataset folder containing the combined_time_series.csv
        png_filename: Name of the PNG file to use for reference
    
    Returns:
        Path to the new full grid CSV file
    """
    # Get the PNG path and verify it exists
    visualization_dir = os.path.join(
        os.path.dirname(os.path.dirname(dataset_path)), 
        'visualizations',
        os.path.basename(dataset_path) + '.asc',
        os.path.basename(dataset_path)
    )
    png_path = os.path.join(visualization_dir, png_filename)
    
    if not os.path.exists(png_path):
        print(f"Warning: PNG file {png_path} not found, skipping dataset {dataset_path}")
        return None
    
    # Get the CSV path and verify it exists
    csv_path = os.path.join(dataset_path, 'combined_time_series.csv')
    if not os.path.exists(csv_path):
        print(f"Warning: CSV file {csv_path} not found, skipping dataset {dataset_path}")
        return None
    
    # Read the PNG dimensions
    try:
        img = Image.open(png_path)
        width, height = img.size
        print(f"Processing {os.path.basename(dataset_path)} - Image size: {width}x{height}")
    except Exception as e:
        print(f"Error reading PNG: {e}, skipping dataset {dataset_path}")
        return None
    
    # Read the CSV with the data points
    try:
        df = pd.read_csv(csv_path)
        print(f"Original CSV has {len(df)} data points")
    except Exception as e:
        print(f"Error reading CSV: {e}, skipping dataset {dataset_path}")
        return None
    
    # Determine the mapping between pixel coordinates and world coordinates
    min_x = df['X'].min()
    max_x = df['X'].max()
    min_y = df['Y'].min()
    max_y = df['Y'].max()
    
    # Get unique X and Y values
    unique_x = sorted(df['X'].unique())
    unique_y = sorted(df['Y'].unique())
    
    # Print mapping info for debugging
    print(f"X range: {min_x} to {max_x}, {len(unique_x)} unique values")
    print(f"Y range: {min_y} to {max_y}, {len(unique_y)} unique values")
    
    # Create a dictionary to map (x, y) world coordinates to data rows
    # First reorganize the DataFrame to be indexed by coordinates
    coord_to_data = {}
    for idx, row in df.iterrows():
        coord_to_data[(row['X'], row['Y'])] = row.to_dict()
    
    # Find data column names from the CSV (excluding Index, X, Y)
    data_columns = [col for col in df.columns if col not in ['Index', 'X', 'Y']]
    
    # Function to find the nearest data point for a given pixel coordinate
    def world_to_data(world_x, world_y):
        # Find the closest X coordinate
        closest_x = min(unique_x, key=lambda x: abs(x - world_x))
        
        # Find the closest Y coordinate
        closest_y = min(unique_y, key=lambda y: abs(y - world_y))
        
        # Return the data at this coordinate if it exists
        if (closest_x, closest_y) in coord_to_data:
            return coord_to_data[(closest_x, closest_y)]
        return None
    
    # Function to convert pixel coordinates to world coordinates
    def pixel_to_world(pixel_x, pixel_y):
        # Linear mapping from pixel to world coordinates
        # This assumes the PNG is a direct rendering of the data range
        world_x = min_x + (pixel_x / width) * (max_x - min_x)
        
        # If there's only one Y value, use that
        if len(unique_y) == 1:
            world_y = unique_y[0]
        else:
            world_y = min_y + (pixel_y / height) * (max_y - min_y)
        
        return world_x, world_y
    
    # Create a list to hold all rows for the full grid
    grid_rows = []
    
    # Generate rows in column-by-column order (x is fast-changing)
    for x in range(width):
        for y in range(height):
            # Convert pixel coordinates to world coordinates
            world_x, world_y = pixel_to_world(x, y)
            
            # Try to find corresponding data
            data = world_to_data(world_x, world_y)
            
            # Prepare the row
            row_data = {
                'pixel_x': x,
                'pixel_y': y,
                'world_x': world_x,
                'world_y': world_y
            }
            
            # Add data values if available, otherwise use NaN
            if data:
                for col in data_columns:
                    row_data[col] = data[col]
            else:
                for col in data_columns:
                    row_data[col] = np.nan
            
            # Add the row to the grid
            grid_rows.append(row_data)
    
    # Create a DataFrame from the grid rows
    grid_df = pd.DataFrame(grid_rows)
    
    # Save the full grid CSV
    output_csv_path = os.path.join(dataset_path, 'combined_time_series_fullgrid.csv')
    grid_df.to_csv(output_csv_path, index=False)
    print(f"Full grid CSV saved to {output_csv_path} with {len(grid_df)} rows")
    
    return output_csv_path

# Base output directory containing all datasets
base_output_dir = os.path.join(os.path.dirname(__file__), '../output')

# PNG file to use for reference
reference_png = "_standard.png" 

# Process each dataset
for dataset_name in os.listdir(base_output_dir):
    dataset_path = os.path.join(base_output_dir, dataset_name)
    if not os.path.isdir(dataset_path):
        continue
    
    # Generate the full PNG filename
    png_filename = f"{dataset_name}{reference_png}"
    
    # Create the full grid CSV
    create_full_grid_csv(dataset_path, png_filename)
    
    # Also create the columnwise sorted original CSV for comparison
    csv_path = os.path.join(dataset_path, 'combined_time_series.csv')
    output_csv_path = os.path.join(dataset_path, 'combined_time_series_columnwise.csv')
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df_sorted = df.sort_values(by=['X', 'Y'])
        df_sorted.to_csv(output_csv_path, index=False)
        print(f"Reordered CSV saved to {output_csv_path}")
    else:
        print(f"No combined_time_series.csv found in {dataset_path}, skipping.")
