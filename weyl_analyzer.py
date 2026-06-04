"""
TopoQgate: Analysis Module
===========================

Analysis functions for Weyl mapping data.
Imports core functionality from topoqgate_core.

Contains:
- Visualization functions
- Clustering analysis  
- Transition detection
- Sensitivity analysis
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import pandas as pd
from scipy.stats import gaussian_kde
from typing import Tuple, Dict, List, Optional
import os

# Import core functionality
from topoqgate_core import *

# ============================================================================
# VISUALIZATION: WEYL CHAMBER
# ============================================================================

def plot_weyl_chamber_boundaries(ax, alpha: float = 0.2, color: str = 'gray'):
    """Plot Weyl chamber boundary surfaces: π/4 ≥ α ≥ β ≥ |γ|"""
    pi4 = np.pi / 4
    n = 30
    
    # Face 1: α = π/4 (top)
    beta_f1 = np.linspace(0, pi4, n)
    gamma_f1 = np.linspace(-pi4, pi4, n)
    B1, G1 = np.meshgrid(beta_f1, gamma_f1)
    A1 = np.full_like(B1, pi4)
    mask1 = B1 >= np.abs(G1)
    A1[~mask1] = np.nan
    ax.plot_surface(A1, B1, G1, alpha=alpha, color=color, edgecolor='none')
    
    # Face 2: α = β (diagonal)
    alpha_f2 = np.linspace(0, pi4, n)
    gamma_f2 = np.linspace(-pi4, pi4, n)
    A2, G2 = np.meshgrid(alpha_f2, gamma_f2)
    B2 = A2.copy()
    mask2 = B2 >= np.abs(G2)
    A2[~mask2] = np.nan
    ax.plot_surface(A2, B2, G2, alpha=alpha, color=color, edgecolor='none')
    
    # Face 3: β = |γ| (lower)
    alpha_f3 = np.linspace(0, pi4, n)
    beta_f3 = np.linspace(0, pi4, n)
    A3, B3 = np.meshgrid(alpha_f3, beta_f3)
    G3_pos = B3.copy()
    G3_neg = -B3.copy()
    mask3 = A3 >= B3
    A3_masked = A3.copy()
    A3_masked[~mask3] = np.nan
    ax.plot_surface(A3_masked, B3, G3_pos, alpha=alpha, color=color, edgecolor='none')
    ax.plot_surface(A3_masked, B3, G3_neg, alpha=alpha, color=color, edgecolor='none')

def add_known_gates(ax, marker_size: int = 100):
    """Add markers for known quantum gates"""
    gates = {
        'CNOT': (np.pi/4, 0, 0, 'red', '^'),
        'iSWAP': (np.pi/4, np.pi/4, 0, 'blue', 's'),
        'SWAP': (np.pi/4, np.pi/4, np.pi/4, 'green', 'o'),
        'B': (np.pi/4, np.pi/8, 0, 'purple', 'D'),
    }
    
    for name, (a, b, g, color, marker) in gates.items():
        ax.scatter([a], [b], [g], s=marker_size, c=color, marker=marker,
                  edgecolors='black', linewidths=2, label=name, zorder=10)

# ============================================================================
# VISUALIZATION: 3D WEYL DISTRIBUTION
# ============================================================================

def plot_weyl_distribution_3d(df: pd.DataFrame, output_dir: str = "/mnt/user-data/outputs",
                              filename: str = "weyl_distribution.png"):
    """3D scatter plot of Weyl points with density coloring"""
    df = df.dropna()
    
    if len(df) == 0:
        print("No data to plot!")
        return
    
    # Compute density
    print("Computing density...")
    try:
        points = np.vstack([df['alpha'], df['beta'], df['gamma']])
        kde = gaussian_kde(points)
        density = kde(points)
        density = density / density.max()
    except:
        density = np.ones(len(df))
    
    fig = plt.figure(figsize=(18, 14))
    
    # Main view
    ax1 = fig.add_subplot(221, projection='3d')
    ax1.view_init(elev=20, azim=45)
    plot_weyl_chamber_boundaries(ax1, alpha=0.15)
    scatter = ax1.scatter(df['alpha'], df['beta'], df['gamma'],
                         c=density, cmap='hot_r', s=3, alpha=0.6)
    add_known_gates(ax1, marker_size=150)
    ax1.set_xlabel('α', fontsize=13, fontweight='bold')
    ax1.set_ylabel('β', fontsize=13, fontweight='bold')
    ax1.set_zlabel('γ', fontsize=13, fontweight='bold')
    ax1.set_title('Weyl Chamber (Color = Density)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=10)
    plt.colorbar(scatter, ax=ax1, shrink=0.5, label='Density')
    
    # Top view
    ax2 = fig.add_subplot(222, projection='3d')
    ax2.view_init(elev=60, azim=30)
    plot_weyl_chamber_boundaries(ax2, alpha=0.15)
    ax2.scatter(df['alpha'], df['beta'], df['gamma'],
               c=density, cmap='hot_r', s=3, alpha=0.6)
    add_known_gates(ax2, marker_size=150)
    ax2.set_xlabel('α', fontsize=12)
    ax2.set_ylabel('β', fontsize=12)
    ax2.set_zlabel('γ', fontsize=12)
    ax2.set_title('Top View', fontsize=13, fontweight='bold')
    
    # Projections
    ax3 = fig.add_subplot(223)
    h3 = ax3.hexbin(df['alpha']/np.pi, df['beta']/np.pi, gridsize=50, cmap='hot', mincnt=1)
    ax3.set_xlabel('α/π', fontsize=12, fontweight='bold')
    ax3.set_ylabel('β/π', fontsize=12, fontweight='bold')
    ax3.set_title('α-β projection', fontsize=12, fontweight='bold')
    ax3.plot([0, 0.25], [0, 0.25], 'k--', alpha=0.5, label='α=β')
    ax3.legend(fontsize=9)
    plt.colorbar(h3, ax=ax3, label='Count')
    
    ax4 = fig.add_subplot(224)
    h4 = ax4.hexbin(df['alpha']/np.pi, df['gamma']/np.pi, gridsize=50, cmap='hot', mincnt=1)
    ax4.set_xlabel('α/π', fontsize=12, fontweight='bold')
    ax4.set_ylabel('γ/π', fontsize=12, fontweight='bold')
    ax4.set_title('α-γ projection', fontsize=12, fontweight='bold')
    ax4.axhline(0, color='k', linestyle='--', alpha=0.5)
    plt.colorbar(h4, ax=ax4, label='Count')
    
    plt.tight_layout()
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.show()

# ============================================================================
# TRANSITION DETECTION
# ============================================================================

def find_topological_transitions(df: pd.DataFrame, grid_structure: Dict,
                                verbose: bool = True) -> pd.DataFrame:
    """
    Find all single-parameter changes that cause topology change.
    
    Args:
        df: DataFrame with H parameters and topology
        grid_structure: Grid structure from detect_grid_structure()
        verbose: Print progress
    
    Returns:
        DataFrame with transition records
    """
    if verbose:
        print("\nFinding topological transitions...")
    
    # Ensure topology is computed
    if 'nu1' not in df.columns:
        df = add_topology_to_dataframe(df, verbose=False)
    
    transitions = []
    params = ['tau', 'delta', 'omega1', 'omega2']
    
    # Sort for efficient lookup
    df_sorted = df.sort_values(params).reset_index(drop=True)
    
    # Build lookup table
    # Key: (tau_idx, delta_idx, omega1_idx, omega2_idx)
    # Value: row index in df
    ## Example lookup table:
    # lookup = {
    #     (0, 0, 0, 0): 0,      # First point in dataframe
    #     (0, 0, 0, 1): 1,      # Second point
    #     (0, 0, 0, 2): 2,
    #     ...
    #     (14, 11, 11, 11): 25919  # Last point
    # }
    for idx, row in df_sorted.iterrows():
        key = tuple(np.argmin(np.abs(grid_structure[p] - row[p])) for p in params)
        lookup[key] = idx
    
    if verbose:
        print(f"  Lookup table: {len(lookup)} entries")
    
    # Find transitions
    count = 0
    for key, idx in lookup.items():
        row = df_sorted.iloc[idx]
        
        # Check each direction
        for param_idx, param_name in enumerate(params):
            # Try neighbor in +1 direction
            neighbor_key = list(key)
            neighbor_key[param_idx] += 1
            neighbor_key = tuple(neighbor_key)
            
            if neighbor_key in lookup:
                neighbor_idx = lookup[neighbor_key]
                neighbor = df_sorted.iloc[neighbor_idx]
                
                # Check topology change
                if (row['nu1'] != neighbor['nu1'] or 
                    row['nu2'] != neighbor['nu2'] or 
                    row['nu'] != neighbor['nu']):
                    
                    transitions.append({
                        'from_idx': idx,
                        'to_idx': neighbor_idx,
                        'varied_param': param_name,
                        **{f'from_{p}': row[p] for p in params},
                        **{f'to_{p}': neighbor[p] for p in params},
                        **{f'from_{c}': row[c] for c in ['alpha', 'beta', 'gamma']},
                        **{f'to_{c}': neighbor[c] for c in ['alpha', 'beta', 'gamma']},
                        **{f'from_{n}': row[n] for n in ['nu1', 'nu2', 'nu']},
                        **{f'to_{n}': neighbor[n] for n in ['nu1', 'nu2', 'nu']},
                        **{f'delta_{n}': neighbor[n] - row[n] for n in ['nu1', 'nu2', 'nu']},
                    })
                    count += 1
        
        if verbose and (idx + 1) % 5000 == 0:
            print(f"  Processed {idx+1}/{len(df_sorted)}, found {count} transitions")
    
    trans_df = pd.DataFrame(transitions)
    
    if verbose and len(trans_df) > 0:
        print(f"\n✓ Found {len(trans_df)} transitions")
        print(f"\n  By parameter:")
        print(trans_df['varied_param'].value_counts())
        print(f"\n  By topology change:")
        print(f"    Δν₁ ≠ 0: {(transitions_df['delta_nu1'] != 0).sum()}")
        print(f"    Δν₂ ≠ 0: {(transitions_df['delta_nu2'] != 0).sum()}")
        print(f"    Δν ≠ 0: {(transitions_df['delta_nu'] != 0).sum()}")
    
    return trans_df

# ============================================================================
# CLUSTERING ANALYSIS
# ============================================================================

def analyze_clustering(df: pd.DataFrame):
    """Compute and print clustering statistics"""
    print(f"\n{'='*80}")
    print("CLUSTERING ANALYSIS")
    print(f"{'='*80}\n")
    
    # Statistics
    print("Weyl Coordinate Statistics:")
    for coord in ['alpha', 'beta', 'gamma']:
        mean = df[coord].mean() / np.pi
        std = df[coord].std() / np.pi
        print(f"  {coord}: mean={mean:.4f}π, std={std:.4f}π")
    
    # Coverage
    alpha_cov = (df['alpha'].max() - df['alpha'].min()) / (np.pi/4)
    beta_cov = (df['beta'].max() - df['beta'].min()) / (np.pi/4)
    gamma_cov = (df['gamma'].max() - df['gamma'].min()) / (np.pi/2)
    
    print(f"\nWeyl Chamber Coverage:")
    print(f"  α: {100*alpha_cov:.1f}% of [0, π/4]")
    print(f"  β: {100*beta_cov:.1f}% of [0, π/4]")
    print(f"  γ: {100*gamma_cov:.1f}% of [-π/4, π/4]")
    
    # Density
    n_bins = 20
    hist, _ = np.histogramdd(
        np.column_stack([df['alpha'], df['beta'], df['gamma']]),
        bins=n_bins
    )
    
    occupied = np.sum(hist > 0)
    total = n_bins**3
    
    print(f"\nDensity Metrics:")
    print(f"  Occupied bins: {occupied}/{total} ({100*occupied/total:.1f}%)")
    print(f"  Max density: {hist.max():.0f} points")
    print(f"  Mean density: {hist[hist>0].mean():.1f} points")
    
    # High-density regions
    threshold = np.percentile(hist[hist>0], 90)
    high_dens = hist > threshold
    points_high = hist[high_dens].sum()
    
    print(f"  High-density bins (>90th): {high_dens.sum()}")
    print(f"  Points in high-density: {points_high:.0f} ({100*points_high/len(df):.1f}%)")
    
    print(f"\n{'='*80}\n")
