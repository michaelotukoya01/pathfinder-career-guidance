"""Compatibility entry point: training and preprocessing now share a leakage-safe pipeline.

Run python training.py --output .run/model-candidate to generate reviewed artifacts.
"""
from training import main

if __name__ == '__main__':
    main()