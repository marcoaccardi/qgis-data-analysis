#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGIS Algorithm Discovery Tool
----------------------------
List all available QGIS processing algorithms in the current environment.

This script:
1. Initializes QGIS
2. Lists all available processing algorithms grouped by provider
3. Optionally filters algorithms by provider or search term
4. Displays detailed help for specific algorithms

Usage:
    python list_qgis_algorithms.py [--provider <provider_name>] [--search <search_term>] [--help <algorithm_id>]
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility modules
from utils.qgis_utils import initialize_qgis, cleanup_qgis, list_available_algorithms

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_algorithm_help(algorithm_id):
    """
    Get detailed help for a specific algorithm.
    
    Args:
        algorithm_id (str): The algorithm ID (e.g., 'native:slope')
        
    Returns:
        str: Help text for the algorithm
    """
    try:
        import processing
        help_text = processing.algorithmHelp(algorithm_id)
        return help_text
    except Exception as e:
        logger.error(f"Error getting help for algorithm '{algorithm_id}': {str(e)}")
        return f"Error: Could not get help for '{algorithm_id}'"

def main():
    """Main function to parse arguments and display QGIS algorithms."""
    parser = argparse.ArgumentParser(description='List available QGIS processing algorithms')
    parser.add_argument('--provider', help='Filter algorithms by provider (e.g., native, gdal)')
    parser.add_argument('--search', help='Search term to filter algorithm names')
    parser.add_argument('--help', dest='algorithm_help', help='Get detailed help for a specific algorithm ID')
    
    args = parser.parse_args()
    
    # Initialize QGIS
    qgs = initialize_qgis()
    if not qgs:
        logger.error("Failed to initialize QGIS. Exiting.")
        sys.exit(1)
    
    try:
        if args.algorithm_help:
            # Display help for a specific algorithm
            help_text = get_algorithm_help(args.algorithm_help)
            print(f"\nHelp for algorithm '{args.algorithm_help}':\n")
            print(help_text)
        else:
            # List available algorithms, optionally filtered
            algorithms = list_available_algorithms(args.provider)
            
            if not algorithms:
                logger.warning("No algorithms found. Check your QGIS installation.")
                sys.exit(1)
            
            print("\nAVAILABLE QGIS PROCESSING ALGORITHMS")
            print("======================================\n")
            
            total_algorithms = 0
            
            for provider, algs in sorted(algorithms.items()):
                # Skip empty providers
                if not algs:
                    continue
                
                # Apply search filter if provided
                if args.search:
                    search_term = args.search.lower()
                    filtered_algs = [alg for alg in algs if search_term in alg['id'].lower() or search_term in alg['name'].lower()]
                    
                    if not filtered_algs:
                        continue
                        
                    algs = filtered_algs
                
                print(f"PROVIDER: {provider.upper()} ({len(algs)} algorithms)")
                print("-" * 50)
                
                for alg in sorted(algs, key=lambda x: x['id']):
                    print(f"{alg['id']:45} | {alg['name']}")
                
                print("\n")
                total_algorithms += len(algs)
            
            print(f"Total: {total_algorithms} algorithms")
            
            if args.search or args.provider:
                filters = []
                if args.provider:
                    filters.append(f"provider='{args.provider}'")
                if args.search:
                    filters.append(f"search='{args.search}'")
                print(f"Filters applied: {', '.join(filters)}")
                
            print("\nTo get detailed help for an algorithm, use: python list_qgis_algorithms.py --help <algorithm_id>")
        
    except Exception as e:
        logger.error(f"Error listing algorithms: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
