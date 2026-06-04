"""
TopoQgate: Parameter Space Scanner
===================================

Simple script to scan H parameter space and generate Weyl mapping data.
Imports all functionality from topoqgate_core.

CONFIGURE GRID HERE - modify the parameters below to change resolution.
"""

import os
from topoqgate_core import *

# ============================================================================
# CONFIGURATION - CHANGE THESE VALUES TO ADJUST GRID
# ============================================================================

# Output directory
# OUTPUT_DIR = "/mnt/user-data/outputs"
OUTPUT_DIR = "./outputs"  # Uncomment for local use

# Grid resolution (number of points per dimension)
N_TAU = 15      # Time points
N_DELTA = 20    # Detuning points
N_OMEGA1 = 20   # Drive 1 points
N_OMEGA2 = 20   # Drive 2 points


# Parameter range (all parameters sampled in this range)
PARAM_MIN = 0.05
PARAM_MAX = 50.0

# Output filename
# OUTPUT_FILE_NAME = "weyl_mapping_data.csv"
OUTPUT_FILE_NAME = "gate_stability.csv"

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("TopoQgate: Parameter Space Scanner")
    print("="*80)
    # print(f"Qiskit available: {QISKIT_AVAILABLE}")
    # print(f"Output directory: {OUTPUT_DIR}")
    # print(f"\nGrid configuration:")
    # print(f"  τ points: {N_TAU}")
    # print(f"  δ points: {N_DELTA}")
    # print(f"  ω₁ points: {N_OMEGA1}")
    # print(f"  ω₂ points: {N_OMEGA2}")
    # print(f"  Total: {N_TAU * N_DELTA * N_OMEGA1 * N_OMEGA2:,} points")
    # print(f"  Range: [{PARAM_MIN}, {PARAM_MAX}]")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate grid
    print("\nGenerating logarithmic grid...")
    # grid = generate_log_grid(
    #     n_tau=N_TAU,
    #     n_delta=N_DELTA,
    #     n_omega1=N_OMEGA1,
    #     n_omega2=N_OMEGA2,
    #     param_range=(PARAM_MIN, PARAM_MAX),
    #     coefficients,
    # )

    Ncoeff = {
        'IX': 0, 'IY': 0, 'IZ': 0,
        'XI': 0, 'XX': 30, 'XY': 0, 'XZ': 0,
        'YI': 0, 'YX': 0, 'YY': 0, 'YZ': 0,
        'ZI': 0, 'ZX': 0, 'ZY': 0, 'ZZ': 0,
    }

    PARAM_MIN = np.pi/4 - np.pi/40
    PARAM_MAX = np.pi/4 + np.pi/40

    grid = generate_log_grid(
        n_tau=N_TAU,
        n_delta=N_DELTA,
        n_omega1=N_OMEGA1,
        n_omega2=N_OMEGA2,
        param_range=(PARAM_MIN, PARAM_MAX),
        coefficients=Ncoeff,
    )
    
    # Scan parameter space
    df = scan_parameter_space(grid, verbose=True)
    
    # Save results
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE_NAME)
    save_dataframe(df, output_path)
    
    # Print summary
    print_summary(df)
    
    print("="*80)
    print("✓ SCAN COMPLETE!")
    print(f"✓ Data saved to: {output_path}")
    print("="*80)
