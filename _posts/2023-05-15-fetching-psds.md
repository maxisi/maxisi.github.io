---
layout: post
title: "Retrieving the noise spectra used in LVK parameter estimation"
date: 2023-05-15 12:00:00-0400
description: "Locate the latest parameter-estimation release for an event in the GWOSC catalog and pull the per-detector PSDs out of the data file"
tags: [data-access, noise, parameter-estimation]
notebook: /assets/notebooks/fetching-psds.ipynb
gist: https://gist.github.com/maxisi/e3847dfe3d81d2c306f6efa518f0e732
gist_updated: 2023-05-15T18:03:56Z
related_posts: false
---

This notebook demonstrates how to obtain the PSD used in a given PE run.

```python
%matplotlib inline
%config InlineBackend.figure_format = 'retina'
```

```python
import requests
import os 
from tqdm import tqdm
import json
import wget
from matplotlib import pyplot as plt
import h5py
```

Define the name of the event whose PSD we want, as well as the GWOSC catalog URL.

```python
event = "GW190521_074359"
gwosc_url = "https://www.gw-openscience.org/eventapi/jsonfull/GWTC"
```

Obtain a set of metadata for all events in the GWOSC catalog, and locate our event.

```python
catalog = requests.get(gwosc_url).json()
```

```python
event_keys = [k for k in catalog['events'].keys() if event in k]
if len(event_keys) == 0:
    print(f"ERROR: {event} not found in catalog.")
elif len(event_keys) > 1:
    print(f"WARNING: multiple entries matching '{event}': {event_keys}")
else:
    event_key = event_keys[0]
    event_info = catalog['events'][event_key]

    # pull additional information for this event
    event_info_extra = requests.get(event_info['jsonurl']).json()['events'][event_key]
```

```python
# locate most recent PE file info
param_dict = event_info_extra['parameters']
pe_dates = []
for k_pe, v_pe in param_dict.items():
    # ignore parameters from pipelines
    if '_pe_' in k_pe:
        date = v_pe['date_added']
        pe_dates.append((date, k_pe))
if not pe_dates:
    print(f"ERROR: did not find PE for {k}")
    
chosen_pe_key = sorted(pe_dates)[-1][1]
if not param_dict[chosen_pe_key]['is_preferred']:
    print(f"WARNING: did not pick preferred PE for {k}")
    pref_key = [k for k, v in param_dict.items()
                if '_pe_' in k and v['is_preferred']][0]
    print(f"INFO: Chose {chosen_pe_key} over {pref_key}")
```

```python
# we can now get the URL of the PE samples from the chosen PE run
data_url = param_dict[chosen_pe_key]['data_url']
fname = os.path.basename(data_url)
outpath = fname
if not os.path.exists(outpath):
    print(f"INFO: Downloading {event}")
    # response = requests.get(data_url, stream=True)
    # with open(outpath, "wb") as handle:
    #     for data in tqdm(response.iter_content()):
    #         handle.write(data)
    wget.download(data_url, outpath)
elif os.path.exists(outpath):
    print(f"INFO: Skipping preexisting file: {outpath}")
```

```text
INFO: Skipping preexisting file: IGWN-GWTC2p1-v2-GW190521_074359_PEDataRelease_mixed_cosmo.h5
```

Load file and extract PSDs:

```python
with h5py.File(outpath) as f:
    # get approximant name first
    approx = sorted([k for k in f.keys()
                     if 'phenom' in k.lower() or "seob" in k.lower()])[0]
    print(f"Selecting approximant: {approx}")
    psds_df =  f[approx]['psds']
    psds = {ifo: psds_df[ifo][()] for ifo in psds_df.keys()}
    
```

```text
Selecting approximant: C01:IMRPhenomXPHM
```

```python
psds
```

```text
{'H1': array([[0.00000e+00, 5.00000e-01],
        [2.50000e-01, 5.00000e-01],
        [5.00000e-01, 5.00000e-01],
        ...,
        [5.11250e+02, 2.39617e-43],
        [5.11500e+02, 4.50207e-43],
        [5.11750e+02, 4.63891e-42]]),
 'L1': array([[0.00000e+00, 5.00000e-01],
        [2.50000e-01, 5.00000e-01],
        [5.00000e-01, 5.00000e-01],
        ...,
        [5.11250e+02, 2.74168e-46],
        [5.11500e+02, 2.96262e-46],
        [5.11750e+02, 1.88789e-43]])}
```
