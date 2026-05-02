# TopoQgate
Quantum Gate Classification via Hamiltonian Decomposition

A Python-based numerical tool for calsifying real-life experimentally constructed 2-qubit gates by their topologal numbers.

Features
- Construction of the Experminatal Hamiltonian - H_exp via coeffiecnts c_i and 2 quibit operators {O_A_i \otimes O_B_j}_ij
- KAK decompostion of H_exp - mapping of the coefficients c_i to the Weyl chamber coordinates C_xx, C_yy, C_zz with 0<=|C_ZZ|<= C_yy <= C_XX
- Calculation of the topological numbers via the Weyl chember coordinates 
- Placment of the cpecific gate in it topological sector in the Weyl chamber
- Stability Analysis - roboustness of the topological clasification to noise in the H_exp coefficients c_i 
