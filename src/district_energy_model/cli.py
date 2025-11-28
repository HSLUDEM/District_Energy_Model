# -*- coding: utf-8 -*-
"""
Created on Thu Nov 27 09:13:01 2025

@author: UeliSchilt
"""

# src/district_energy_model/cli.py
import argparse
# from pathlib import Path
from district_energy_model.run_dem import main  # or from . import main if main() is in same file

def cli():
    parser = argparse.ArgumentParser(
        prog="district_energy_model",
        description="District Energy Model - Command line interface"
    )

    parser.add_argument(
        "--project_dir",
        type=str,
        default=".",
        help=(
            "Project directory that includes both the data/ and config/ "
            "folders. Simulation results will also be stored within this "
            "directory. Default: current working directory"
            )
    )

    args = parser.parse_args()
    main(root_dir=args.project_dir)
