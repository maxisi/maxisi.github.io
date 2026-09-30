---
layout: post
title: "A probability density for drawing injections in a selection-function study"
date: 2023-03-06 12:00:00-0400
description: "A vectorized density over masses, spins and redshift, with hard bounds, from which to draw injections for estimating a detection selection function"
tags: [populations]
notebook: /assets/notebooks/injection-draws.ipynb
gist: https://gist.github.com/maxisi/2a65bb55720d2856b931a3427ae4f0ee
gist_updated: 2023-03-06T19:04:36Z
related_posts: false
---

```python
%matplotlib inline
%config InlineBackend.figure_format = 'retina'
```

```python
import numpy as np
from astropy.cosmology import FlatLambdaCDM
```

```python
default_cosmo = FlatLambdaCDM(H0=67.9, Om0=0.3065)
```

```python
def theta(x, min=-np.inf, max=np.inf):
    """Auxiliary indicator function, which is 1 wherever its argument
    is True and 0 whenever its argument is False.
    """
    out = np.less_equal(min, x) & np.less_equal(x, max)
    return out.astype(int)

def prob(mass1, mass2, spin1x, spin1y, spin1z, spin2x, spin2y, spin2z, z,
         pow_mass1=-2.35, ref_mass1=0., min_mass1=2., max_mass1=100.,
         pow_mass2=1., min_mass2=2., 
         max_spin1=0.998, max_spin2=0.998,
         pow_z=1., max_z=1.9, cosmo=default_cosmo):
    """Implements injection draw distribution from LVK's O3 injection set:
    
    https://zenodo.org/record/5546676#.Y_T0gC-B1pT
    
    The probability density is not normalized. Default values correspond
    to the BBH injection set.
    """
    # masses
    p_mass1 = (mass1 - ref_mass1)**pow_mass1 * theta(mass1, min_mass1, max_mass1)
    p_mass2_given_mass1 = mass2**pow_mass2 * theta(mass2, min_mass2, mass1)
    p_mass1_and_mass2 = p_mass1 * p_mass2_given_mass1
    
    # spins
    p_spin1 = 1./(4*np.pi*(spin1x**2 + spin1y**2 + spin1z**2) * max_spin1) \
              * theta(spin1x**2 + spin1y**2 + spin1z**2, max=max_spin1**2)
    p_spin2 = 1./(4*np.pi*(spin2x**2 + spin2y**2 + spin2z**2) * max_spin2) \
              * theta(spin2x**2 + spin2y**2 + spin2z**2, max=max_spin2**2)
    
    # redshift
    dVc_dz = cosmo.differential_comoving_volume(z).value
    p_z = (dVc_dz) * (1.+z)**(pow_z - 1) * theta(z, max=max_z)
    
    # total
    return p_mass1_and_mass2*p_spin1*p_spin2*p_z
```

```python
# works with floats
prob(30, 30, 0., 0., 0.5, 0., 0., 0.1, 0.1)
```

```text
20163479.218463805
```

```python
# works with arrays
prob(np.array([30, 15.]), np.array([30, 10.]), np.array([0., 0.]), np.array([0., 0.]), np.array([0.5, 0.1]),
     np.array([0., 0.]), np.array([0., 0.]), np.array([0.1, 0.5]), np.array([0.1, 0.2]))
```

```text
array([2.01634792e+07, 1.23752146e+08])
```

```python
# vanishes if any outside bounds
prob(30, 30, 0., 0., 0.5, 0., 0., 0.1, 5)
```

```text
0.0
```

```python
# works with arrays
prob(np.array([30, 15.]), np.array([30, 10.]), np.array([0., 0.]), np.array([0., 0.]), np.array([0.5, 0.1]),
     np.array([0., 0.]), np.array([0., 0.]), np.array([0.1, 0.5]), np.array([0.1, 5]))
```

```text
array([20163479.2184638,        0.       ])
```
