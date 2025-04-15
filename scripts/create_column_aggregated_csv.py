import pandas as pd
import numpy as np
import os
from PIL import Image

def create_column_aggregated_csv(dataset_path, png_filename):
    """
    Create a CSV where each row represents a single x-position (column) in the image.
    Feature values are aggregated across all y values (rows) in that column.
    
    Args:
        dataset_path: Path to the dataset folder
        png_filename: Name of the PNG file to use for reference
    
    Returns:
        Path to the new aggregated CSV file
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
    
    # Read the PNG to get its width
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
    
    # Determine the mapping between pixel x-coordinate and world x-coordinate
    min_x = df['X'].min()
    max_x = df['X'].max()
    unique_x = sorted(df['X'].unique())
    
    print(f"X range: {min_x} to {max_x}, {len(unique_x)} unique values")
    
    # Get the feature columns (excluding Index, X, Y)
    feature_columns = [col for col in df.columns if col not in ['Index', 'X', 'Y']]
    
    # Function to convert pixel x-coordinate to world x-coordinate
    def pixel_x_to_world_x(pixel_x):
        # Linear mapping from pixel to world coordinates
        return min_x + (pixel_x / width) * (max_x - min_x)
    
    # Create a list to hold the aggregated rows (one per x-column)
    aggregated_rows = []
    
    # Process each column (x position) in the image
    for x in range(width):
        # Convert pixel x to world x
        world_x = pixel_x_to_world_x(x)
        
        # Find the closest world_x in the original data
        closest_x = min(unique_x, key=lambda val: abs(val - world_x))
        
        # Get all rows with this X value
        column_data = df[df['X'] == closest_x]
        
        # Create a new row with the aggregated values
        row_data = {'pixel_x': x, 'world_x': world_x}
        
        # For each feature, calculate the median (ignoring NaN values)
        for feature in feature_columns:
            values = column_data[feature].values
            # Only calculate median if we have values
            if len(values) > 0:
                row_data[feature] = np.median(values)
            else:
                row_data[feature] = np.nan
        
        # Add the aggregated row
        aggregated_rows.append(row_data)
    
    # Create a DataFrame from the aggregated rows
    aggregated_df = pd.DataFrame(aggregated_rows)
    
    # Save the aggregated CSV
    output_csv_path = os.path.join(dataset_path, 'combined_time_series_columnaggregated.csv')
    aggregated_df.to_csv(output_csv_path, index=False)
    print(f"Aggregated CSV saved to {output_csv_path} with {len(aggregated_df)} rows")
    
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
    
    # Create the column-aggregated CSV
    create_column_aggregated_csv(dataset_path, png_filename)
    
    print(f"Completed processing for {dataset_name}")
