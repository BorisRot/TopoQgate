# TopoQgate
Quantum Gate Classification via Hamiltonian Decomposition

A Python-based numerical tool for calsifying real-life experimentally constructed 2-qubit gates by their topologal numbers.

Features
- Construction of the Experminatal Hamiltonian - $H_{exp}$ via coeffiecnts $c_i$ and 2 quibit operators ${\, O_{A_i} \otimes O_{B_j} \,}_{ij}$
- KAK decompostion of $H_{exp}$ - mapping of the coefficients $c_i$ to the Weyl chamber coordinates $c_{xx}, \, c_{yy}, \, c_{zz}$ with $0 \le |C_{zz}| \le c_{yy}\le c_{xx} \ le \frac{\pi}{4}$
- Calculation of the topological numbers via the Weyl chember coordinates 
- Placment of the cpecific gate in it topological sector in the Weyl chamber
- Stability Analysis - roboustness of the topological clasification to noise in the H_exp coefficients $c_i$ 



# TopoQgate: Modular Code Structure
**📁 File Organization
Core Module (Import This!)
topoqgate_core.py          ← MASTER MODULE - all core functions
Contains:

Pauli matrices (XX, YY, ZZ, XI, IX, etc.)
Weyl coordinate extraction
Topological invariant computation
Hamiltonian builder
Grid generation
Parameter space scanning
Data loading/saving utilities
All other scripts import from this!

# Application Scripts (Run These!)
scan_weyl_space.py         ← Scan H parameters → Weyl chamber
weyl_analyzer.py           ← Analysis functions (visualization, transitions)
example_usage.py           ← Examples of how to use everything


# 🎯 How to Use
1. Configure and Run Scanner
  Edit scan_weyl_space.py lines 17-24:
  
  # CHANGE THESE TO CONFIGURE GRID
  N_TAU = 15      # Time points
  N_DELTA = 12    # Detuning points  
  N_OMEGA1 = 12   # Drive 1 points
  N_OMEGA2 = 12   # Drive 2 points
  
  PARAM_MIN = 0.05   # Minimum parameter value
  PARAM_MAX = 50.0   # Maximum parameter value
  
  OUTPUT_DIR = "/mnt/user-data/outputs"  # Or "./outputs" for Windows
  OUTPUT_FILE = "weyl_mapping_data.csv"
  Then run:
  
  python scan_weyl_space.py
  For your 120k points, set:
  
  N_TAU = 30      # 30 points
  N_DELTA = 20    # 20 points
  N_OMEGA1 = 20   # 20 points
  N_OMEGA2 = 20   # 20 points
  Total: 30×20×20×20 = 240,000 points (adjust as needed)
  
2. Load and Analyze Data
  from topoqgate_core import *
  from weyl_analyzer import *
  
  Load existing CSV (automatically adds topology)
  df = load_weyl_data("weyl_mapping_data.csv", add_topology=True)
  
  Print summary
  print_summary(df)
  
  Clustering analysis
  analyze_clustering(df)
  
  Visualize
  plot_weyl_distribution_3d(df, output_dir="./outputs")
  
  Find transitions
  grid = detect_grid_structure(df)
  transitions = find_topological_transitions(df, grid)
  
  Save transitions
  save_dataframe(transitions, "transitions.csv")
3. Compute Single Point
  from topoqgate_core import map_params_to_weyl, map_params_to_topology
  
  **Get Weyl coordinates**
  coords = map_params_to_weyl(tau=5.0, delta=2.0, omega1=3.0, omega2=3.0)
  print(coords.alpha, coords.beta, coords.gamma)
  
  **Get topology**
  nu1, nu2, nu = map_params_to_topology(5.0, 2.0, 3.0, 3.0)
  print(nu1, nu2, nu)
  4. Query Transitions
  import pandas as pd
  
  **Load transitions**
  trans = pd.read_csv("topological_transitions.csv")
  
  **Find transitions caused by ω₂**
  omega2_trans = trans[trans['varied_param'] == 'omega2']
  
  **Find ν: 0→+1 transitions**
  zero_to_plus = trans[(trans['from_nu'] == 0) & (trans['to_nu'] == 1)]
  
  **Find large jumps**
  big_jumps = trans[abs(trans['delta_nu']) == 2]
  
  **Find transitions at specific parameter value**
  tau_at_5 = trans[(trans['varied_param'] == 'tau') & 
                   (abs(trans['from_tau'] - 5.0) < 1.0)]

                   
# ➕ Adding New Features
The RIGHT way (don't rewrite everything!):

Example: Add new visualization function
Create new file: my_new_plots.py

from topoqgate_core import *
import matplotlib.pyplot as plt

def plot_my_awesome_thing(df):
    """Your new plot function"""
    # Use df['alpha'], df['beta'], df['gamma'], df['nu1'], etc.
    plt.figure()
    # ... your plotting code ...
    plt.show()
Use it:

from topoqgate_core import load_weyl_data
from my_new_plots import plot_my_awesome_thing

df = load_weyl_data("weyl_mapping_data.csv")
plot_my_awesome_thing(df)
Example: Add new analysis function
Create: my_analysis.py

from topoqgate_core import *

def my_sensitivity_analysis(df):
    """Your analysis function"""
    # Compute stuff using df
    result = ...
    return result
Use it:

from topoqgate_core import load_weyl_data
from my_analysis import my_sensitivity_analysis

df = load_weyl_data("weyl_mapping_data.csv", add_topology=True)
results = my_sensitivity_analysis(df)
📊 Data Files
Input Data
weyl_mapping_data.csv          ← Raw H→Weyl mapping (from scanner)
Columns: tau, delta, omega1, omega2, alpha, beta, gamma

After loading with add_topology=True:
Added columns: nu1, nu2, nu

Output Data
weyl_mapping_enhanced.csv      ← With topology added
topological_transitions.csv    ← All transitions (12,879 records)
Transitions file columns:

varied_param: Which H parameter changed
from_tau, from_delta, from_omega1, from_omega2: Initial H
to_tau, to_delta, to_omega1, to_omega2: Modified H
from_alpha, from_beta, from_gamma: Initial Weyl
to_alpha, to_beta, to_gamma: Modified Weyl
from_nu1, from_nu2, from_nu: Initial topology
to_nu1, to_nu2, to_nu: Modified topology
delta_nu1, delta_nu2, delta_nu: Changes


# 🔧 Available Functions in Core
From topoqgate_core.py:
Grid & Scanning:

generate_log_grid(n_tau, n_delta, n_omega1, n_omega2, param_range) → Dict
scan_parameter_space(grid, verbose) → DataFrame
Mapping:

map_params_to_weyl(tau, delta, omega1, omega2) → WeylCoordinates
map_params_to_topology(tau, delta, omega1, omega2) → (ν₁, ν₂, ν)
Topology:

compute_topological_invariants(alpha, beta, gamma) → (ν₁, ν₂, ν)
add_topology_to_dataframe(df) → DataFrame with nu1, nu2, nu
Data I/O:

load_weyl_data(filepath, add_topology) → DataFrame
save_dataframe(df, filepath)
print_summary(df)
Grid Analysis:

detect_grid_structure(df) → Dict with grid info
Low-level:

build_dimensionless_hamiltonian(delta, omega1, omega2) → H matrix
evolve_hamiltonian(H, tau) → U matrix
extract_weyl_coordinates(U) → WeylCoordinates
From weyl_analyzer.py:
Visualization:

plot_weyl_distribution_3d(df, output_dir, filename)
plot_weyl_chamber_boundaries(ax)
add_known_gates(ax)
Analysis:

find_topological_transitions(df, grid_structure) → DataFrame
analyze_clustering(df) → prints statistics


# 🚀 Quick Start Examples
Run Full Analysis Pipeline
python example_usage.py
Custom Grid Scan

**Edit scan_weyl_space.py to set N_TAU, N_DELTA, etc.**
python scan_weyl_space.py
Interactive Python Session
from topoqgate_core import *

**Compute one point**
coords = map_params_to_weyl(5.0, 2.0, 3.0, 3.0)
nu1, nu2, nu = compute_topological_invariants(coords.alpha, coords.beta, coords.gamma)
print(f"ν = {nu}")

**Load and query data**
df = load_weyl_data("weyl_mapping_data.csv", add_topology=True)
trivial_gates = df[df['nu'] == 0]
print(f"Trivial gates: {len(trivial_gates)}/{len(df)}")

# 🎯 Summary
To scan: Edit scan_weyl_space.py grid parameters → Run To analyze: Import from topoqgate_core and weyl_analyzer To add features: Create new file → Import from core → Add functions To query data: Load CSV with pandas → Query with standard pandas operations

Never rewrite the core module! Just import and build on top. 🚀
