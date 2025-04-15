#!/bin/bash
# QGIS Sonification Pipeline Runner
# This script runs all steps of the QGIS terrain analysis pipeline for sonification

# Set default values
INPUT_FILE=""
OUTPUT_DIR="output"
EPSG_CODE="EPSG:32616"  # Default to UTM Zone 16N
DIRECTION="left_to_right"
NUM_POINTS=100
WINDOW_SIZE=5
VERBOSE=0
EXTRACT_CENTROIDS=0
SKIP_STAGES=""
SINGLE_STAGE=""

# Display help information
show_help() {
    echo "QGIS Sonification Pipeline"
    echo "Usage: ./run_sonification_pipeline.sh -i <input_file> [-o <output_dir>] [-e <epsg_code>] [-d <direction>] [-n <num_points>] [-w <window_size>] [-c] [-v] [-s <stages_to_skip>] [-r <single_stage>]"
    echo ""
    echo "Options:"
    echo "  -i <input_file>      Input DEM file (.asc, .tif, etc.)"
    echo "  -o <output_dir>      Output directory (default: output)"
    echo "  -e <epsg_code>       Target EPSG code (default: EPSG:32616)"
    echo "  -d <direction>       Direction for temporal simulation (left_to_right, top_to_bottom, diagonal)"
    echo "  -n <num_points>      Number of points for temporal simulation (default: 100)"
    echo "  -w <window_size>     Window size for moving averages (default: 5)"
    echo "  -c                   Extract centroids from vector polygons"
    echo "  -v                   Verbose output"
    echo "  -s <stages_to_skip>  Comma-separated list of stages to skip (e.g., '3,4')"
    echo "  -r <single_stage>    Run only a single stage (options: load-prepare, compute-features, create-masks, zonal-stats, vectorize, temporal)"
    echo "  -h                   Display this help message"
    echo ""
    echo "Single Stage Options:"
    echo "  load-prepare      Run only 01_load_and_prepare_raster.py"
    echo "  compute-features  Run only 02_compute_features.py"
    echo "  create-masks      Run only 03_create_zonal_masks.py"
    echo "  zonal-stats       Run only 04_zonal_statistics.py"
    echo "  vectorize         Run only 05_vectorize_masks.py"
    echo "  temporal          Run only 06_temporal_simulation.py"
    exit 1
}

# Parse arguments
while getopts "i:o:e:d:n:w:cvs:r:h" opt; do
    case ${opt} in
        i ) INPUT_FILE=$OPTARG ;;
        o ) OUTPUT_DIR=$OPTARG ;;
        e ) EPSG_CODE=$OPTARG ;;
        d ) DIRECTION=$OPTARG ;;
        n ) NUM_POINTS=$OPTARG ;;
        w ) WINDOW_SIZE=$OPTARG ;;
        c ) EXTRACT_CENTROIDS=1 ;;
        v ) VERBOSE=1 ;;
        s ) SKIP_STAGES=$OPTARG ;;
        r ) SINGLE_STAGE=$OPTARG ;;
        h ) show_help ;;
        \? ) show_help ;;
    esac
done

# Check if input file is provided
if [ -z "$INPUT_FILE" ]; then
    echo "Error: Input file is required"
    show_help
fi

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

# Setup logging
LOG_LEVEL="INFO"
if [ $VERBOSE -eq 1 ]; then
    LOG_LEVEL="DEBUG"
fi

# Create base output directory
mkdir -p "$OUTPUT_DIR"

# Extract filename without extension for output naming
INPUT_BASENAME=$(basename "$INPUT_FILE")
INPUT_NAME="${INPUT_BASENAME%.*}"
SPECIFIC_OUTPUT_DIR="$OUTPUT_DIR/$INPUT_NAME"
mkdir -p "$SPECIFIC_OUTPUT_DIR"

# Configure logging function
log_info() {
    echo -e "\033[0;32m[$(date +"%Y-%m-%d %H:%M:%S")] [INFO] $1\033[0m"
}

log_debug() {
    if [ $VERBOSE -eq 1 ]; then
        echo -e "\033[0;34m[$(date +"%Y-%m-%d %H:%M:%S")] [DEBUG] $1\033[0m"
    fi
}

log_error() {
    echo -e "\033[0;31m[$(date +"%Y-%m-%d %H:%M:%S")] [ERROR] $1\033[0m"
}

# Function to check if an expected output file exists
check_output() {
    local output_file=$1
    if [ ! -f "$output_file" ]; then
        log_error "Stage $CURRENT_STAGE did not produce expected output: $output_file"
        log_error "Check logs for errors and try running with -v for verbose output"
        exit 1
    fi
}

# Function to run stage 0: load and prepare raster
run_stage_0() {
    log_info "Running Stage 0: Input Preparation"
    OUTPUT_TIF="$SPECIFIC_OUTPUT_DIR/$INPUT_NAME.tif"
    
    # Command to run
    CMD="conda run -n qgis_env bash -c \"cd /home/anecoica/Desktop/qgis_sonification_pipeline && python scripts/01_load_and_prepare_raster.py --input \\\"$INPUT_FILE\\\" --output \\\"$OUTPUT_TIF\\\" --epsg \\\"$EPSG_CODE\\\"\""
    log_debug "Command: $CMD"
    
    # Run the command and time it
    START_TIME=$(date +%s)
    eval $CMD
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Check if output was created
    check_output "$OUTPUT_TIF"
    
    log_info "Stage 0 completed in $DURATION seconds"
}

# Function to run stage 1: compute features
run_stage_1() {
    log_info "Running Stage 1: Feature Extraction"
    
    # Ensure input file exists
    INPUT_TIF="$SPECIFIC_OUTPUT_DIR/$INPUT_NAME.tif"
    if [ ! -f "$INPUT_TIF" ] && [ -z "$SINGLE_STAGE" ]; then
        log_error "Input TIF file not found: $INPUT_TIF"
        log_error "You must run stage 0 first or specify a valid input TIF"
        exit 1
    fi
    
    # Command to run
    CMD="conda run -n qgis_env python scripts/02_compute_features.py --input \"$INPUT_TIF\" --output_dir \"$SPECIFIC_OUTPUT_DIR\""
    log_debug "Command: $CMD"
    
    # Run the command and time it
    START_TIME=$(date +%s)
    eval $CMD
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Check if output was created
    check_output "$SPECIFIC_OUTPUT_DIR/feature_list.json"
    
    log_info "Stage 1 completed in $DURATION seconds"
}

# Function to run stage 2: create zonal masks
run_stage_2() {
    log_info "Running Stage 2: Zonal Masks"
    
    # Command to run
    CMD="conda run -n qgis_env python scripts/03_create_zonal_masks.py --input_dir \"$SPECIFIC_OUTPUT_DIR\" --output_dir \"$SPECIFIC_OUTPUT_DIR\""
    log_debug "Command: $CMD"
    
    # Run the command and time it
    START_TIME=$(date +%s)
    eval $CMD
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Check if output was created
    check_output "$SPECIFIC_OUTPUT_DIR/mask_metadata.json"
    
    log_info "Stage 2 completed in $DURATION seconds"
}

# Function to run stage 3: zonal statistics
run_stage_3() {
    log_info "Running Stage 3: Zonal Statistics"
    
    # Command to run
    CMD="conda run -n qgis_env python scripts/04_zonal_statistics.py --input_dir \"$SPECIFIC_OUTPUT_DIR\" --output_dir \"$SPECIFIC_OUTPUT_DIR\""
    log_debug "Command: $CMD"
    
    # Run the command and time it
    START_TIME=$(date +%s)
    eval $CMD
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Check if output was created
    check_output "$SPECIFIC_OUTPUT_DIR/all_zones_statistics.csv"
    
    log_info "Stage 3 completed in $DURATION seconds"
}

# Function to run stage 4: vectorize masks
run_stage_4() {
    log_info "Running Stage 4: Vectorize Masks"
    
    # Command to run
    CENTROID_OPTION=""
    if [ $EXTRACT_CENTROIDS -eq 1 ]; then
        CENTROID_OPTION="--extract_centroids"
    fi
    
    CMD="conda run -n qgis_env python scripts/05_vectorize_masks.py --input_dir \"$SPECIFIC_OUTPUT_DIR\" --output_dir \"$SPECIFIC_OUTPUT_DIR\" $CENTROID_OPTION"
    log_debug "Command: $CMD"
    
    # Run the command and time it
    START_TIME=$(date +%s)
    eval $CMD
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Check if output was created
    check_output "$SPECIFIC_OUTPUT_DIR/vector_metadata.json"
    
    log_info "Stage 4 completed in $DURATION seconds"
}

# Function to run stage 5: temporal simulation
run_stage_5() {
    log_info "Running Stage 5: Temporal Simulation"
    
    # Command to run
    CMD="conda run -n qgis_env python scripts/06_temporal_simulation.py --input_dir \"$SPECIFIC_OUTPUT_DIR\" --output_dir \"$SPECIFIC_OUTPUT_DIR\" --direction \"$DIRECTION\" --num_points $NUM_POINTS --window_size $WINDOW_SIZE"
    log_debug "Command: $CMD"
    
    # Run the command and time it
    START_TIME=$(date +%s)
    eval $CMD
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    # Check if output was created
    check_output "$SPECIFIC_OUTPUT_DIR/combined_time_series.csv"
    
    log_info "Stage 5 completed in $DURATION seconds"
}

# Function to check if a stage should be skipped
should_skip() {
    local stage=$1
    if [[ $SKIP_STAGES == *"$stage"* ]]; then
        return 0  # True (skip)
    else
        return 1  # False (don't skip)
    fi
}

# If a single stage is specified, run only that stage
if [ ! -z "$SINGLE_STAGE" ]; then
    log_info "Running single stage: $SINGLE_STAGE"
    
    case $SINGLE_STAGE in
        "load-prepare")
            run_stage_0
            ;;
        "compute-features")
            run_stage_1
            ;;
        "create-masks")
            run_stage_2
            ;;
        "zonal-stats")
            run_stage_3
            ;;
        "vectorize")
            run_stage_4
            ;;
        "temporal")
            run_stage_5
            ;;
        *)
            log_error "Unknown stage: $SINGLE_STAGE"
            show_help
            ;;
    esac
    
    log_info "Single stage completed: $SINGLE_STAGE"
    exit 0
fi

# Otherwise run the full pipeline with skip options

log_info "Starting QGIS sonification pipeline for $INPUT_FILE"
log_info "Output directory: $SPECIFIC_OUTPUT_DIR"

# Show configuration
log_info "Pipeline configuration:"
log_info "  Input file: $INPUT_FILE"
log_info "  Output directory: $SPECIFIC_OUTPUT_DIR"
log_info "  EPSG code: $EPSG_CODE"
log_info "  Direction: $DIRECTION"
log_info "  Number of points: $NUM_POINTS"
log_info "  Window size: $WINDOW_SIZE"
log_info "  Skip stages: $SKIP_STAGES"
log_info "  Extract centroids: $EXTRACT_CENTROIDS"

# Stage 0: Input Preparation
CURRENT_STAGE=0
if should_skip $CURRENT_STAGE; then
    log_info "Skipping Stage $CURRENT_STAGE: Input Preparation"
else
    run_stage_0
fi

# Stage 1: Feature Extraction
CURRENT_STAGE=1
if should_skip $CURRENT_STAGE; then
    log_info "Skipping Stage $CURRENT_STAGE: Feature Extraction"
else
    run_stage_1
fi

# Stage 2: Zonal Masks
CURRENT_STAGE=2
if should_skip $CURRENT_STAGE; then
    log_info "Skipping Stage $CURRENT_STAGE: Zonal Masks"
else
    run_stage_2
fi

# Stage 3: Zonal Statistics
CURRENT_STAGE=3
if should_skip $CURRENT_STAGE; then
    log_info "Skipping Stage $CURRENT_STAGE: Zonal Statistics"
else
    run_stage_3
fi

# Stage 4: Vectorize Masks
CURRENT_STAGE=4
if should_skip $CURRENT_STAGE; then
    log_info "Skipping Stage $CURRENT_STAGE: Vectorize Masks"
else
    run_stage_4
fi

# Stage 5: Temporal Simulation
CURRENT_STAGE=5
if should_skip $CURRENT_STAGE; then
    log_info "Skipping Stage $CURRENT_STAGE: Temporal Simulation"
else
    run_stage_5
fi

log_info "Sonification pipeline completed successfully!"
log_info "All outputs saved to: $SPECIFIC_OUTPUT_DIR"
log_info "Ready for sonification in Max/MSP or SuperCollider"

# Exit successfully
exit 0
