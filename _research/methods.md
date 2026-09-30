---
title: Machine learning and statistical methods
slug: methods
order: 3
img: assets/img/research/methods.png
summary: Fast, flexible inference tools&#58; differentiable waveforms, normalizing flows, and likelihoods that learn what real detector noise looks like.
keywords: methods
software: [kazewong/jim, simonajmiller/tdinf]
---

Extracting physics from gravitational-wave data is a problem in statistical inference,
and the growing catalog demands tools that are both faster and more honest about the
data than the standard approach. We develop such tools, drawing on modern machine
learning and hardware-accelerated computing, and we release them as open-source
software.

With collaborators we built [`jim`](https://github.com/kazewong/jim), a
parameter-estimation code that combines differentiable waveforms
(`ripple`), normalizing flows, and GPU
sampling to analyze a signal in minutes rather than days, without simplifying
assumptions. We have used score-based generative models to characterize
non-Gaussian detector noise directly from data and machine learning to remove
nonstationary noise from the detectors, and we develop time-domain inference
techniques that avoid the pitfalls of the usual frequency-domain likelihood.

The same emphasis on methodology runs through the rest of our research: hierarchical
models for populations and for tests of general relativity, signal-coherence
statistics for detection confidence, and careful treatments of noise estimation and
data conditioning for ringdown analyses. Worked examples of many of these techniques
are collected in our [notes](/notes/).
