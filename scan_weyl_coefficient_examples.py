"""
TopoQgate: Coefficient-Based Scanning Examples
==============================================

Demonstrating the correct way to use the coefficient system
for different types of Hamiltonian studies.

Author: Bob
Project: TopoQgate
"""

import numpy as np
import sys
sys.path.insert(0, '/mnt/user-data/uploads')

from topoqgate_core import (
    generate_log_grid, generate_custom_grid, generate_linear_grid,
    scan_parameter_space, build_hamiltonian_from_coefficients,
    build_general_hamiltonian, map_hamiltonian_to_weyl,
    add_topology_to_dataframe, print_summary, save_dataframe
)

# ============================================================================
# EXAMPLE 1: Pure Coefficient-Based Hamiltonian (Cartan Form)
# ============================================================================
# For studying H = α·XX + β·YY + γ·ZZ (Orion & Akkermans Eq. 27)
# where you DON'T want the AshN parameters (delta, omega1, omega2)

def example_pure_coefficients():
    """
    Scan over tau only, with fixed coefficient-based Hamiltonian.
    No delta/omega1/omega2 contributions.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Pure Coefficient-Based Hamiltonian")
    print("="*70)
    
    # Define the Hamiltonian coefficients (Cartan form)
    # H = 0.5*XX + 0.5*YY + 0.3*ZZ
    cartan_coeffs = {
        'XX': 0.5,
        'YY': 0.5,
        'ZZ': 0.3,
    }
    
    # Create grid with SINGLE values for delta, omega1, omega2 (all zero)
    # This way they don't contribute to the Hamiltonian
    grid = generate_custom_grid(
        tau_range=np.linspace(0.1, np.pi, 50),
        delta_range=np.array([0.0]),    # Single zero
        omega1_range=np.array([0.0]),   # Single zero
        omega2_range=np.array([0.0]),   # Single zero
        coefficients=cartan_coeffs
    )
    
    print(f"Coefficients: {cartan_coeffs}")
    print(f"Scanning {len(grid['tau'])} tau values")
    
    df = scan_parameter_space(grid, verbose=False)
    df = add_topology_to_dataframe(df, verbose=False)
    
    print(f"Results: {len(df)} points")
    print(f"\nTopology distribution:")
    print(f"  ν: {dict(df['nu'].value_counts().sort_index())}")
    
    return df


# ============================================================================
# EXAMPLE 2: Your Scan Style - Fixed Coefficients + Varying Parameters
# ============================================================================
# For studying how the AshN parameters affect topology when base interaction
# is defined by coefficients

def example_fixed_coeffs_varying_params():
    """
    Fixed base Hamiltonian (e.g., XX=30) while scanning over 
    tau, delta, omega1, omega2.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Fixed Coefficients + Varying Parameters")
    print("="*70)
    
    # Your coefficient definition
    # Note: This sets XX=30, but no YY! (unlike standard iSWAP)
    Ncoeff = {
        'IX': 0, 'IY': 0, 'IZ': 0,
        'XI': 0, 'XX': 30, 'XY': 0, 'XZ': 0,
        'YI': 0, 'YX': 0, 'YY': 0, 'YZ': 0,
        'ZI': 0, 'ZX': 0, 'ZY': 0, 'ZZ': 0,
    }
    
    # Small test grid
    grid = generate_log_grid(
        n_tau=5,
        n_delta=3,
        n_omega1=3,
        n_omega2=3,
        param_range=(0.1, 1.0),
        coefficients=Ncoeff
    )
    
    # Show non-zero coefficients
    nonzero = {k: v for k, v in Ncoeff.items() if v != 0}
    print(f"Non-zero coefficients: {nonzero}")
    print(f"Grid: {len(grid['tau'])}×{len(grid['delta'])}×{len(grid['omega1'])}×{len(grid['omega2'])}")
    
    df = scan_parameter_space(grid, verbose=False)
    df = add_topology_to_dataframe(df, verbose=False)
    
    print(f"Results: {len(df)} points")
    
    # Note: The actual Hamiltonian will be:
    # H = (delta/2)(ZI + IZ) + (omega1/2)XI + (omega2/2)IX + 30*XX
    # because build_general_hamiltonian ADDS the coefficients
    
    return df


# ============================================================================
# EXAMPLE 3: iSWAP-like with ZZ perturbation
# ============================================================================
# Standard coupling (XX+YY)/2 with varying ZZ interaction

def example_isawp_with_zz():
    """
    Study how ZZ coupling affects topology in an iSWAP-like system.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: iSWAP-like with ZZ perturbation")
    print("="*70)
    
    # iSWAP base + variable ZZ
    coeffs = {
        'XX': 0.5,
        'YY': 0.5,
        'ZZ': 0.0,  # Will be varied via delta scan (trick!)
    }
    
    # Or, for true independent ZZ scanning, use scan_single_coefficient:
    from topoqgate_core import scan_single_coefficient
    
    base_coeffs = {'XX': 0.5, 'YY': 0.5}
    zz_values = np.linspace(-0.5, 0.5, 21)
    tau = np.pi / 2  # Fixed evolution time
    
    df = scan_single_coefficient(base_coeffs, 'ZZ', zz_values, tau, verbose=False)
    # Note: scan_single_coefficient already includes nu1, nu2, nu columns
    
    print(f"Scanning ZZ from {zz_values[0]:.2f} to {zz_values[-1]:.2f}")
    print(f"Results: {len(df)} points at τ = π/2")
    print(f"\nTopology distribution:")
    print(f"  ν: {dict(df['nu'].value_counts().sort_index())}")
    
    return df


# ============================================================================
# EXAMPLE 4: 2D Coefficient Scan (e.g., XX vs ZZ)
# ============================================================================

def example_2d_coefficient_scan():
    """
    2D scan over two coefficients to map topological phase diagram.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: 2D Coefficient Scan (XX vs ZZ)")
    print("="*70)
    
    from topoqgate_core import scan_two_coefficients
    
    # Base Hamiltonian with YY coupling
    base_coeffs = {'YY': 0.5}
    
    # Scan XX and ZZ
    xx_values = np.linspace(0, 1.0, 11)
    zz_values = np.linspace(-0.5, 0.5, 11)
    tau = np.pi / 2
    
    df = scan_two_coefficients(
        base_coeffs, 
        'XX', xx_values, 
        'ZZ', zz_values, 
        tau, 
        verbose=False
    )
    # Note: scan_two_coefficients already includes nu1, nu2, nu columns
    
    print(f"Grid: {len(xx_values)}×{len(zz_values)} = {len(df)} points")
    print(f"\nTopology distribution:")
    print(f"  ν: {dict(df['nu'].value_counts().sort_index())}")
    
    return df

# == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == == ==

# EXAMPLE 5: Fixed H with arbitrary single perturbation
# ============================================================================
# Standard coupling (XX+YY)/2 with varying ZZ interaction


def example_H_with_dh(Hbase={'XX':0.0, 'YY': 0.0 , 'ZZ': 0.0}, var_vals=np.array([1]), var_coeff='XX'):
    """
    Study how single H coupling deltaH affects topology a general system.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Fixed H with arbitrary single perturbation")
    print("=" * 70)

    # H base
    coeffs = Hbase

    # Or, for true independent ZZ scanning, use scan_single_coefficient:
    from topoqgate_core import scan_single_coefficient

    base_coeffs = {key: value for key, value in Hbase.items() if value != 0.0}
    var_values = var_vals
    tau = 1  # Fixed evolution time

    df = scan_single_coefficient(base_coeffs, var_coeff, var_values, tau, verbose=True)
    # Note: scan_single_coefficient already includes nu1, nu2, nu columns

    print("Scanning" + f"{var_coeff} from {var_values[0]:.2f} to {var_values[-1]:.2f}")
    print(f"Results: {len(df)} points at τ =1")
    print(f"\nTopology distribution:")
    print(f"  ν: {dict(df['nu'].value_counts().sort_index())}")

    return df



# ============================================================================
# VERIFICATION: Show what Hamiltonian is actually built
# ============================================================================

def verify_hamiltonian_construction():
    """
    Explicitly show what build_general_hamiltonian produces.
    """
    print("\n" + "="*70)
    print("VERIFICATION: Hamiltonian Construction")
    print("="*70)
    
    # Case 1: Pure coefficients (delta=omega=0)
    coeffs = {'XX': 0.5, 'YY': 0.5, 'ZZ': 0.3}
    H1 = build_general_hamiltonian(0, 0, 0, 0, coeffs)  # tau=0 (not used in building)
    print("\n1. Pure coefficients (delta=0, omega1=0, omega2=0):")
    print(f"   Coefficients: {coeffs}")
    print(f"   H diagonal: {np.diag(H1).real}")
    
    # Case 2: Coefficients + AshN parameters
    H2 = build_general_hamiltonian(0, delta=1.0, omega1=2.0, omega2=0, coefficients=coeffs)
    print("\n2. With AshN parameters (delta=1.0, omega1=2.0):")
    print(f"   The Hamiltonian includes:")
    print(f"   - ZI: 0 + 1.0/2 = 0.5")
    print(f"   - IZ: 0 + 1.0/2 = 0.5") 
    print(f"   - XI: 0 + 2.0/2 = 1.0")
    print(f"   - Plus your coefficients")
    
    # Case 3: Compare with direct coefficient build
    direct_coeffs = {
        'XX': 0.5, 'YY': 0.5, 'ZZ': 0.3,
        'ZI': 0.5, 'IZ': 0.5, 'XI': 1.0
    }
    H3 = build_hamiltonian_from_coefficients(direct_coeffs)
    print("\n3. Direct equivalent:")
    print(f"   Coefficients: {direct_coeffs}")
    print(f"   H2 == H3: {np.allclose(H2, H3)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("TopoQgate: Coefficient-Based Scanning Examples")
    print("="*70)
    
    # Run all examples
    # df1 = example_pure_coefficients()
    # df2 = example_fixed_coeffs_varying_params()
    # df3 = example_isawp_with_zz()
    # df4 = example_2d_coefficient_scan()

    # ###################################### for SWAP perturb ##############################################
    # var_vals = np.linspace(np.pi/4-np.pi/40,np.pi/4+np.pi/40,30)
    # df5 = example_H_with_dh(Hbase={'XX': np.pi / 4, 'YY': np.pi / 4, 'ZZ': np.pi / 4}, var_vals=var_vals, var_coeff='ZZ')
    # save_dataframe(df5, './outputs/SWAP_scan_ZZ.csv')
    # print_summary(df5)
    # ######################################################################################################

    # ###################################### for CNOT perturb ##############################################
    var_vals = np.linspace(np.pi / 4 - np.pi / 40, np.pi / 4 + np.pi / 40, 30)
    df5 = example_H_with_dh(Hbase={'ZI': np.pi/4, 'IX': np.pi/4, 'ZX': -np.pi/4}, var_vals=var_vals, var_coeff='IX')
    save_dataframe(df5, './outputs/CNOT_scan_IX.csv')
    print_summary(df5)
    # ######################################################################################################

    # Show verification
    # verify_hamiltonian_construction()
    
    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70)
