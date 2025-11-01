#!/usr/bin/env python3
"""Data preparation script."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.prepare import main

if __name__ == "__main__":
    main("data/autoscout24_sample_data.xlsx", "data/clean.parquet")

