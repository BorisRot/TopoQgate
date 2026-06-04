"""
TopoQgate: Topology Visualization Module (Improved)
====================================================

Creates 3 separate figures instead of one heavy 9-panel plot:
- Figure 1: Histograms (3 panels)
- Figure 2: 3D Weyl chamber scatter plots (3 panels)
- Figure 3: 2D projections (3 panels)

Imports from topoqgate_core - modular design.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import os

# Import core functionality
from topoqgate_core import *

# ============================================================================
# WEYL CHAMBER BOUNDARY VISUALIZATION
# ============================================================================

def plot_weyl_chamber_edges(ax, color='black', linewidth=1.5, alpha=0.8):
    """
    Draw Weyl chamber boundary edges with black lines.

    Weyl chamber constraints: π/4 ≥ α ≥ β ≥ |γ|

    Args:
        ax: 3D matplotlib axis
        color: Edge color
        linewidth: Line thickness
        alpha: Line transparency
    """
    pi4 = np.pi / 4

    # Define key vertices of the Weyl chamber tetrahedron
    vertices = {
        'Id': (0, 0, 0),                    # (0, 0, 0)
        'CNOT': (pi4, 0, 0),               # (π/4, 0, 0)       CNOT gate
        'alpha_beta_max': (pi4, pi4, 0),        # (π/4, π/4, 0)
        'SWAP': (pi4, pi4, pi4),        # (π/4, π/4, π/4) - SWAP gate
        'SWAP_dag': (pi4, pi4, -pi4),       # (π/4, π/4, -π/4)
        'alpha_gamma_pos': (pi4, 0, pi4),       # (π/4, 0, π/4)
        'alpha_gamma_neg': (pi4, 0, -pi4),      # (π/4, 0, -π/4)
    }

    # Define edges connecting vertices
    edges = [
        # Bottom face ( α = π/4 plane)
        ('SWAP', 'CNOT'),
        ('CNOT', 'SWAP_dag'),
        ('SWAP_dag', 'SWAP'),

        # Positive CNOT SWAP_dag Id edges
        ('Id', 'CNOT'),
        ('Id', 'SWAP_dag'),

        # Negative Id SWAP edges
        ('Id', 'SWAP'),

    ]

    # Draw all edges
    for v1, v2 in edges:
        p1 = vertices[v1]
        p2 = vertices[v2]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]],
               color=color, linewidth=linewidth, alpha=alpha)


def map_topology_to_colors(nu_values):
    """
    Map topology values to discrete colors.

    Returns array of color strings.
    """
    color_map = {
        -2: '#00008B',  # Dark blue
        -1: '#4169E1',  # Royal blue
        0: '#FFA500',  # Orange
        1: '#32CD32',  # Lime green
        2: '#006400'  # Dark green
    }
    return [color_map.get(nu, '#808080') for nu in nu_values]

# ============================================================================
# FIGURE 1: HISTOGRAMS
# ============================================================================

def plot_topology_histograms(df: pd.DataFrame,
                             output_dir: str = "/mnt/user-data/outputs",
                             filename: str = "topology_histograms.png"):
    """
    Figure 1: Topology histograms (3 panels in one row).

    Shows distribution of ν₁, ν₂, and ν values.

    Args:
        df: DataFrame with nu1, nu2, nu columns
        output_dir: Directory to save figure
        filename: Output filename
    """
    print("Creating topology histograms...")

    # Ensure topology is computed
    if 'nu1' not in df.columns:
        df = add_topology_to_dataframe(df, verbose=False)

    # Create figure with 1 row, 3 columns
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    # Panel 1: ν₁ histogram
    nu1_counts = df['nu1'].value_counts().sort_index()
    nu1_counts.plot(kind='bar', ax=ax1, color='steelblue', alpha=0.8, edgecolor='black')
    ax1.set_xlabel('ν₁', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Count', fontsize=14)
    ax1.set_title('Distribution of ν₁', fontsize=15, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=0)
    ax1.tick_params(labelsize=12)

    # Panel 2: ν₂ histogram
    nu2_counts = df['nu2'].value_counts().sort_index()
    nu2_counts.plot(kind='bar', ax=ax2, color='coral', alpha=0.8, edgecolor='black')
    ax2.set_xlabel('ν₂', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Count', fontsize=14)
    ax2.set_title('Distribution of ν₂', fontsize=15, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=0)
    ax2.tick_params(labelsize=12)

    # Panel 3: ν histogram
    nu_counts = df['nu'].value_counts().sort_index()
    nu_counts.plot(kind='bar', ax=ax3, color='mediumseagreen', alpha=0.8, edgecolor='black')
    ax3.set_xlabel('ν = ν₁ + ν₂', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Count', fontsize=14)
    ax3.set_title('Distribution of ν', fontsize=15, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)
    ax3.tick_params(labelsize=12)

    plt.tight_layout()

    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.show()

# ============================================================================
# FIGURE 2: 3D WEYL CHAMBER SCATTER PLOTS
# ============================================================================

def plot_topology_3d_weyl(df: pd.DataFrame,
                          output_dir: str = "/mnt/user-data/outputs",
                          filename: str = "topology_3d_weyl.png"):
    """
    Figure 2: 3D Weyl chamber scatter plots (3 panels in one row).

    Shows Weyl chamber colored by ν₁, ν₂, and ν.
    Uses custom view: α→-z, β→-x direction.

    Args:
        df: DataFrame with alpha, beta, gamma, nu1, nu2, nu columns
        output_dir: Directory to save figure
        filename: Output filename
    """
    print("Creating 3D Weyl chamber plots...")

    # Ensure topology is computed
    if 'nu1' not in df.columns:
        df = add_topology_to_dataframe(df, verbose=False)

    # Create figure with 1 row, 3 columns
    fig = plt.figure(figsize=(20, 6))

    # Custom view angle: α→down, β→left
    # elev: elevation angle (looking from above if high)
    # azim: azimuth angle (rotation around z-axis)
    elevation = 280
    azimuth = 135  # Rotates so β points left, α points away

    # Panel 1: Colored by ν₁
    ax1 = fig.add_subplot(131, projection='3d')

    # Draw Weyl chamber edges
    plot_weyl_chamber_edges(ax1, color='black', linewidth=1.5, alpha=0.7)

    # Scatter plot
    # scatter1 = ax1.scatter(df['alpha'], df['beta'], df['gamma'],
    #                       c=df['nu1'],
    #                       cmap='RdBu_r',
    #                       s=1.5,
    #                       alpha=0.5,
    #                       vmin=-2, vmax=2)
    colors1 = map_topology_to_colors(df['nu1'])
    scatter1 = ax1.scatter(df['alpha'], df['beta'], df['gamma'],
                           c=colors1,
                           s=1.5,
                           alpha=0.5)


    ax1.set_xlabel('α', fontsize=13, fontweight='bold', labelpad=8)
    ax1.set_ylabel('β', fontsize=13, fontweight='bold', labelpad=8)
    ax1.set_zlabel('γ', fontsize=13, fontweight='bold', labelpad=8)
    ax1.set_title('Weyl Chamber colored by ν₁', fontsize=14, fontweight='bold', pad=15)
    ax1.view_init(elev=elevation, azim=azimuth)

    # cbar1 = plt.colorbar(scatter1, ax=ax1, shrink=0.6, pad=0.1)
    # cbar1.set_label('ν₁', fontsize=12, fontweight='bold')
    # cbar1.set_ticks([-2, -1, 0, 1, 2])
    # Create legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#00008B', label='ν=-2'),
        Patch(facecolor='#4169E1', label='ν=-1'),
        Patch(facecolor='#FFA500', label='ν=0'),
        Patch(facecolor='#32CD32', label='ν=1'),
        Patch(facecolor='#006400', label='ν=2')
    ]
    ax1.legend(handles=legend_elements, loc='upper left', fontsize=9)

    # Panel 2: Colored by ν₂
    ax2 = fig.add_subplot(132, projection='3d')

    plot_weyl_chamber_edges(ax2, color='black', linewidth=1.5, alpha=0.7)

    # scatter2 = ax2.scatter(df['alpha'], df['beta'], df['gamma'],
    #                       c=df['nu2'],
    #                       cmap='RdBu_r',
    #                       s=1.5,
    #                       alpha=0.5,
    #                       vmin=-2, vmax=2)
    colors2 = map_topology_to_colors(df['nu2'])
    scatter2 = ax2.scatter(df['alpha'], df['beta'], df['gamma'],
                           c=colors2,
                           s=1.5,
                           alpha=0.5)

    ax2.set_xlabel('α', fontsize=13, fontweight='bold', labelpad=8)
    ax2.set_ylabel('β', fontsize=13, fontweight='bold', labelpad=8)
    ax2.set_zlabel('γ', fontsize=13, fontweight='bold', labelpad=8)
    ax2.set_title('Weyl Chamber colored by ν₂', fontsize=14, fontweight='bold', pad=15)
    ax2.view_init(elev=elevation, azim=azimuth)

    # cbar2 = plt.colorbar(scatter2, ax=ax2, shrink=0.6, pad=0.1)
    # cbar2.set_label('ν₂', fontsize=12, fontweight='bold')
    # cbar2.set_ticks([-2, -1, 0, 1, 2])
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#00008B', label='ν=-2'),
        Patch(facecolor='#4169E1', label='ν=-1'),
        Patch(facecolor='#FFA500', label='ν=0'),
        Patch(facecolor='#32CD32', label='ν=1'),
        Patch(facecolor='#006400', label='ν=2')
    ]
    ax2.legend(handles=legend_elements, loc='upper left', fontsize=9)

    # Panel 3: Colored by ν
    ax3 = fig.add_subplot(133, projection='3d')

    plot_weyl_chamber_edges(ax3, color='black', linewidth=1.5, alpha=0.7)

    # scatter3 = ax3.scatter(df['alpha'], df['beta'], df['gamma'],
    #                       c=df['nu'],
    #                       cmap='RdBu_r',
    #                       s=1.5,
    #                       alpha=0.5,
    #                       vmin=-2, vmax=2)
    colors3 = map_topology_to_colors(df['nu'])
    scatter3 = ax3.scatter(df['alpha'], df['beta'], df['gamma'],
                           c=colors3,
                           s=1.5,
                           alpha=0.5)

    ax3.set_xlabel('α', fontsize=13, fontweight='bold', labelpad=8)
    ax3.set_ylabel('β', fontsize=13, fontweight='bold', labelpad=8)
    ax3.set_zlabel('γ', fontsize=13, fontweight='bold', labelpad=8)
    ax3.set_title('Weyl Chamber colored by ν', fontsize=14, fontweight='bold', pad=15)
    ax3.view_init(elev=elevation, azim=azimuth)

    # cbar3 = plt.colorbar(scatter3, ax=ax3, shrink=0.6, pad=0.1)
    # cbar3.set_label('ν', fontsize=12, fontweight='bold')
    # cbar3.set_ticks([-2, -1, 0, 1, 2])
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#00008B', label='ν=-2'),
        Patch(facecolor='#4169E1', label='ν=-1'),
        Patch(facecolor='#FFA500', label='ν=0'),
        Patch(facecolor='#32CD32', label='ν=1'),
        Patch(facecolor='#006400', label='ν=2')
    ]
    ax3.legend(handles=legend_elements, loc='upper left', fontsize=9)

    plt.tight_layout()

    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.show()

# ============================================================================
# FIGURE 3: 2D PROJECTIONS
# ============================================================================

def plot_topology_2d_projections(df: pd.DataFrame,
                                 output_dir: str = "/mnt/user-data/outputs",
                                 filename: str = "topology_2d_projections.png"):
    """
    Figure 3: 2D projections (3 panels in one row).

    Shows α-β, α-γ, and β-γ planes colored by topology.

    Args:
        df: DataFrame with alpha, beta, gamma, nu1, nu2, nu columns
        output_dir: Directory to save figure
        filename: Output filename
    """
    print("Creating 2D projection plots...")

    # Ensure topology is computed
    if 'nu1' not in df.columns:
        df = add_topology_to_dataframe(df, verbose=False)

    # Create figure
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6))

    # Color map for discrete topology values
    color_map = {
        -2: 'darkblue',
        -1: 'blue',
        0: 'orange',
        1: 'green',
        2: 'darkgreen'
    }

    # Panel 1: α-β plane by ν₁
    unique_nu1 = sorted(df['nu1'].unique())
    for nu_val in unique_nu1:
        mask = df['nu1'] == nu_val
        ax1.scatter(df[mask]['alpha']/np.pi,
                   df[mask]['beta']/np.pi,
                   s=3,
                   alpha=0.5,
                   color=color_map.get(nu_val, 'gray'),
                   label=f'ν₁={nu_val}')

    ax1.set_xlabel('α/π', fontsize=14, fontweight='bold')
    ax1.set_ylabel('β/π', fontsize=14, fontweight='bold')
    ax1.set_title('α-β Plane by ν₁', fontsize=15, fontweight='bold')
    ax1.legend(fontsize=11, loc='best', framealpha=0.9)
    ax1.grid(True, alpha=0.3)
    ax1.plot([0, 0.25], [0, 0.25], 'k--', alpha=0.5, linewidth=1, label='α=β')
    ax1.set_aspect('equal')
    ax1.tick_params(labelsize=11)

    # Panel 2: α-γ plane by ν
    unique_nu = sorted(df['nu'].unique())
    for nu_val in unique_nu:
        mask = df['nu'] == nu_val
        ax2.scatter(df[mask]['alpha']/np.pi,
                   df[mask]['gamma']/np.pi,
                   s=3,
                   alpha=0.5,
                   color=color_map.get(nu_val, 'gray'),
                   label=f'ν={nu_val}')

    ax2.set_xlabel('α/π', fontsize=14, fontweight='bold')
    ax2.set_ylabel('γ/π', fontsize=14, fontweight='bold')
    ax2.set_title('α-γ Plane by ν', fontsize=15, fontweight='bold')
    ax2.legend(fontsize=11, loc='best', framealpha=0.9)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(0, color='k', linestyle='--', alpha=0.5, linewidth=1, label='γ=0')
    ax2.tick_params(labelsize=11)

    # Panel 3: β-γ plane by ν
    for nu_val in unique_nu:
        mask = df['nu'] == nu_val
        ax3.scatter(df[mask]['beta']/np.pi,
                   df[mask]['gamma']/np.pi,
                   s=3,
                   alpha=0.5,
                   color=color_map.get(nu_val, 'gray'),
                   label=f'ν={nu_val}')

    ax3.set_xlabel('β/π', fontsize=14, fontweight='bold')
    ax3.set_ylabel('γ/π', fontsize=14, fontweight='bold')
    ax3.set_title('β-γ Plane by ν', fontsize=15, fontweight='bold')
    ax3.legend(fontsize=11, loc='best', framealpha=0.9)
    ax3.grid(True, alpha=0.3)
    ax3.axhline(0, color='k', linestyle='--', alpha=0.5, linewidth=1, label='γ=0')
    ax3.tick_params(labelsize=11)

    plt.tight_layout()

    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {save_path}")
    plt.show()

# ============================================================================
# CONVENIENCE FUNCTION: GENERATE ALL 3 FIGURES
# ============================================================================

def plot_all_topology_figures(df: pd.DataFrame,
                               output_dir: str = "/mnt/user-data/outputs"):
    """
    Generate all 3 topology figures at once.

    Args:
        df: DataFrame with topology data
        output_dir: Directory to save figures
    """
    print("\n" + "="*80)
    print("GENERATING ALL TOPOLOGY FIGURES")
    print("="*80 + "\n")

    plot_topology_histograms(df, output_dir)
    print()
    plot_topology_3d_weyl(df, output_dir)
    print()
    plot_topology_2d_projections(df, output_dir)

    print("\n" + "="*80)
    print("✓ ALL TOPOLOGY FIGURES GENERATED")
    print("="*80)

