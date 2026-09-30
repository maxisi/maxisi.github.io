---
layout: post
title: "Reading LVK parameter-estimation samples with h5py"
date: 2022-06-29 12:00:00-0400
description: "Download a GWTC-3 posterior release from Zenodo and read the samples directly with h5py, without PESummary"
tags: [data-access, parameter-estimation]
notebook: /assets/notebooks/loading-pe-samples.ipynb
gist: https://gist.github.com/maxisi/d033b94be8af4b7d3b0e167f7574224f
gist_updated: 2022-06-29T03:20:18Z
related_posts: false
---

Let's download some samples from Zenodo. https://zenodo.org/record/5546663#.YrvAoy1h2Zw

```python
!wget https://zenodo.org/record/5546663/files/IGWN-GWTC3p0-v1-GW191109_010717_PEDataRelease_mixed_nocosmo.h5
```

```text
--2022-06-28 23:05:16--  https://zenodo.org/record/5546663/files/IGWN-GWTC3p0-v1-GW191109_010717_PEDataRelease_mixed_nocosmo.h5
Resolving zenodo.org (zenodo.org)... 137.138.76.77
Connecting to zenodo.org (zenodo.org)|137.138.76.77|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 374495928 (357M) [application/octet-stream]
Saving to: ‘IGWN-GWTC3p0-v1-GW191109_010717_PEDataRelease_mixed_nocosmo.h5’

IGWN-GWTC3p0-v1-GW1 100%[===================>] 357.15M  18.7MB/s    in 20s     

2022-06-28 23:05:38 (18.1 MB/s) - ‘IGWN-GWTC3p0-v1-GW191109_010717_PEDataRelease_mixed_nocosmo.h5’ saved [374495928/374495928]
```

We could read this file with PESummary, but we can also just read it directly with `h5py`.

```python
import h5py
```

```python
path = "IGWN-GWTC3p0-v1-GW191109_010717_PEDataRelease_mixed_nocosmo.h5"
f = h5py.File(path, 'r')
```

Let's look at the contents of the file. There should be several versions of parameter estimation with different waveforms (and `Mixed` which mixes them together---we won't use that).

```python
f.keys()
```

```text
<KeysViewHDF5 ['C01:IMRPhenomXPHM', 'C01:Mixed', 'C01:SEOBNRv4PHM', 'history', 'version']>
```

Let's look at the IMRPhenomXPHM posterior.

```python
f["C01:IMRPhenomXPHM"].keys()
```

```text
<KeysViewHDF5 ['approximant', 'calibration_envelope', 'config_file', 'description', 'injection_data', 'meta_data', 'posterior_samples', 'priors', 'psds', 'skymap', 'version']>
```

There's a lot of useful data there. Let's grab the posteiror samples.

```python
samples = f["C01:IMRPhenomXPHM"]["posterior_samples"][()]
```

The object `samples` is now a `numpy` array of sample values. Look at the first one:

```python
samples[0]
```

```text
(49.83796952, 0.47550625, 0.76094274, 0.97779026, 2.68089553, 2.33125286, 1.43867327, 5.4794171, 1.86400836, 2.88303856, 0.95087449, 3.16668241, 1.23991265, -0.0345347, -0.03027852, 0.02633217, 0.00612017, 0.02118842, 0.00483064, -0.02262716, 0.01399977, -0.00912521, 0.0077975, 0.00762875, 0.00898645, 0.01673635, 0.00153966, -0.00325621, 0.00043218, -0.00900994, 0.02093193, -0.00096529, 0.00584457, 0.03638164, -0.0142964, 0.06758084, 0.02025775, -0.00939106, 0.00021786, -0.02526524, 0.00014082, -0.00751683, 0.02485568, 0.0213544, 0.00276958, -0.10831524, 0.00395862, -0.03166127, -0.00679669, 0.00657231, -0.00048339, 0.01633011, 0.00641051, -0.00043257, 841.1004016, 1.25729686e+09, 20., 28.25254356, 39.91031089, 56.37838986, 79.64164577, 112.50395334, 158.92614214, 224.50338771, 317.13958708, 448., 20., 28.25254356, 39.91031089, 56.37838986, 79.64164577, 112.50395334, 158.92614214, 224.50338771, 317.13958708, 448., 139.33682696, 91.65241743, 124.16404871, 84.15013375, 40.01391496, 4.06338557, -0.685645, 0.21841081, 2.16288408, 0.14362758, 0.306291, -0.68160898, -0.59619716, 0.38265128, -0.67394417, 1.13231609, 2.57098936, -0.67913887, 0.33829434, 0.70842999, 0.33829434, -0.89574279, -0.68925228, 719.28615156, 10.15287976, 9.89555481, 14.20906255, 14.16518131, 10.15383651, -0.0137278, 14.32316601, -0.12630881, 0.16966857, 2.10302176, 71.94357114, 34.20961808, 106.15318921, 42.60862515, 0.33866277, 0.44604944, 4.08469549, 0.38196144, 2.03258767, 120.83156706, 103.30410722, 2.84908199, 1.25729686e+09, 1.25729686e+09, 17.27930457, 17.46264291, -0.28902865, 1.2775843, -0.55809461, 2.6521878, 2.36134765, -0.6716178, -0.69495583, -0.67913887, 0.35771971, -0.88261279, -0.71074121)
```

We can see the meaning of the samples by getting their names:

```python
samples.dtype.names
```

```text
('chirp_mass',
 'mass_ratio',
 'a_1',
 'a_2',
 'tilt_1',
 'tilt_2',
 'phi_12',
 'phi_jl',
 'theta_jn',
 'psi',
 'phase',
 'azimuth',
 'zenith',
 'recalib_H1_amplitude_0',
 'recalib_H1_amplitude_1',
 'recalib_H1_amplitude_2',
 'recalib_H1_amplitude_3',
 'recalib_H1_amplitude_4',
 'recalib_H1_amplitude_5',
 'recalib_H1_amplitude_6',
 'recalib_H1_amplitude_7',
 'recalib_H1_amplitude_8',
 'recalib_H1_amplitude_9',
 'recalib_H1_phase_0',
 'recalib_H1_phase_1',
 'recalib_H1_phase_2',
 'recalib_H1_phase_3',
 'recalib_H1_phase_4',
 'recalib_H1_phase_5',
 'recalib_H1_phase_6',
 'recalib_H1_phase_7',
 'recalib_H1_phase_8',
 'recalib_H1_phase_9',
 'recalib_L1_amplitude_0',
 'recalib_L1_amplitude_1',
 'recalib_L1_amplitude_2',
 'recalib_L1_amplitude_3',
 'recalib_L1_amplitude_4',
 'recalib_L1_amplitude_5',
 'recalib_L1_amplitude_6',
... (87 lines omitted) ...
 'viewing_angle',
 'cos_iota',
 'tilt_1_infinity_only_prec_avg',
 'tilt_2_infinity_only_prec_avg',
 'spin_1z_infinity_only_prec_avg',
 'spin_2z_infinity_only_prec_avg',
 'chi_eff_infinity_only_prec_avg',
 'chi_p_infinity_only_prec_avg',
 'cos_tilt_1_infinity_only_prec_avg',
 'cos_tilt_2_infinity_only_prec_avg')
```

So you can histogram the mass of the heaviest black hole (`mass_1`) by doing:

```python
import seaborn as sns
g = sns.histplot(samples['mass_1'], kde=True)
g.axes.set_xlabel(r'$m_1/m_\odot$');
```

{% include figure.html path="assets/img/notes/loading-pe-samples/output_01.png" class="img-fluid rounded z-depth-1" zoomable=true %}

You should remember to close the file when you are done.

```python
f.close()
```

Actually, the best practice to do the data with a `with` statement.

```python
with h5py.File(path, 'r') as f:
    samples = f["C01:IMRPhenomXPHM"]["posterior_samples"][()]
```

And now there's no need to explicitly close the file.
