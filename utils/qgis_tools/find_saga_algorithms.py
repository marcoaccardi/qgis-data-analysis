#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find SAGA Wetness Index Algorithm
--------------------------------
Simple script to find SAGA wetness index algorithms
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.qgis_utils import initialize_qgis, cleanup_qgis

def main():
    # Initialize QGIS
    qgs = initialize_qgis()
    if not qgs:
        print("Failed to initialize QGIS")
        sys.exit(1)
    
    try:
        import processing
        from qgis.core import QgsApplication
        
        registry = QgsApplication.processingRegistry()
        providers = registry.providers()
        
        saga_provider = None
        for provider in providers:
            if provider.id() == 'saga':
                saga_provider = provider
                break
        
        if not saga_provider:
            print("SAGA provider not found")
            sys.exit(1)
        
        print("SAGA ALGORITHMS:")
        print("=" * 60)
        
        algorithms = []
        for alg in saga_provider.algorithms():
            alg_id = alg.id()
            alg_name = alg.displayName()
            algorithms.append((alg_id, alg_name))
        
        # Sort alphabetically
        algorithms.sort(key=lambda x: x[0])
        
        # Print all algorithms
        for alg_id, alg_name in algorithms:
            print(f"{alg_id:45} | {alg_name}")
            
        # Specifically look for wetness-related algorithms
        print("\nWETNESS-RELATED ALGORITHMS:")
        print("=" * 60)
        
        wetness_algs = [(alg_id, alg_name) for alg_id, alg_name in algorithms 
                       if 'wet' in alg_id.lower() or 'wet' in alg_name.lower()]
        
        if wetness_algs:
            for alg_id, alg_name in wetness_algs:
                print(f"{alg_id:45} | {alg_name}")
        else:
            print("No wetness-related algorithms found")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)

if __name__ == "__main__":
    main()
