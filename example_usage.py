"""
TopoQgate: Example Usage
=========================

This demonstrates how to use the modular topoqgate system.

Structure:
- topoqgate_core.py: Master module with all core functions
- scan_weyl_space.py: Scanner (configurable grid)
- weyl_analyzer.py: Analysis functions
- THIS FILE: Examples of how to use everything
"""

import os
from topoqgate_core import *
from weyl_analyzer import *
from topology_plots import *

# ============================================================================
# EXAMPLE 1: LOAD EXISTING DATA AND ANALYZE
# ============================================================================

def example_load_and_analyze():
    """Load CSV data and run analysis"""
    
    # OUTPUT_DIR = "/mnt/user-data/outputs"
    OUTPUT_DIR = "./outputs"
    csv_file = os.path.join(OUTPUT_DIR, "weyl_mapping_data.csv")
    
    # Load data (automatically adds topology if not present)
    df = load_weyl_data(csv_file, add_topology=True)
    
    # Print summary
    print_summary(df)
    
    # Clustering analysis
    analyze_clustering(df)
    
    # Visualize
    plot_weyl_distribution_3d(df, OUTPUT_DIR)
    
    # Find transitions
    grid = detect_grid_structure(df)
    transitions = find_topological_transitions(df, grid)
    
    # Save transitions
    if len(transitions) > 0:
        trans_file = os.path.join(OUTPUT_DIR, "transitions.csv")
        save_dataframe(transitions, trans_file)
    
    return df, transitions

# ============================================================================
# EXAMPLE 2: SCAN NEW PARAMETER SPACE
# ============================================================================

def example_custom_scan():
    """Run a custom parameter scan"""
    
    OUTPUT_DIR = "./outputs"
    
    # Define custom grid (smaller for testing)
    grid = generate_log_grid(
        n_tau=10,
        n_delta=8,
        n_omega1=8,
        n_omega2=8,
        param_range=(0.1, 20.0)  # Custom range
    )
    
    # Scan
    df = scan_parameter_space(grid, verbose=True)
    
    # Add topology
    df = add_topology_to_dataframe(df)
    
    # Save
    output_file = os.path.join(OUTPUT_DIR, "custom_scan.csv")
    save_dataframe(df, output_file)
    
    return df

# ============================================================================
# EXAMPLE 3: COMPUTE SINGLE POINT
# ============================================================================

def example_single_point():
    """Compute Weyl coordinates and topology for single H parameter set"""
    
    # Define parameters
    tau = 5.0
    delta = 2.0
    omega1 = 3.0
    omega2 = 3.0
    
    # Get Weyl coordinates
    coords = map_params_to_weyl(tau, delta, omega1, omega2)
    print(f"\nH parameters: τ={tau}, δ={delta}, ω₁={omega1}, ω₂={omega2}")
    print(f"Weyl coordinates: α={coords.alpha/np.pi:.4f}π, β={coords.beta/np.pi:.4f}π, γ={coords.gamma/np.pi:.4f}π")
    
    # Get topology
    nu1, nu2, nu = map_params_to_topology(tau, delta, omega1, omega2)
    print(f"Topology: ν₁={nu1}, ν₂={nu2}, ν={nu}")
    
    return coords, (nu1, nu2, nu)

# ============================================================================
# EXAMPLE 4: QUERY TRANSITIONS
# ============================================================================

def example_query_transitions():
    """Load transitions and query them"""
    
    OUTPUT_DIR = "./outputs"
    trans_file = os.path.join(OUTPUT_DIR, "transitions.csv")
    
    if not os.path.exists(trans_file):
        print("No transitions file found. Run example_load_and_analyze() first.")
        return
    
    trans = pd.read_csv(trans_file)
    
    print(f"\n{'='*80}")
    print("TRANSITION QUERIES")
    print(f"{'='*80}\n")

    print(f"\n✓ Found {len(trans)} transitions")

    print(f"\n{'=' * 80}")
    print(f"\n  By parameter:")
    print(f"\n{'=' * 80}")
    # print(trans['varied_param'].value_counts())
    # Query 1: Transitions caused by all params. w/ %

    print(f"Transitions from:")
    omega1t = len(trans[(trans['varied_param'] == 'omega1') & (trans['delta_nu'] != 0)])
    print(f" ω₁: {omega1t} transitions ({omega1t/(trans['delta_nu'] != 0).sum()*100:.2f}%)")
    omega2t = len(trans[(trans['varied_param'] == 'omega2') & (trans['delta_nu'] != 0)])
    print(f" ω₂: {omega2t} transitions ({omega2t / (trans['delta_nu'] != 0).sum() * 100:.2f}%)")
    taut = len(trans[(trans['varied_param'] == 'tau') & (trans['delta_nu'] != 0)])
    print(f"  τ: {taut} transitions ({taut / (trans['delta_nu'] != 0).sum() * 100:.2f}%)")
    deltat = len(trans[(trans['varied_param'] == 'delta') & (trans['delta_nu'] != 0)])
    print(f"  δ: {deltat} transitions ({deltat / (trans['delta_nu'] != 0).sum() * 100:.2f}%)")

    # Query 4: Transitions at specific parameter value
    # tau_near_5 = trans[(trans['varied_param'] == 'tau') & (abs(trans['from_tau'] - 5.0) < 1.0)]
    # print(f"τ≈5 transitions: {len(tau_near_5)}")

    print(f"\n{'=' * 80}")
    print(f"\n  By topology change:")
    print(f"\n{'=' * 80}")
    print(f"    Δν₁ ≠ 0: {(trans['delta_nu1'] != 0).sum()}")
    print(f"    Δν₂ ≠ 0: {(trans['delta_nu2'] != 0).sum()}")
    print(f"    Δν ≠ 0: {(trans['delta_nu'] != 0).sum()}")
    print(f"    Δν = -2: {(trans['delta_nu'] == -2).sum()}")
    print(f"    Δν = -1: {(trans['delta_nu'] == -1).sum()}")
    print(f"    Δν = +1: {(trans['delta_nu'] == 1).sum()}")
    print(f"    Δν = +2: {(trans['delta_nu'] == 2).sum()}")

    # Query 2: Transitions from ν=0 to ν=+1
    zero_to_plus = trans[(trans['from_nu'] == 0) & (trans['to_nu'] == 1)]
    print(f"ν: 0→+1 transitions: {len(zero_to_plus)}")

    # Query 3: Large topology jumps
    big_jumps = trans[abs(trans['delta_nu']) == 2]
    print(f"Large jumps (|Δν|=2): {len(big_jumps)}")

    print(f"\n{'=' * 80}")

    return trans

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("TopoQgate: Example Usage")
    print("="*80)
    
    # Run example 1: Load and analyze existing data
    # print("\n\nEXAMPLE 1: Load and analyze existing data")
    # print("-"*80)
    # df, transitions = example_load_and_analyze()
    
    # Run example 3: Single point
    # print("\n\nEXAMPLE 3: Single point calculation")
    # print("-"*80)
    # coords, topology = example_single_point()
    
    # Run example 4: Query transitions
    print("\n\nEXAMPLE 4: Query transitions")
    print("-"*80)
    example_query_transitions()
    

    
    # Uncomment to run example 2:
    # print("\n\nEXAMPLE 2: Custom scan")
    # print("-"*80)
    # df_custom = example_custom_scan()

    print("\n\nEXAMPLE 6: Plot Topology Distributions")
    print("-"*80)
    # Load your data
    # df = load_weyl_data("./outputs/weyl_mapping_data.csv", add_topology=True)
    # Create the plot
    # plot_topology_3d_weyl(df, output_dir="./outputs")
    # plot_all_topology_figures(df, output_dir="./outputs")

    print("\n" + "="*80)
    print("✓ ALL EXAMPLES COMPLETE")
    print("="*80)