"""
TopoQgate Core Module
====================

Master module containing all core functionality:
- Pauli matrices
- General Hamiltonian building
- Weyl coordinate extraction
- Topological invariant computation
- Grid generation with coefficient support
- Parameter space scanning
- Basic plotting utilities

All other scripts should import from this module.
"""

import numpy as np
import scipy.linalg as la
from typing import Tuple, Dict, Optional, Union, List
import pandas as pd
from dataclasses import dataclass

# ============================================================================
# PAULI MATRICES & OPERATORS
# ============================================================================

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)

# Two-qubit operators
XX = np.kron(X, X)
YY = np.kron(Y, Y)
ZZ = np.kron(Z, Z)
IX = np.kron(I2, X)
XI = np.kron(X, I2)
IZ = np.kron(I2, Z)
ZI = np.kron(Z, I2)
IY = np.kron(I2, Y)
YI = np.kron(Y, I2)
ZX = np.kron(Z, X)
XZ = np.kron(X, Z)
XY = np.kron(X, Y)
YX = np.kron(Y, X)
YZ = np.kron(Y, Z)
ZY = np.kron(Z, Y)
II = np.kron(I2, I2)

# Complete Pauli basis dictionary (all 16 terms)
PAULI_BASIS = {
    'II': II, 'IX': IX, 'IY': IY, 'IZ': IZ,
    'XI': XI, 'XX': XX, 'XY': XY, 'XZ': XZ,
    'YI': YI, 'YX': YX, 'YY': YY, 'YZ': YZ,
    'ZI': ZI, 'ZX': ZX, 'ZY': ZY, 'ZZ': ZZ,
}

# Classification
LOCAL_OPS = {'XI', 'YI', 'ZI', 'IX', 'IY', 'IZ'}
NONLOCAL_OPS = {'XX', 'XY', 'XZ', 'YX', 'YY', 'YZ', 'ZX', 'ZY', 'ZZ'}

# ============================================================================
# QISKIT INTERFACE
# ============================================================================

try:
    from qiskit.synthesis.two_qubit import TwoQubitWeylDecomposition
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

# ============================================================================
# WEYL COORDINATES
# ============================================================================

@dataclass
class WeylCoordinates:
    """Container for Weyl chamber coordinates"""
    alpha: float
    beta: float
    gamma: float

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.alpha, self.beta, self.gamma)

    def to_dict(self) -> Dict[str, float]:
        return {'alpha': self.alpha, 'beta': self.beta, 'gamma': self.gamma}

def extract_weyl_coordinates(U: np.ndarray) -> WeylCoordinates:
    """
    Extract Weyl coordinates from unitary using Qiskit KAK decomposition.

    Args:
        U: 4×4 unitary matrix

    Returns:
        WeylCoordinates(α, β, γ) or WeylCoordinates(nan, nan, nan) if failed
    """
    if not QISKIT_AVAILABLE:
        return WeylCoordinates(np.nan, np.nan, np.nan)

    try:
        decomp = TwoQubitWeylDecomposition(U)
        return WeylCoordinates(decomp.a, decomp.b, decomp.c)
    except:
        return WeylCoordinates(np.nan, np.nan, np.nan)

# ============================================================================
# TOPOLOGICAL INVARIANTS
# ============================================================================

def compute_topological_invariants(alpha: float, beta: float, gamma: float) -> Tuple[int, int, int]:
    """
    Compute topological invariants from Weyl coordinates.

    From Orion & Akkermans Eqs. 38-40:
    - ν₁: controlled by γ vs (α - β)
    - ν₂: controlled by γ vs (α + β)
    - ν = ν₁ + ν₂

    Args:
        alpha, beta, gamma: Weyl coordinates

    Returns:
        (ν₁, ν₂, ν)
    """
    if np.isnan(alpha):
        return (0, 0, 0)

    # Equation (38)
    threshold1 = alpha - beta
    if gamma > threshold1:
        nu1 = +1
    elif gamma < -threshold1:
        nu1 = -1
    else:
        nu1 = 0

    # Equation (39)
    threshold2 = alpha + beta
    if gamma > threshold2:
        nu2 = +1
    elif gamma < -threshold2:
        nu2 = -1
    else:
        nu2 = 0

    # Equation (40)
    nu = nu1 + nu2

    return (nu1, nu2, nu)

# ============================================================================
# GENERAL HAMILTONIAN BUILDING
# ============================================================================


def build_hamiltonian_from_coefficients(coefficients: Dict[str, float]) -> np.ndarray:
    """
    Build general two-qubit Hamiltonian from coefficient dictionary.

    H = Σ_{ij} t_{ij} (σ_i ⊗ σ_j)

    Args:
        coefficients: Dictionary mapping operator names to coefficients
                     e.g., {'XX': 0.5, 'YY': 0.5, 'ZI': 1.0}

    Returns:
        4×4 Hamiltonian matrix
    """
    H = np.zeros((4, 4), dtype=complex)
    for op, coeff in coefficients.items():
        if op not in PAULI_BASIS:
            raise ValueError(f"Unknown operator: {op}. Valid: {list(PAULI_BASIS.keys())}")
        if coeff != 0:  # Skip zero coefficients for efficiency
            H += coeff * PAULI_BASIS[op]
    return H

def build_general_hamiltonian(tau: float, delta: float, omega1: float, omega2: float,
                              coefficients: Optional[Dict[str, float]] = None) -> np.ndarray:
    """
    Build general Hamiltonian combining AshN-style parameters with arbitrary coefficients.

    The Hamiltonian is:
        H = (δ/2)(ZI + IZ) + (ω₁/2)XI + (ω₂/2)IX + Σ coefficients[op] * op

    Note: If coefficients contains 'XX' or 'YY', they ADD to any base values.
    For pure coefficient-based Hamiltonian, set delta=omega1=omega2=0.

    Args:
        tau: Evolution time (not used in building, but kept for API consistency)
        delta: Detuning parameter
        omega1: Drive 1 amplitude
        omega2: Drive 2 amplitude
        coefficients: Additional/override coefficients for any Pauli terms

    Returns:
        4×4 Hamiltonian matrix
    """
    # Start with empty coefficients
    all_coeffs = {
        'ZI': delta / 2,
        'IZ': delta / 2,
        'XI': omega1 / 2,
        'IX': omega2 / 2,
    }

    # Add user-specified coefficients
    if coefficients:
        for op, coeff in coefficients.items():
            if op in all_coeffs:
                all_coeffs[op] += coeff
            else:
                all_coeffs[op] = coeff

    return build_hamiltonian_from_coefficients(all_coeffs)

def evolve_hamiltonian(H: np.ndarray, tau: float) -> np.ndarray:
    """
    Time evolution: U = exp(-i·τ·H)

    Args:
        H: Hamiltonian matrix
        tau: Dimensionless time (τ = gt)

    Returns:
        Unitary evolution operator
    """
    return la.expm(-1j * tau * H)

# ============================================================================
# BACKWARD COMPATIBLE: OLD FUNCTION SIGNATURES
# ============================================================================

def build_dimensionless_hamiltonian(delta: float, omega1: float, omega2: float,
                                    tzz: float = 0, tzx: float = 0, txz: float = 0) -> np.ndarray:
    """
    Build dimensionless Hamiltonian H/g (backward compatible version).

    H/g = (δ/2)(ZI + IZ) + (1/2)(XX + YY) + (ω₁/2)XI + (ω₂/2)IX + tzz*ZZ + tzx*ZX + txz*XZ

    For new code, use build_general_hamiltonian() or build_hamiltonian_from_coefficients().
    """
    coefficients = {
        'XX': 0.5,
        'YY': 0.5,
        'ZI': delta / 2,
        'IZ': delta / 2,
        'XI': omega1 / 2,
        'IX': omega2 / 2,
        'ZZ': tzz,
        'ZX': tzx,
        'XZ': txz,
    }
    return build_hamiltonian_from_coefficients(coefficients)

# ============================================================================
# PARAMETER → WEYL MAPPING
# ============================================================================

def map_params_to_weyl(tau: float, delta: float = 0, omega1: float = 0, omega2: float = 0,
                       coefficients: Optional[Dict[str, float]] = None) -> WeylCoordinates:
    """
    Map Hamiltonian parameters to Weyl coordinates.

    Args:
        tau: τ = gt (dimensionless time)
        delta: δ = Δ/g (dimensionless detuning)
        omega1: ω₁ = Ω₁/g (dimensionless drive 1)
        omega2: ω₂ = Ω₂/g (dimensionless drive 2)
        coefficients: Additional Pauli term coefficients

    Returns:
        WeylCoordinates(α, β, γ)
    """
    H = build_general_hamiltonian(tau, delta, omega1, omega2, coefficients)
    U = evolve_hamiltonian(H, tau)
    return extract_weyl_coordinates(U)

def map_params_to_topology(tau: float, delta: float = 0, omega1: float = 0, omega2: float = 0,
                           coefficients: Optional[Dict[str, float]] = None) -> Tuple[int, int, int]:
    """
    Map H parameters directly to topological invariants.

    Returns:
        (ν₁, ν₂, ν)
    """
    coords = map_params_to_weyl(tau, delta, omega1, omega2, coefficients)
    return compute_topological_invariants(coords.alpha, coords.beta, coords.gamma)

def map_hamiltonian_to_weyl(H: np.ndarray, tau: float) -> WeylCoordinates:
    """
    Map a Hamiltonian matrix directly to Weyl coordinates.

    Args:
        H: 4×4 Hamiltonian matrix
        tau: Evolution time

    Returns:
        WeylCoordinates(α, β, γ)
    """
    U = evolve_hamiltonian(H, tau)
    return extract_weyl_coordinates(U)

def map_hamiltonian_to_topology(H: np.ndarray, tau: float) -> Tuple[int, int, int]:
    """
    Map a Hamiltonian matrix directly to topological invariants.

    Args:
        H: 4×4 Hamiltonian matrix
        tau: Evolution time

    Returns:
        (ν₁, ν₂, ν)
    """
    coords = map_hamiltonian_to_weyl(H, tau)
    return compute_topological_invariants(coords.alpha, coords.beta, coords.gamma)

# ============================================================================
# GRID GENERATION
# ============================================================================

def generate_log_grid(n_tau: int = 15, n_delta: int = 12,
                     n_omega1: int = 12, n_omega2: int = 12,
                     param_range: Tuple[float, float] = (0.05, 50.0),
                     coefficients: Optional[Dict[str, float]] = None) -> Dict:
    """
    Generate logarithmic grid in dimensionless parameter space.

    Args:
        n_tau, n_delta, n_omega1, n_omega2: Number of points per dimension
        param_range: (min, max) for all parameters
        coefficients: Fixed Hamiltonian coefficients to use during scan

    Returns:
        Dictionary with parameter arrays and coefficients
    """
    min_val, max_val = param_range

    grid = {
        'tau': np.logspace(np.log10(min_val), np.log10(max_val), n_tau),
        'delta': np.logspace(np.log10(min_val), np.log10(max_val), n_delta),
        'omega1': np.logspace(np.log10(min_val), np.log10(max_val), n_omega1),
        'omega2': np.logspace(np.log10(min_val), np.log10(max_val), n_omega2),
        'coefficients': coefficients if coefficients else {},
    }

    return grid

def generate_linear_grid(n_tau: int = 15, n_delta: int = 12,
                        n_omega1: int = 12, n_omega2: int = 12,
                        param_range: Tuple[float, float] = (0.0, 10.0),
                        coefficients: Optional[Dict[str, float]] = None) -> Dict:
    """
    Generate linear grid in dimensionless parameter space.

    Args:
        n_tau, n_delta, n_omega1, n_omega2: Number of points per dimension
        param_range: (min, max) for all parameters
        coefficients: Fixed Hamiltonian coefficients to use during scan

    Returns:
        Dictionary with parameter arrays and coefficients
    """
    min_val, max_val = param_range

    grid = {
        'tau': np.linspace(min_val, max_val, n_tau),
        'delta': np.linspace(min_val, max_val, n_delta),
        'omega1': np.linspace(min_val, max_val, n_omega1),
        'omega2': np.linspace(min_val, max_val, n_omega2),
        'coefficients': coefficients if coefficients else {},
    }

    return grid

def generate_custom_grid(tau_range: np.ndarray = None,
                        delta_range: np.ndarray = None,
                        omega1_range: np.ndarray = None,
                        omega2_range: np.ndarray = None,
                        coefficients: Optional[Dict[str, float]] = None) -> Dict:
    """
    Generate grid with custom parameter ranges.

    Args:
        tau_range, delta_range, omega1_range, omega2_range: Custom arrays
        coefficients: Fixed Hamiltonian coefficients

    Returns:
        Dictionary with parameter arrays and coefficients
    """
    grid = {
        'tau': tau_range if tau_range is not None else np.array([np.pi/4]),
        'delta': delta_range if delta_range is not None else np.array([0.0]),
        'omega1': omega1_range if omega1_range is not None else np.array([0.0]),
        'omega2': omega2_range if omega2_range is not None else np.array([0.0]),
        'coefficients': coefficients if coefficients else {},
    }

    return grid

# ============================================================================
# PARAMETER SPACE SCANNING
# ============================================================================

def scan_parameter_space(grid: Dict, verbose: bool = True) -> pd.DataFrame:
    """
    Scan full 4D parameter space and map to Weyl chamber.

    Args:
        grid: Dictionary with parameter ranges and coefficients
              (from generate_log_grid, generate_linear_grid, or generate_custom_grid)
        verbose: Print progress

    Returns:
        DataFrame with columns: tau, delta, omega1, omega2, alpha, beta, gamma
        Also includes coefficient columns if non-zero coefficients were used
    """
    import time

    tau_range = grid['tau']
    delta_range = grid['delta']
    omega1_range = grid['omega1']
    omega2_range = grid['omega2']
    coefficients = grid.get('coefficients', {})

    total_points = len(tau_range) * len(delta_range) * len(omega1_range) * len(omega2_range)

    if verbose:
        print(f"\n{'='*80}")
        print(f"SCANNING PARAMETER SPACE")
        print(f"{'='*80}")
        print(f"Grid: {len(tau_range)}×{len(delta_range)}×{len(omega1_range)}×{len(omega2_range)}")
        print(f"Total points: {total_points:,}")
        print(f"τ range: [{tau_range[0]:.4f}, {tau_range[-1]:.4f}]")
        print(f"δ range: [{delta_range[0]:.4f}, {delta_range[-1]:.4f}]")
        print(f"ω₁ range: [{omega1_range[0]:.4f}, {omega1_range[-1]:.4f}]")
        print(f"ω₂ range: [{omega2_range[0]:.4f}, {omega2_range[-1]:.4f}]")
        if coefficients:
            nonzero = {k: v for k, v in coefficients.items() if v != 0}
            if nonzero:
                print(f"Fixed coefficients: {nonzero}")
        print(f"{'='*80}\n")

    results = []
    start_time = time.time()
    count = 0
    failed = 0

    for tau in tau_range:
        for delta in delta_range:
            for omega1 in omega1_range:
                for omega2 in omega2_range:
                    # Build Hamiltonian with all parameters
                    H = build_general_hamiltonian(tau, delta, omega1, omega2, coefficients)
                    U = evolve_hamiltonian(H, tau)
                    coords = extract_weyl_coordinates(U)

                    if np.isnan(coords.alpha):
                        failed += 1

                    # Build result row
                    row = {
                        'tau': tau, 'delta': delta,
                        'omega1': omega1, 'omega2': omega2,
                        **coords.to_dict()
                    }

                    results.append(row)

                    count += 1
                    if verbose and count % 5000 == 0:
                        elapsed = time.time() - start_time
                        rate = count / elapsed
                        remaining = (total_points - count) / rate
                        print(f"Progress: {count:,}/{total_points:,} ({100*count/total_points:.1f}%) | "
                              f"Rate: {rate:.0f} pts/s | ETA: {remaining:.0f}s | Failed: {failed}")

    elapsed = time.time() - start_time

    if verbose:
        print(f"\n{'='*80}")
        print(f"SCAN COMPLETE")
        print(f"{'='*80}")
        print(f"Time: {elapsed:.1f}s | Rate: {total_points/elapsed:.0f} pts/s")
        print(f"Failed: {failed}/{total_points} ({100*failed/total_points:.1f}%)")
        print(f"{'='*80}\n")

    df = pd.DataFrame(results)
    df_clean = df.dropna()

    if verbose:
        print(f"Clean points: {len(df_clean):,}/{len(df):,}\n")

    return df_clean

def scan_single_coefficient(base_coefficients: Dict[str, float],
                           vary_term: str,
                           vary_range: np.ndarray,
                           tau: float,
                           verbose: bool = True) -> pd.DataFrame:
    """
    Scan a single coefficient while keeping others fixed.

    Args:
        base_coefficients: Base Hamiltonian coefficients
        vary_term: Which term to vary (e.g., 'ZZ', 'XY')
        vary_range: Values to scan
        tau: Evolution time
        verbose: Print progress

    Returns:
        DataFrame with coefficient value and Weyl coordinates
    """
    if verbose:
        print(f"Scanning {vary_term} over {len(vary_range)} values at τ = {tau:.4f}")

    results = []

    for val in vary_range:
        coeffs = base_coefficients.copy()
        coeffs[vary_term] = val

        H = build_hamiltonian_from_coefficients(coeffs)
        coords = map_hamiltonian_to_weyl(H, tau)
        nu1, nu2, nu = compute_topological_invariants(coords.alpha, coords.beta, coords.gamma)

        results.append({
            vary_term: val,
            'alpha': coords.alpha,
            'beta': coords.beta,
            'gamma': coords.gamma,
            'nu1': nu1,
            'nu2': nu2,
            'nu': nu,
        })

    return pd.DataFrame(results)

def scan_two_coefficients(base_coefficients: Dict[str, float],
                         term1: str, range1: np.ndarray,
                         term2: str, range2: np.ndarray,
                         tau: float,
                         verbose: bool = True) -> pd.DataFrame:
    """
    2D scan over two coefficients.

    Args:
        base_coefficients: Base Hamiltonian coefficients
        term1, term2: Terms to vary
        range1, range2: Value ranges
        tau: Evolution time
        verbose: Print progress

    Returns:
        DataFrame with all combinations
    """
    total = len(range1) * len(range2)
    if verbose:
        print(f"Scanning {term1}×{term2}: {len(range1)}×{len(range2)} = {total} points")

    results = []

    for v1 in range1:
        for v2 in range2:
            coeffs = base_coefficients.copy()
            coeffs[term1] = v1
            coeffs[term2] = v2

            H = build_hamiltonian_from_coefficients(coeffs)
            coords = map_hamiltonian_to_weyl(H, tau)
            nu1, nu2, nu = compute_topological_invariants(coords.alpha, coords.beta, coords.gamma)

            results.append({
                term1: v1,
                term2: v2,
                'alpha': coords.alpha,
                'beta': coords.beta,
                'gamma': coords.gamma,
                'nu1': nu1,
                'nu2': nu2,
                'nu': nu,
            })

    return pd.DataFrame(results)

# ============================================================================
# TOPOLOGY COMPUTATION FOR DATAFRAME
# ============================================================================

def add_topology_to_dataframe(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Add ν₁, ν₂, ν columns to dataframe.

    Args:
        df: DataFrame with alpha, beta, gamma columns
        verbose: Print progress

    Returns:
        DataFrame with added nu1, nu2, nu columns
    """
    if verbose:
        print("Computing topological invariants...")

    results = []
    for _, row in df.iterrows():
        nu1, nu2, nu = compute_topological_invariants(row['alpha'], row['beta'], row['gamma'])
        results.append({'nu1': nu1, 'nu2': nu2, 'nu': nu})

    topology_df = pd.DataFrame(results)
    df_with_topology = pd.concat([df.reset_index(drop=True), topology_df], axis=1)

    if verbose:
        print(f"✓ Topology computed for {len(df)} points\n")

    return df_with_topology

# ============================================================================
# DATA LOADING
# ============================================================================

def load_weyl_data(filepath: str, add_topology: bool = True, verbose: bool = True) -> pd.DataFrame:
    """
    Load CSV data and optionally add topology.

    Args:
        filepath: Path to CSV file
        add_topology: Whether to compute ν₁, ν₂, ν if not present
        verbose: Print info

    Returns:
        DataFrame with all data
    """
    if verbose:
        print(f"Loading: {filepath}")

    df = pd.read_csv(filepath)

    if verbose:
        print(f"✓ Loaded {len(df)} points")

    # Add topology if requested and not present
    if add_topology and 'nu1' not in df.columns:
        df = add_topology_to_dataframe(df, verbose)

    if verbose:
        print(f"\nColumns: {list(df.columns)}")

        if 'nu1' in df.columns:
            print(f"\nTopology distribution:")
            print(f"  ν₁: {dict(df['nu1'].value_counts().sort_index())}")
            print(f"  ν₂: {dict(df['nu2'].value_counts().sort_index())}")
            print(f"  ν:  {dict(df['nu'].value_counts().sort_index())}")

    return df

# ============================================================================
# GRID STRUCTURE DETECTION
# ============================================================================

def detect_grid_structure(df: pd.DataFrame, verbose: bool = True) -> Dict:
    """
    Detect regular grid structure from data.

    Returns:
        Dictionary with unique values and counts for each parameter
    """
    structure = {}

    for param in ['tau', 'delta', 'omega1', 'omega2']:
        if param in df.columns:
            unique_vals = np.sort(df[param].unique())
            structure[param] = unique_vals
            structure[f'{param}_n'] = len(unique_vals)

    if verbose:
        print("\nGrid structure:")
        for param in ['tau', 'delta', 'omega1', 'omega2']:
            if f'{param}_n' in structure:
                print(f"  {param}: {structure[f'{param}_n']} points")
        print(f"  Total: {len(df)} points\n")

    return structure

# ============================================================================
# UTILITIES
# ============================================================================

def save_dataframe(df: pd.DataFrame, filepath: str, verbose: bool = True):
    """Save dataframe to CSV"""
    df.to_csv(filepath, index=False)
    if verbose:
        print(f"✓ Saved: {filepath}")

def print_summary(df: pd.DataFrame):
    """Print summary statistics"""
    print(f"\n{'='*80}")
    print("DATA SUMMARY")
    print(f"{'='*80}")

    # H parameters
    if 'tau' in df.columns:
        print(f"H Parameters:")
        for param in ['tau', 'delta', 'omega1', 'omega2']:
            if param in df.columns:
                print(f"  {param}: [{df[param].min():.4f}, {df[param].max():.4f}]")

    # Weyl coordinates
    if 'alpha' in df.columns:
        print(f"\nWeyl Coordinates:")
        for coord in ['alpha', 'beta', 'gamma']:
            print(f"  {coord}: [{df[coord].min()/np.pi:.4f}π, {df[coord].max()/np.pi:.4f}π]")

    # Topology
    if 'nu1' in df.columns:
        print(f"\nTopology:")
        print(f"  ν₁: {dict(df['nu1'].value_counts().sort_index())}")
        print(f"  ν₂: {dict(df['nu2'].value_counts().sort_index())}")
        print(f"  ν:  {dict(df['nu'].value_counts().sort_index())}")

    print(f"{'='*80}\n")

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("TopoQgate Core Module - Test")
    print("="*70)

    # Test 1: Build Hamiltonian from coefficients
    print("\n1. Building Hamiltonian from coefficients:")
    coeffs = {'XX': 0.5, 'YY': 0.5, 'ZZ': 0.3, 'ZI': 0.5, 'IZ': 0.5}
    H = build_hamiltonian_from_coefficients(coeffs)
    print(f"   Coefficients: {coeffs}")
    print(f"   H shape: {H.shape}")

    # Test 2: Map to Weyl
    print("\n2. Mapping to Weyl coordinates:")
    tau = np.pi / 2
    coords = map_hamiltonian_to_weyl(H, tau)
    print(f"   τ = {tau:.4f}")
    print(f"   Weyl: ({coords.alpha/np.pi:.4f}π, {coords.beta/np.pi:.4f}π, {coords.gamma/np.pi:.4f}π)")

    # Test 3: Compute topology
    print("\n3. Computing topology:")
    nu1, nu2, nu = compute_topological_invariants(coords.alpha, coords.beta, coords.gamma)
    print(f"   ν₁={nu1}, ν₂={nu2}, ν={nu}")

    # Test 4: Generate grid with coefficients
    print("\n4. Generating grid with coefficients:")
    grid = generate_log_grid(
        n_tau=3, n_delta=3, n_omega1=3, n_omega2=3,
        param_range=(0.1, 1.0),
        coefficients={'XX': 0.5, 'YY': 0.5}
    )
    print(f"   Grid has {len(grid['tau'])}×{len(grid['delta'])}×{len(grid['omega1'])}×{len(grid['omega2'])} points")
    print(f"   Coefficients stored: {grid['coefficients']}")

    # Test 5: Scan (small test)
    print("\n5. Small parameter scan:")
    df = scan_parameter_space(grid, verbose=False)
    print(f"   Scanned {len(df)} points")
    print(f"   Columns: {list(df.columns)}")

    print("\n✓ All tests passed!")