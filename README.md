# AI_german_parliament

## Recommended hardware requirements

- CPU with at least 8 threads
- Graphics card with 8 GB VRAM (absolutely necessary to compute the embeddings)
- 16 GB RAM
- 10 GB available storage space

## Software requirements
- Python 3.13 (or compatible versions, Python 3.14 does not work)
- R 4.6.0 (compatible versions, also tested 4.5.1 and 4.5.2)
- CUDA (version compatibility required depending on GPU drivers), ROCm should also work, but ist not tested

## Operating System

### Linux and Mac
Congratulations, the pipeline should work natively, but it has only been tested on Linux. Go to [Setup](#Setup).

### Windows
If you use Windows, I recommended uninstall your operating system and install a Linux distribution of your choice.

If you do not want or cannot do this, you have two options:

1. Run the pipeline on a high-performance computer at your university or research institute
2. Run it locally using the Windows Subsystem for Linux (WSL), official documentation: https://learn.microsoft.com/en-us/windows/wsl/


Go to [Setup](#Setup).

## Setup

### GPU setup
For GPU support, install PyTorch with CUDA or ROCm following the official instructions:
https://pytorch.org/get-started/locally/

A CUDA-capable NVIDIA GPU or ROCm-compatible AMD GPU with compatible drivers is required for full performance.
Notice that ROCm was not tested.
CPU-only execution is technically possible but prohibitively slow (expect runtimes of over a week depending on your CPU).

### Prepare Python and R

At first open a Terminal in .../Analysis. You can install all R-packages with the following terminal command:

```
Rscript r_packages.r
```

For Python you must use a virtual enviroment (venv). Create a venv called ".venv" (name is important):

```
python3.13 -m venv .venv
``` 

Activate it:
``` 
source .venv/bin/activate
``` 

install the requirements:
```
pip install -r requirements.txt
```

## Start the pipeline

From now on you can start the pipeline through your python enviroment using following command:
``` 
snakemake -s start_ai_research.smk --cores 3
```
Have fun!
