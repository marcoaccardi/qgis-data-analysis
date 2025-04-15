#!/bin/bash
# Run the sonification pipeline for all datasets in the dataset folder

# Check if the pipeline script exists
if [ ! -f "run_sonification_pipeline.sh" ]; then
    echo "Error: run_sonification_pipeline.sh not found"
    exit 1
fi

# Make the scripts executable
chmod +x run_sonification_pipeline.sh
chmod +x generate_all_visualizations.sh

# Create a log directory
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Process each .asc file in the dataset directory
for dataset in dataset/*.asc; do
    echo "=========================================="
    echo "Processing dataset: $dataset"
    echo "=========================================="
    
    # Extract the filename without path
    filename=$(basename "$dataset")
    
    # Run the pipeline with the current dataset
    # Logging both to console and to a log file
    ./run_sonification_pipeline.sh -i "$dataset" -o "output" -v | tee "$LOG_DIR/${filename%.asc}_log.txt"
    
    echo "Completed processing: $dataset"
    echo ""
done

# Generate visualizations for all processed datasets
echo "=========================================="
echo "Generating visualizations for all datasets"
echo "=========================================="
./generate_all_visualizations.sh

echo "All datasets processed and visualized successfully!"
echo "Sonification-ready files are available in the output folders in clean raster format with no NoData values."
echo "Visualization files are available in the visualizations directory."
