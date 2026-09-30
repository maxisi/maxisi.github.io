---
layout: post
title: "Simulating detector noise from a power spectral density"
date: 2023-02-03 12:00:00-0400
description: "Draw Gaussian noise for LIGO and Virgo from their design PSDs in the frequency domain, transform to the time domain and check the result with a Welch estimate"
tags: [noise]
notebook: /assets/notebooks/simulate-gw-noise.ipynb
gist: https://gist.github.com/maxisi/7d63b4878a48e5e1c5e0307159bb3e09
gist_updated: 2024-03-04T14:06:28Z
related_posts: false
---

Simulate time-domain strain noise from a given power specral density (PSD). **NOTE:** There might be cleverer ways of doing this, but I this is the most transparent to me.

```python
%pylab inline
%config InlineBackend.figure_format = 'retina'
```

```text
Populating the interactive namespace from numpy and matplotlib
```

```python
import seaborn as sns
import scipy.signal as ssig
import lalsimulation as lalsim

sns.set(context='notebook', palette='colorblind')
```

We will simulate detector data containing noise for a number of detectors. To do this, we will take advantage of the reference PSDs shipped with _LALSimulation_. The choices below correspond to the design sensitivies of advanced LIGO Hanford (`H1`), LIGO Livingston (`L1`) and Virgo (`V1`). Since these are projected sensitivies, these are the same for H and L, but in a real analysis that would not be the case (because, although the detectors have the same design, in real life they are independent).

Of course, the _LALSimulation_ functions could be replaced with whatever PSD you want.

```python
psd_func_dict = {
    'H1': lalsim.SimNoisePSDaLIGOZeroDetHighPower,
    'L1': lalsim.SimNoisePSDaLIGOZeroDetHighPower,
    'V1': lalsim.SimNoisePSDAdvVirgo,
}
ifos = list(psd_func_dict.keys())
```

We can visualize these spectra:

```python
fs = np.linspace(10, 2E3, 4096)
for ifo, psd in psd_func_dict.items():
    loglog(fs, np.vectorize(psd)(fs), label=ifo, alpha=0.6, lw=2)
xlabel('f (Hz)')
ylabel('PSD (1/Hz)')
legend();
```

{% include figure.html path="assets/img/notes/simulate-gw-noise/output_01.png" class="img-fluid rounded z-depth-1" zoomable=true %}

## Frequency-domain noise

Next, construct a list of time-stamps for each detector; for simplicity, we can take this to be the same for all IFOs (this is usually be the case in real life). We will construct the time-stamps based on a reference GPS time, which here we choose based on the first LIGO detection (GW150914). 

Constructing the time array here will defined important quantities like `delta_t`. (If you are staying in the Fourier domain, that's basically all you need.)

```python
# define center of time array
tgps_geo = 1126259462.423

# define sampling rate and duration
fsamp = 8192
duration = 2

delta_t = 1/fsamp
tlen = int(round(duration / delta_t))

epoch = tgps_geo - 0.5*tlen*delta_t

time_dict = {i: np.arange(tlen)*delta_t + epoch for i in ifos}
```

Now we want to instantiate the PSDs, to get an array of values instead of a function. To do this, we need an array of frequencies corresponding to the time series data we constructed above. **NOTE:** all this does is evaluate the PSDs at the desired frequencies---you could skip straight to this part if you had an array in the first place.

```python
freqs = fft.rfftfreq(tlen, delta_t)
delta_f = freqs[1] - freqs[0]

# we will want to pad low frequencies; the function below applies a
# prescription to do so smoothly, but this is not really needed: you
# could just set all values below `fmin` to a constant.
fmin = 10
def pad_low_freqs(f, psd_ref):
    return psd_ref + psd_ref*(fmin-f)*np.exp(-(fmin-f))/3

psd_dict = {}
for ifo in ifos:
    psd = np.zeros(len(freqs))
    for i,f in enumerate(freqs):
        if f >= fmin:
            psd[i] = psd_func_dict[ifo](f)
        else:
            psd[i] = pad_low_freqs(f, psd_func_dict[ifo](fmin))
    psd_dict[ifo] = psd
```

#### Adding noise to data

If we are not doing a no-noise simulation, then we should add noise to the data; this should match the PSD above. To do this, first simulate noise with the right variance, $$S(f)/(4 \Delta f)$$, in the Fourier domain and then IFFT back into the time domain. Recall that, since we assume the noise is stationary, the covariance of the noise is diagonal in the Fourier domain.

```python
rng = np.random.default_rng(12345)

noise_fd_dict = {}
for ifo, psd in psd_dict.items():
    var = psd / (4.*delta_f)  # this is the variance of LIGO noise given the definition of the likelihood function
    noise_real = rng.normal(size=len(psd), loc=0, scale=np.sqrt(var))
    noise_imag = rng.normal(size=len(psd), loc=0, scale=np.sqrt(var))
    noise_fd_dict[ifo] = noise_real + 1j*noise_imag
```

```python
# IFFT into the time domain
noise_td_dict = {}
for ifo, noise_fd in noise_fd_dict.items():
    noise_td_dict[ifo] = fft.irfft(noise_fd) / delta_t
```

As a sanity check, let's manually compute the PSD from the simulated data using Welch and compare to the one we prescribed.

```python
fig, axs = subplots(1, len(ifos), figsize=(5*len(ifos), 3))
for ax, (ifo, noise) in zip(axs, noise_td_dict.items()):
    # compute Welch PSD
    psd_freq, psd_data = ssig.welch(noise, fs=1./delta_t, nperseg=0.1*duration/delta_t)
    
    ax.loglog(freqs, psd_dict[ifo], label='Original', c='crimson', lw=2, zorder=100)
    ax.loglog(psd_freq, psd_data, label='Welch')
    ax.legend(loc='upper right', frameon=False, title=ifo);
    ax.set_xlabel("Frequency (Hz)");
    # ax.set_ylim(1E-47, 1E-46)
axs[0].set_ylabel(r"PSD ($1/\mathrm{Hz}$)");
```

{% include figure.html path="assets/img/notes/simulate-gw-noise/output_02.png" class="img-fluid rounded z-depth-1" zoomable=true %}

We are done! now you can take the time (or frequency) series above and add a signal to it.
