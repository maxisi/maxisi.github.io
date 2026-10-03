---
title: Black-hole ringdowns
slug: ringdown
order: 1
img: assets/img/research/ringdown.png
img_credit: M. Isi / NASA
summary: Listening to the final ring of newborn black holes to test general relativity and the Kerr nature of black holes.
keywords: ringdown
software: [maxisi/ringdown]
---

When two black holes merge, the remnant is born highly distorted and settles down by
emitting gravitational waves at a discrete set of frequencies and damping times: its
_quasinormal modes_. General relativity predicts that, for a Kerr black hole, the whole
spectrum is fixed by just the mass and spin. Measuring two or more modes in the same
signal therefore turns each merger into a laboratory for the _no-hair theorem_ and for
the nature of black holes, an idea known as black-hole spectroscopy.

Our group has been at the forefront of turning this idea into a reality. Starting with GW150914, we have shown that _overtones_ bring black-hole spectroscopy within reach of LIGO and Virgo. 
This was most strikingly demonstrated with GW250114, a record-loud signal whose ringdown furnished the best tests yet of the Kerr nature of black holes and of Hawking's black-hole area law.
Our group's work made these results possible by developing a self-consistent framework for analyzing ringdowns directly in the time domain and producing widely-used software to do so.
We have also quantified the systematics that may arise from detector noise and data conditioning, and applied
these tools to the most massive events observed by LIGO and Virgo, including GW190521
and GW231123, where hints of multiple modes and precessional signatures appear.

Ongoing work connects the observations to numerical relativity, including nonlinear
and precessing ringdowns, the polarization content of the ringdown signal, and
forecasts for what next-generation detectors and LISA will be able to say about the
black holes they observe. These analyses are carried out with our open-source
[`ringdown`](https://github.com/maxisi/ringdown) package.
