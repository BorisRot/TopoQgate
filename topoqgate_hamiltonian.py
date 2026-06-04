"""
TopoQgate: Generalized Hamiltonian Module
==========================================

Extends topoqgate_core with a general framework for arbitrary two-qubit Hamiltonians.

The most general two-qubit Hamiltonian in su(4) + identity:
    H = Σ_{i,j ∈ {I,X,Y,Z}} t_{ij} (σ_i ⊗ σ_j)

This gives 16 terms (15 traceless + identity).

Physical Classification:
- IDENTITY: II (global energy shift, no effect on dynamics)
- LOCAL Q1: XI, YI, ZI (single-qubit rotations on qubit 1)
- LOCAL Q2: IX, IY, IZ (single-qubit rotations on qubit 2)
- NON-LOCAL: XX, XY, XZ, YX, YY, YZ, ZX, ZY, ZZ (entangling interactions)

Cartan Decomposition:
- h₂ = span{XI, YI, ZI, IX, IY, IZ} → non-entangling
- p₂ = span{XX, XY, XZ, YX, YY, YZ, ZX, ZY, ZZ} → entangling

Only the p₂ terms affect Weyl coordinates (α, β, γ) and topology (ν).
"""

import numpy as np
import scipy.linalg as la
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, field
import pandas as pd

# Import from core module - CRITICAL FOR INTEGRATION
from topoqgate_core import extract_weyl_coordinates, compute_topological_invariants

# ============================================================================
# COMPLETE TWO-QUBIT OPERATOR BASIS
# ============================================================================

# Single-qubit Pauli matrices
I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)

# Complete basis dictionary: all 16 two-qubit Pauli products
PAULI_BASIS = {
    # Identity
    'II': np.kron(I2, I2),
    
    # Local on qubit 1 (left)
    'XI': np.kron(X, I2),
    'YI': np.kron(Y, I2),
    'ZI': np.kron(Z, I2),
    
    # Local on qubit 2 (right)
    'IX': np.kron(I2, X),
    'IY': np.kron(I2, Y),
    'IZ': np.kron(I2, Z),
    
    # Non-local (entangling)
    'XX': np.kron(X, X),
    'XY': np.kron(X, Y),
    'XZ': np.kron(X, Z),
    'YX': np.kron(Y, X),
    'YY': np.kron(Y, Y),
    'YZ': np.kron(Y, Z),
    'ZX': np.kron(Z, X),
    'ZY': np.kron(Z, Y),
    'ZZ': np.kron(Z, Z),
}

# Classification of operators
LOCAL_Q1_OPS = {'XI', 'YI', 'ZI'}
LOCAL_Q2_OPS = {'IX', 'IY', 'IZ'}
LOCAL_OPS = LOCAL_Q1_OPS | LOCAL_Q2_OPS
NONLOCAL_OPS = {'XX', 'XY', 'XZ', 'YX', 'YY', 'YZ', 'ZX', 'ZY', 'ZZ'}

# ============================================================================
# GENERALIZED HAMILTONIAN CLASS
# ============================================================================

@dataclass
class GeneralHamiltonian:
    """
    General two-qubit Hamiltonian with arbitrary terms.
    
    Usage:
        # Method 1: Dictionary
        H = GeneralHamiltonian({'XX': 0.5, 'YY': 0.5, 'ZI': 1.0, 'IZ': 1.0})
        
        # Method 2: Builder pattern
        H = GeneralHamiltonian()
        H.add_term('XX', 0.5).add_term('YY', 0.5).add_term('ZI', 1.0)
        
        # Get matrix
        matrix = H.to_matrix()
        
        # Evolve
        U = H.evolve(tau=5.0)
    """
    coefficients: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        # Validate all keys
        for key in self.coefficients:
            if key not in PAULI_BASIS:
                raise ValueError(f"Unknown operator: {key}. Valid: {list(PAULI_BASIS.keys())}")
    
    def add_term(self, operator: str, coefficient: float) -> 'GeneralHamiltonian':
        """Add a term (chainable)"""
        if operator not in PAULI_BASIS:
            raise ValueError(f"Unknown operator: {operator}")
        self.coefficients[operator] = self.coefficients.get(operator, 0) + coefficient
        return self
    
    def set_term(self, operator: str, coefficient: float) -> 'GeneralHamiltonian':
        """Set a term (overwrites)"""
        if operator not in PAULI_BASIS:
            raise ValueError(f"Unknown operator: {operator}")
        self.coefficients[operator] = coefficient
        return self
    
    def remove_term(self, operator: str) -> 'GeneralHamiltonian':
        """Remove a term"""
        if operator in self.coefficients:
            del self.coefficients[operator]
        return self
    
    def to_matrix(self) -> np.ndarray:
        """Build 4×4 Hamiltonian matrix"""
        H = np.zeros((4, 4), dtype=complex)
        for op, coeff in self.coefficients.items():
            H += coeff * PAULI_BASIS[op]
        return H
    
    def evolve(self, tau: float) -> np.ndarray:
        """Time evolution: U = exp(-i·τ·H)"""
        return la.expm(-1j * tau * self.to_matrix())
    
    def get_local_part(self) -> Dict[str, float]:
        """Extract local (non-entangling) terms"""
        return {k: v for k, v in self.coefficients.items() if k in LOCAL_OPS}
    
    def get_nonlocal_part(self) -> Dict[str, float]:
        """Extract non-local (entangling) terms"""
        return {k: v for k, v in self.coefficients.items() if k in NONLOCAL_OPS}
    
    def local_strength(self) -> float:
        """Total local coefficient magnitude"""
        return sum(abs(v) for k, v in self.coefficients.items() if k in LOCAL_OPS)
    
    def nonlocal_strength(self) -> float:
        """Total non-local coefficient magnitude"""
        return sum(abs(v) for k, v in self.coefficients.items() if k in NONLOCAL_OPS)
    
    def copy(self) -> 'GeneralHamiltonian':
        """Create a copy"""
        return GeneralHamiltonian(self.coefficients.copy())
    
    def __repr__(self):
        terms = [f"{v:+.4f}·{k}" for k, v in sorted(self.coefficients.items()) if abs(v) > 1e-10]
        return "H = " + " ".join(terms) if terms else "H = 0"

# ============================================================================
# HAMILTONIAN BUILDERS (COMMON CONFIGURATIONS)
# ============================================================================

def build_ashn_hamiltonian(delta: float = 0, omega1: float = 0, omega2: float = 0,
                          g: float = 1.0) -> GeneralHamiltonian:
    """
    AshN-style Hamiltonian (normalized by g).
    
    H/g = (δ/2)(ZI + IZ) + (1/2)(XX + YY) + (ω₁/2)XI + (ω₂/2)IX
    
    Args:
        delta: δ = Δ/g (dimensionless detuning)
        omega1: ω₁ = Ω₁/g (dimensionless drive on Q1)
        omega2: ω₂ = Ω₂/g (dimensionless drive on Q2)
        g: coupling strength (default 1 for dimensionless)
    """
    return GeneralHamiltonian({
        'XX': 0.5,
        'YY': 0.5,
        'ZI': delta / 2,
        'IZ': delta / 2,
        'XI': omega1 / 2,
        'IX': omega2 / 2,
    })

def build_heisenberg_hamiltonian(jx: float = 1, jy: float = 1, jz: float = 1,
                                 hx: float = 0, hz: float = 0) -> GeneralHamiltonian:
    """
    Heisenberg XYZ model with external field.
    
    H = Jₓ·XX + Jᵧ·YY + Jᵤ·ZZ + hₓ(XI + IX) + hᵤ(ZI + IZ)
    """
    return GeneralHamiltonian({
        'XX': jx,
        'YY': jy,
        'ZZ': jz,
        'XI': hx,
        'IX': hx,
        'ZI': hz,
        'IZ': hz,
    })

def build_ising_hamiltonian(j: float = 1, hx: float = 0, hz: float = 0) -> GeneralHamiltonian:
    """
    Transverse-field Ising model.
    
    H = J·ZZ + hₓ(XI + IX) + hᵤ(ZI + IZ)
    """
    return GeneralHamiltonian({
        'ZZ': j,
        'XI': hx,
        'IX': hx,
        'ZI': hz,
        'IZ': hz,
    })

def build_xy_hamiltonian(jxy: float = 1, jz: float = 0, delta: float = 0) -> GeneralHamiltonian:
    """
    XY model (exchange interaction) with optional ZZ.
    
    H = Jₓᵧ/2·(XX + YY) + Jᵤ·ZZ + (Δ/2)(ZI + IZ)
    """
    return GeneralHamiltonian({
        'XX': jxy / 2,
        'YY': jxy / 2,
        'ZZ': jz,
        'ZI': delta / 2,
        'IZ': delta / 2,
    })

def build_dzyaloshinskii_moriya(d: float, axis: str = 'z') -> GeneralHamiltonian:
    """
    Dzyaloshinskii-Moriya interaction: D·(σ₁ × σ₂).
    
    For axis='z': H = D·(XY - YX)
    """
    if axis == 'z':
        return GeneralHamiltonian({'XY': d, 'YX': -d})
    elif axis == 'y':
        return GeneralHamiltonian({'ZX': d, 'XZ': -d})
    elif axis == 'x':
        return GeneralHamiltonian({'YZ': d, 'ZY': -d})
    else:
        raise ValueError(f"Unknown axis: {axis}")

# ============================================================================
# WEYL ANALYSIS
# ============================================================================

@dataclass
class WeylAnalysis:
    """Container for complete Weyl chamber analysis"""
    alpha: float
    beta: float
    gamma: float
    nu1: int
    nu2: int
    nu: int
    nonlocal_strength: float
    hamiltonian: 'GeneralHamiltonian'
    tau: float
    
    def __repr__(self):
        return (f"Weyl(α={self.alpha/np.pi:.4f}π, β={self.beta/np.pi:.4f}π, "
                f"γ={self.gamma/np.pi:.4f}π) → ν={self.nu} (ν₁={self.nu1}, ν₂={self.nu2})")

def analyze_hamiltonian(H: GeneralHamiltonian, tau: float) -> WeylAnalysis:
    """
    Complete analysis: Hamiltonian → Weyl coordinates → Topology.
    
    Args:
        H: GeneralHamiltonian instance
        tau: Evolution time (dimensionless)
    
    Returns:
        WeylAnalysis with all computed quantities
    """
    # Evolve
    U = H.evolve(tau)
    
    # Extract Weyl coordinates using core module function
    coords = extract_weyl_coordinates(U)
    alpha, beta, gamma = coords.alpha, coords.beta, coords.gamma
    
    # Handle NaN case
    if np.isnan(alpha):
        return WeylAnalysis(
            alpha=np.nan, beta=np.nan, gamma=np.nan,
            nu1=0, nu2=0, nu=0,
            nonlocal_strength=0,
            hamiltonian=H, tau=tau
        )
    
    # Compute topology using core module function
    nu1, nu2, nu = compute_topological_invariants(alpha, beta, gamma)
    
    # Non-local strength
    nls = alpha**2 + beta**2 + gamma**2
    
    return WeylAnalysis(
        alpha=alpha, beta=beta, gamma=gamma,
        nu1=nu1, nu2=nu2, nu=nu,
        nonlocal_strength=nls,
        hamiltonian=H, tau=tau
    )

# ============================================================================
# PARAMETER SENSITIVITY ANALYSIS
# ============================================================================

def analyze_term_sensitivity(base_H: GeneralHamiltonian, tau: float,
                            term: str, values: np.ndarray) -> pd.DataFrame:
    """
    Analyze how varying a single Hamiltonian term affects Weyl coordinates.
    
    Args:
        base_H: Base Hamiltonian
        tau: Evolution time
        term: Operator to vary (e.g., 'ZZ', 'XY')
        values: Array of coefficient values to test
    
    Returns:
        DataFrame with columns: coeff, alpha, beta, gamma, nu1, nu2, nu
    """
    results = []
    
    for val in values:
        H = base_H.copy()
        H.set_term(term, val)
        analysis = analyze_hamiltonian(H, tau)
        
        results.append({
            'coeff': val,
            'alpha': analysis.alpha,
            'beta': analysis.beta,
            'gamma': analysis.gamma,
            'nu1': analysis.nu1,
            'nu2': analysis.nu2,
            'nu': analysis.nu,
            'nonlocal_strength': analysis.nonlocal_strength,
        })
    
    return pd.DataFrame(results)

def scan_two_terms(base_H: GeneralHamiltonian, tau: float,
                   term1: str, values1: np.ndarray,
                   term2: str, values2: np.ndarray) -> pd.DataFrame:
    """
    2D scan: vary two terms simultaneously.
    
    Returns:
        DataFrame with all parameter combinations
    """
    results = []
    
    for v1 in values1:
        for v2 in values2:
            H = base_H.copy()
            H.set_term(term1, v1)
            H.set_term(term2, v2)
            analysis = analyze_hamiltonian(H, tau)
            
            results.append({
                term1: v1,
                term2: v2,
                'alpha': analysis.alpha,
                'beta': analysis.beta,
                'gamma': analysis.gamma,
                'nu1': analysis.nu1,
                'nu2': analysis.nu2,
                'nu': analysis.nu,
            })
    
    return pd.DataFrame(results)

# ============================================================================
# MAPPING NONLOCAL TERMS TO WEYL CHAMBER
# ============================================================================

def analyze_nonlocal_contributions(tau: float = np.pi/2, 
                                  coeff_range: Tuple[float, float] = (-2, 2),
                                  n_points: int = 50) -> Dict[str, pd.DataFrame]:
    """
    Systematically analyze how each non-local term maps to Weyl coordinates.
    
    For each non-local operator (XX, XY, XZ, YX, YY, YZ, ZX, ZY, ZZ),
    evolve H = coeff · Operator and extract Weyl coordinates.
    
    Args:
        tau: Evolution time
        coeff_range: Range of coefficients to test
        n_points: Number of points
    
    Returns:
        Dictionary mapping operator name to DataFrame
    """
    coeffs = np.linspace(coeff_range[0], coeff_range[1], n_points)
    results = {}
    
    print("Analyzing non-local term contributions to Weyl coordinates...")
    print(f"τ = {tau:.4f}, coefficient range = {coeff_range}")
    print("-" * 60)
    
    for op in NONLOCAL_OPS:
        data = []
        for c in coeffs:
            H = GeneralHamiltonian({op: c})
            analysis = analyze_hamiltonian(H, tau)
            data.append({
                'coeff': c,
                'alpha': analysis.alpha,
                'beta': analysis.beta,
                'gamma': analysis.gamma,
                'nu': analysis.nu,
            })
        
        df = pd.DataFrame(data).dropna()
        results[op] = df
        
        # Summary
        if len(df) > 0:
            print(f"{op}: α ∈ [{df['alpha'].min()/np.pi:.3f}π, {df['alpha'].max()/np.pi:.3f}π], "
                  f"β ∈ [{df['beta'].min()/np.pi:.3f}π, {df['beta'].max()/np.pi:.3f}π], "
                  f"γ ∈ [{df['gamma'].min()/np.pi:.3f}π, {df['gamma'].max()/np.pi:.3f}π]")
    
    print("-" * 60)
    return results

# ============================================================================
# WEYL CHAMBER THEORY FOR SPECIFIC TERMS
# ============================================================================

def theoretical_weyl_for_pure_terms():
    """
    Print theoretical predictions for pure non-local Hamiltonians.
    
    For H = c·Op evolved for time τ:
    U = exp(-i·c·τ·Op)
    
    Known results:
    - XX only: (α, β, γ) = (|cτ| mod π/2, 0, 0)
    - YY only: (α, β, γ) = (|cτ| mod π/2, 0, 0) [locally equivalent to XX]
    - ZZ only: (α, β, γ) = (0, 0, |cτ| mod π/2)
    - XX + YY (exchange): (α, β, γ) = (|cτ|, |cτ|, 0) [iSWAP family]
    """
    print("="*70)
    print("THEORETICAL WEYL COORDINATES FOR PURE NON-LOCAL TERMS")
    print("="*70)
    print()
    print("For U = exp(-i·c·τ·Op), before Weyl chamber folding:")
    print()
    print("Diagonal terms (commute with computational basis):")
    print("  ZZ: (α, β, γ) → (0, 0, |cτ|)")
    print()
    print("Off-diagonal terms:")
    print("  XX: (α, β, γ) → (|cτ|, 0, 0)")
    print("  YY: (α, β, γ) → (|cτ|, 0, 0)  [locally equiv. to XX]")
    print()
    print("Mixed terms (create asymmetric entanglement):")
    print("  XY, YX: Mix α and β")
    print("  XZ, ZX: Mix α and γ")
    print("  YZ, ZY: Mix β and γ")
    print()
    print("Common combinations:")
    print("  XX + YY (exchange): (|cτ|, |cτ|, 0) → iSWAP at cτ = π/4")
    print("  XX + YY + ZZ (Heisenberg): (|cτ|, |cτ|, |cτ|) → SWAP at cτ = π/4")
    print("  XX + YY + δZZ: Control γ/α ratio → control topology")
    print()
    print("="*70)

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("TopoQgate: Generalized Hamiltonian Module Demo")
    print("="*70)

    # ============================================================================
    # Example 1: Build custom Hamiltonian
    # ============================================================================
    print("\n1. Building custom Hamiltonian:")
    H = GeneralHamiltonian()
    H.add_term('XX', np.pi/4).add_term('YY', np.pi/4).add_term('ZZ', np.pi/4)
    # H.add_term('ZI', 1.0).add_term('IZ', 1.0)
    print(f"   {H}")
    print(f"   Local part: {H.get_local_part()}")
    print(f"   Non-local part: {H.get_nonlocal_part()}")

    # ============================================================================
    # # Example 2: Analyze evolution
    # ============================================================================
    print("\n2. Analyzing evolution at τ = gt:")
    analysis = analyze_hamiltonian(H, tau=1)
    print(f"   {analysis}")
    #

    # ============================================================================
    # # Example 3: Compare Hamiltonians
    # ============================================================================

    # print("\n3. Comparing different Hamiltonians:")
    #
    # hamiltonians = {
    #     'AshN (δ=2, ω₁=1)': build_ashn_hamiltonian(delta=2, omega1=1, omega2=0),
    #     'Heisenberg XYZ': build_heisenberg_hamiltonian(jx=1, jy=1, jz=1),
    #     'Ising + field': build_ising_hamiltonian(j=1, hx=0.5),
    #     'XY + ZZ': build_xy_hamiltonian(jxy=1, jz=0.5),
    # }
    #
    # tau = np.pi / 2
    # for name, H in hamiltonians.items():
    #     analysis = analyze_hamiltonian(H, tau)
    #     if not np.isnan(analysis.alpha):
    #         print(f"   {name}:")
    #         print(f"      Weyl: ({analysis.alpha/np.pi:.3f}π, {analysis.beta/np.pi:.3f}π, {analysis.gamma/np.pi:.3f}π)")
    #         print(f"      Topology: ν = {analysis.nu}")

    # ============================================================================
    # Example 4: Term sensitivity
    # ============================================================================

    print("\n4. ZZ term sensitivity (varying ?? coefficient):")
    # base_H = build_ashn_hamiltonian(delta=0, omega1=0, omega2=0)
    base_H = H
    # zz_values = np.linspace(-np.pi/4-np.pi/40, np.pi/4+np.pi/40, 30)
    xx_values = np.linspace(np.pi / 4 - np.pi / 40, np.pi / 4 + np.pi / 40, 30)
    df = analyze_term_sensitivity(base_H, tau=1, term='XX', values=xx_values)
    print(df[['coeff', 'alpha', 'beta', 'gamma', 'nu']].to_string(index=False))

    # ============================================================================
    # Example 5: Theory
    # ============================================================================


    # print("\n5. Theoretical predictions:")
    # theoretical_weyl_for_pure_terms()
    #
    print("\n✓ Demo complete!")
