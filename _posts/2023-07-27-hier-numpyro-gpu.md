---
layout: post
title: "Fitting a hierarchical Gaussian model with NumPyro on a GPU"
date: 2023-07-27 12:00:00-0400
description: "The same KDE-smoothed hierarchical Gaussian fit as the CPU version, run with NUTS on a single CUDA device"
tags: [hierarchical-inference, gpu]
notebook: /assets/notebooks/hier-numpyro-gpu.ipynb
gist: https://gist.github.com/maxisi/db17a3d8d8ae7772a8b298a3b9b1aed3
gist_updated: 2023-07-27T15:33:53Z
related_posts: false
---

Here I demonstrate how to fit a Gaussian hierarchically using _numpyro_ on a GPU. We use a KDE to smoothen over samples.

```python
%matplotlib inline
```

```python
import numpy as np
import arviz as az
import jax
import jax.numpy as jnp
```

```python
jax.local_device_count()
```

```text
1
```

```python
import numpy as np
import arviz as az
import jax
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
```

```python
numpyro.set_platform("gpu")
numpyro.set_host_device_count(1)
```

```python
def make_model(x_samples_stack, manual=False):
    Nobs = x_samples_stack.shape[0]
    Nsamp = x_samples_stack.shape[1]

    # hyper prior
    mu = numpyro.sample('mu', dist.Uniform(-1, 1))
    sigma = numpyro.sample('sigma', dist.Uniform(0, 1))

    # compute KDE bandwidths using Scott's rule
    bws = np.std(x_samples_stack, axis=1)/Nsamp**(1.0/5.0)

    sigma_tot = jnp.sqrt(jnp.square(sigma) + bws**2)

    def log_density(xs, m, s):
        return dist.Normal(m, s).log_prob(xs)

    logps = log_density(x_samples_stack.T, mu, sigma_tot)
    evt_log_mean_wts = jax.nn.logsumexp(logps, axis=0) - np.log(Nsamp)
    numpyro.factor('log_likelihood', jnp.sum(evt_log_mean_wts))
```

```python
# test model: simulate some events

mu_true = 0.
sigma_true = 0.

Nobs = 100
Nsamp = 1000

sigma_obs = 0.1

fake_truths = np.random.normal(mu_true, sigma_true, Nobs)
fake_obs = np.random.normal(0, sigma_obs, (Nobs, Nsamp)) + fake_truths[:,np.newaxis]
```

```python
nmcmc = 1000
nchain = 4

kernel = NUTS(make_model)
mcmc = MCMC(kernel, num_warmup=nmcmc, num_samples=nmcmc, num_chains=nchain)
mcmc.run(jax.random.PRNGKey(1234), fake_obs)
```

```text
/tmp/ipykernel_645051/3316457081.py:5: UserWarning: There are not enough devices to run parallel chains: expected 4 but got 1. Chains will be drawn sequentially. If you are running MCMC in CPU, consider using `numpyro.set_host_device_count(4)` at the beginning of your program. You can double-check how many devices are available in your system using `jax.local_device_count()`.
  mcmc = MCMC(kernel, num_warmup=nmcmc, num_samples=nmcmc, num_chains=nchain)
sample: 100%|█| 2000/2000 [00:07<00:00, 252.01it/s, 1 steps of size 6.60e-01. ac
sample: 100%|█| 2000/2000 [00:06<00:00, 324.39it/s, 3 steps of size 7.97e-01. ac
sample: 100%|█| 2000/2000 [00:06<00:00, 290.49it/s, 7 steps of size 5.08e-01. ac
sample: 100%|█| 2000/2000 [00:06<00:00, 300.65it/s, 3 steps of size 6.54e-01. ac
```

```python
result = az.from_numpyro(mcmc)
```

```python
az.plot_trace(result, var_names=['mu', 'sigma']);
```

```text
/mnt/sw/nix/store/fyb44x0iw8gg9dc8bx70ykh1pbrzfgfv-python-3.10.8-view/lib/python3.10/site-packages/arviz/plots/backends/matplotlib/distplot.py:36: UserWarning: Argument backend_kwargs has not effect in matplotlib.plot_distSupplied value won't be used
  warnings.warn(
/mnt/sw/nix/store/fyb44x0iw8gg9dc8bx70ykh1pbrzfgfv-python-3.10.8-view/lib/python3.10/site-packages/arviz/plots/backends/matplotlib/distplot.py:36: UserWarning: Argument backend_kwargs has not effect in matplotlib.plot_distSupplied value won't be used
  warnings.warn(
/mnt/sw/nix/store/fyb44x0iw8gg9dc8bx70ykh1pbrzfgfv-python-3.10.8-view/lib/python3.10/site-packages/arviz/plots/backends/matplotlib/distplot.py:36: UserWarning: Argument backend_kwargs has not effect in matplotlib.plot_distSupplied value won't be used
  warnings.warn(
```

{% include figure.html path="assets/img/notes/hier-numpyro-gpu/output_01.png" class="img-fluid rounded z-depth-1" zoomable=true %}
