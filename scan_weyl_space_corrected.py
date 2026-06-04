"""
scan_weyl_space.py - Corrected Version
======================================

Proper usage of coefficient-based scanning for TopoQgate project.
Project: TopoQgate
"""

import numpy as np
import sys
sys.path.insert(0, './outputs')  # For your local setup, adjust path

from topoqgate_core import (
    generate_log_grid, generate_custom_grid, generate_linear_grid,
    scan_parameter_space, add_topology_to_dataframe, 
    save_dataframe, print_summary
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Grid sizes
N_TAU = 10
N_DELTA = 8
N_OMEGA1 = 8
N_OMEGA2 = 8

# Parameter ranges
PARAM_MIN = 0.1
PARAM_MAX = 10.0

# Output
OUTPUT_FILE = "weyl_scan_results.csv"

# ============================================================================
# OPTION A: Pure Coefficient-Based Hamiltonian
# ============================================================================
# Use this when you want ONLY your coefficients to define the Hamiltonian
# (no contribution from delta, omega1, omega2)

def scan_pure_coefficient_hamiltonian():
    """
    Scan tau only with a fixed coefficient-defined Hamiltonian.
    H = Σ Ncoeff[op] * op
    """
    print("\n" + "="*70)
    print("PURE COEFFICIENT-BASED SCAN")
    print("="*70)
    
    # Define your Hamiltonian entirely through coefficients
    # Example: Strong XX coupling (your Ncoeff style)
    Ncoeff = {
        'XX': 30,  # Strong XX coupling
        # Add any other terms you want:
        # 'YY': 0,
        # 'ZZ': 0,
    }
    
    # Create grid with SINGLE ZERO values for delta, omega1, omega2
    # This ensures they don't contribute to the Hamiltonian
    grid = generate_custom_grid(
        tau_range=np.logspace(np.log10(PARAM_MIN), np.log10(PARAM_MAX), N_TAU),
        delta_range=np.array([0.0]),    # Single zero - no contribution
        omega1_range=np.array([0.0]),   # Single zero - no contribution
        omega2_range=np.array([0.0]),   # Single zero - no contribution
        coefficients=Ncoeff
    )
    
    # Run scan
    df = scan_parameter_space(grid, verbose=True)
    df = add_topology_to_dataframe(df, verbose=True)
    
    return df


# ============================================================================
# OPTION B: Coefficient Base + AshN Parameter Scanning
# ============================================================================
# Use this when you want to study how delta, omega1, omega2 affect topology
# when starting from a base Hamiltonian defined by coefficients

def scan_with_parameter_perturbation():
    """
    Fix base Hamiltonian via coefficients, then scan over AshN parameters.
    
    The final Hamiltonian will be:
    H = Ncoeff[XX]*XX + ... + (delta/2)(ZI + IZ) + (omega1/2)XI + (omega2/2)IX
    """
    print("\n" + "="*70)
    print("COEFFICIENT BASE + PARAMETER PERTURBATION SCAN")
    print("="*70)
    
    # Base Hamiltonian from coefficients
    Ncoeff = {
        'XX': 30,  # Strong base coupling
        # You can set ZI, IZ, XI, IX here too, but note they'll be ADDED to
        # the delta/omega contributions from the scan
    }
    
    # Full 4D scan over tau, delta, omega1, omega2
    grid = generate_log_grid(
        n_tau=N_TAU,
        n_delta=N_DELTA,
        n_omega1=N_OMEGA1,
        n_omega2=N_OMEGA2,
        param_range=(PARAM_MIN, PARAM_MAX),
        coefficients=Ncoeff
    )
    
    # Run scan
    df = scan_parameter_space(grid, verbose=True)
    df = add_topology_to_dataframe(df, verbose=True)
    
    return df


# ============================================================================
# OPTION C: Standard iSWAP-like with Additional Terms
# ============================================================================
# Use this for the standard XX+YY/2 coupling with possible additional terms

def scan_iswap_like():
    """
    Standard iSWAP coupling with optional additional terms.
    
    H = (delta/2)(ZI + IZ) + (XX + YY)/2 + (omega1/2)XI + (omega2/2)IX + extras
    """
    print("\n" + "="*70)
    print("iSWAP-LIKE SCAN")
    print("="*70)
    
    # Standard iSWAP + potential ZZ interaction
    Ncoeff = {
        'XX': 0.5,
        'YY': 0.5,
        'ZZ': 0.1,  # Small ZZ perturbation
    }
    
    # Scan parameters
    grid = generate_log_grid(
        n_tau=N_TAU,
        n_delta=N_DELTA,
        n_omega1=N_OMEGA1,
        n_omega2=N_OMEGA2,
        param_range=(PARAM_MIN, PARAM_MAX),
        coefficients=Ncoeff
    )
    
    df = scan_parameter_space(grid, verbose=True)
    df = add_topology_to_dataframe(df, verbose=True)
    
    return df


# ============================================================================
# OPTION D: Cartan Form (For Topological Phase Diagram)
# ============================================================================
# Study the Cartan Hamiltonian H_AI = α·XX + β·YY + γ·ZZ

def scan_cartan_form():
    """
    Scan over Cartan parameters for topological phase diagram.
    
    Uses coefficient scanning functions for proper parameter variation.
    """
    print("\n" + "="*70)
    print("CARTAN FORM SCAN")
    print("="*70)
    
    from topoqgate_core import scan_two_coefficients
    
    # Fix one coupling, scan the other two
    base_coeffs = {'YY': 0.5}
    
    xx_values = np.linspace(0, 1.0, 20)
    zz_values = np.linspace(-0.5, 0.5, 20)
    tau = np.pi / 2  # Fixed time for this scan
    
    df = scan_two_coefficients(
        base_coeffs,
        'XX', xx_values,
        'ZZ', zz_values,
        tau,
        verbose=True
    )
    # Note: scan_two_coefficients already includes topology columns!
    
    return df


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("TopoQgate: Weyl Space Scanning")
    print("="*70)
    
    # Choose which scan to run:
    
    # Option A: Pure coefficient Hamiltonian (tau scan only)
    # df = scan_pure_coefficient_hamiltonian()
    
    # Option B: Coefficient base + parameter perturbation
    df = scan_with_parameter_perturbation()
    
    # Option C: iSWAP-like with extras
    # df = scan_iswap_like()
    
    # Option D: Cartan form phase diagram
    # df = scan_cartan_form()
    
    # Summary and save
    print_summary(df)
    save_dataframe(df, OUTPUT_FILE)
    
    print(f"\n✓ Results saved to: {OUTPUT_FILE}")
