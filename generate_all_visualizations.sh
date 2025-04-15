#!/bin/bash
# Generate visualizations for all processed datasets

# Set up paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/output"
VISUALIZATION_DIR="$SCRIPT_DIR/visualizations"
LOG_DIR="$SCRIPT_DIR/logs"

# Create visualization directory if it doesn't exist
mkdir -p "$VISUALIZATION_DIR"
mkdir -p "$LOG_DIR"

# Find all dataset directories in the output folder
echo "Generating visualizations for all processed datasets..."
for dataset_dir in "$OUTPUT_DIR"/*; do
    if [ -d "$dataset_dir" ]; then
        # Extract the dataset name from the folder path
        dataset_name=$(basename "$dataset_dir")
        echo "=========================================="
        echo "Generating visualizations for: $dataset_name"
        echo "=========================================="
        
        # Original dataset visualization
        if [ -f "$dataset_dir/$dataset_name.tif" ]; then
            echo "Visualizing original DEM..."
            python3 "$SCRIPT_DIR/utils/convert_asc_to_png.py" \
                -i "$dataset_dir/$dataset_name.tif" \
                -o "$VISUALIZATION_DIR" \
                -t all | tee -a "$LOG_DIR/${dataset_name}_visualization_log.txt"
        fi
        
        # Feature visualizations
        if [ -d "$dataset_dir/features" ]; then
            echo "Visualizing terrain features..."
            python3 "$SCRIPT_DIR/utils/convert_asc_to_png.py" \
                -i "$dataset_dir/features" \
                -o "$VISUALIZATION_DIR" \
                -t all | tee -a "$LOG_DIR/${dataset_name}_visualization_log.txt"
        fi
        
        # Sonification rasters visualizations
        if [ -d "$dataset_dir/sonification_rasters" ]; then
            echo "Visualizing sonification-ready rasters..."
            python3 "$SCRIPT_DIR/utils/convert_asc_to_png.py" \
                -i "$dataset_dir/sonification_rasters" \
                -o "$VISUALIZATION_DIR" \
                -t all | tee -a "$LOG_DIR/${dataset_name}_visualization_log.txt"
        fi
        
        echo "Completed visualizations for: $dataset_name"
        echo ""
    fi
done

echo "All visualizations generated successfully!"
echo "Visualization files are available in the visualizations directory."
