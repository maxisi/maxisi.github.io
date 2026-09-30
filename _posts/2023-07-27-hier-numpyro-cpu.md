---
layout: post
title: "Fitting a hierarchical Gaussian model with NumPyro on CPUs"
date: 2023-07-27 12:00:00-0400
description: "Infer the mean and width of a Gaussian population from per-event posterior samples with NumPyro, using a KDE to smooth the samples and parallel chains across CPU cores"
tags: [hierarchical-inference]
notebook: /assets/notebooks/hier-numpyro-cpu.ipynb
gist: https://gist.github.com/maxisi/2ce82fae45da4f12721d6b981e742732
gist_updated: 2023-07-27T15:31:47Z
related_posts: false
---

Here I demonstrate how to fit a Gaussian hierarchically using _numpyro_ and CPUs. We use a KDE to smoothen over samples.

```python
%matplotlib inline
```

```python
import numpy as np
import arviz as az
import jax
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
numpyro.set_host_device_count(8)
```

```python
jax.local_device_count()
```

```text
No GPU/TPU found, falling back to CPU. (Set TF_CPP_MIN_LOG_LEVEL=0 and rerun for more info.)
```

```text
8
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

```python
result = az.from_numpyro(mcmc)
```

```python
az.plot_trace(result, var_names=['mu', 'sigma']);
```

{% include figure.html path="assets/img/notes/hier-numpyro-cpu/output_01.png" class="img-fluid rounded z-depth-1" zoomable=true %}
