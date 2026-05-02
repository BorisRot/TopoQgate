# TopoQgate
Quantum Gate Classification via Hamiltonian Decomposition

A Python-based numerical tool for calsifying real-life experimentally constructed 2-qubit gates by their topologal numbers.

Features
- Construction of the Experminatal Hamiltonian - $H_{exp}$ via coeffiecnts $c_i$ and 2 quibit operators ${O_{A_i} \otimes O_{B_j}}_{ij}$
- KAK decompostion of $H_{exp}$ - mapping of the coefficients $c_i$ to the Weyl chamber coordinates $c_{xx}, \, c_{yy}, \, c_{zz}$ with $0 \le |C_{zz}| \le c_{yy}\le c_{xx} \ le \nicefrac{\pi}{4}$
- Calculation of the topological numbers via the Weyl chember coordinates 
- Placment of the cpecific gate in it topological sector in the Weyl chamber
- Stability Analysis - roboustness of the topological clasification to noise in the H_exp coefficients $c_i$ 
