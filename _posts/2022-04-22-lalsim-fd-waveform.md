---
layout: post
title: "Frequency-domain waveforms with LALSimulation"
date: 2022-04-22 12:00:00-0400
description: "Generate an IMRPhenomD waveform with ChooseFDWaveform, plot its amplitude and phase, and inverse-Fourier transform it to the time domain"
tags: [waveforms]
notebook: /assets/notebooks/lalsim-fd-waveform.ipynb
gist: https://gist.github.com/maxisi/f768d30911756bc7c805b5097e3c7019
gist_updated: 2022-04-22T19:01:43Z
related_posts: false
---

```python
%pylab inline
%config InlineBackend.figure_format = 'retina'
```

```text
Populating the interactive namespace from numpy and matplotlib
```

```python
import lalsimulation as lalsim
import lal

import seaborn as sns
sns.set_theme(palette='colorblind', font_scale=1.2)
```

```python
approximant = lalsim.SimInspiralGetApproximantFromString("IMRPhenomD")

# frequency array parameters
df = 0.25
f_min = 20
f_max = 1024
f_ref = f_min

# source parameters
m1_msun = 30
m2_msun = 30
chi1 = [0, 0, 0.5]
chi2 = [0, 0, 0.5]
dist_mpc = 440
inclination = 0
phi_ref = 0

m1_kg = m1_msun*lal.MSUN_SI
m2_kg = m2_msun*lal.MSUN_SI
distance = dist_mpc*1e6*lal.PC_SI

hp, hc = lalsim.SimInspiralChooseFDWaveform(m1_kg, m2_kg,
                                            chi1[0], chi1[1], chi1[2],
                                            chi2[0], chi2[1], chi2[2],
                                            distance, inclination,
                                            phi_ref, 0, 0., 0.,
                                            df, f_min, f_max, f_ref,
                                            None, approximant)
```

Plot the Fourier amplitude:

```python
freq = arange(len(hp.data.data))*df
loglog(freq, abs(hp.data.data), label="+")
loglog(freq, abs(hc.data.data), ls='--', label="x")
legend()
xlabel("frequency (Hz)")
ylabel(r"$|\tilde{h}|$");
```

{% include figure.html path="assets/img/notes/lalsim-fd-waveform/output_01.png" class="img-fluid rounded z-depth-1" zoomable=true %}

Plot the Fourier phase:

```python
freq = arange(len(hp.data.data))*df
plot(freq, unwrap(angle(hp.data.data)), label="+")
plot(freq, unwrap(angle(hc.data.data)), ls='--', label="x")
legend()
xlabel("frequency (Hz)")
ylabel(r"$\angle \tilde{h}$");
```

{% include figure.html path="assets/img/notes/lalsim-fd-waveform/output_02.png" class="img-fluid rounded z-depth-1" zoomable=true %}

You can easily inverse-Fourier transform the waveform:

```python
hp_td = np.fft.irfft(hp.data.data)
```

```python
plot(hp_td)
xlabel("index")
ylabel(r"$h_+$");
```

{% include figure.html path="assets/img/notes/lalsim-fd-waveform/output_03.png" class="img-fluid rounded z-depth-1" zoomable=true %}

Note that the "peak" (or whatever `IMRPhenomD` takes to be the reference time) of this waveform was placed at the beggining of the segment.
