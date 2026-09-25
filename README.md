# duckieSim

A simulation environment for **Duckietown**, built for developing and testing autonomous driving algorithms on simulated duckiebots with feedback.

## Overview

This project wraps and extends a [gym-duckietown](https://github.com/duckietown/gym-duckietown) based simulator to train and evaluate driving policies for duckiebots. A modified/forked version of the simulator lives in `ext_libs/` so it can be customized directly rather than treated as a fixed dependency.

## Project Structure

```
duckieSim/
├── src/            # Main application code (entry point: duckieSim.py)
│   ├── utils/      # Generic helper functions used across the project
│   ├── models/     # Saved AI models (trained policies, guidance agents)
│   └── config/     # Simulation settings and map parameters
├── ext_libs/       # Forked/modified external libraries (e.g. gym-duckietown)
├── maps/           # Map files used by the simulator
├── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3.x
- Core dependencies (see `requirements.txt`):
  - `gym==0.17.2`
  - `numpy==1.23.5`
  - `pyglet==1.5.0` (windowing/rendering, used by gym-duckietown)
- Optional, currently commented out in `requirements.txt` — uncomment as needed:
  - `matplotlib`, `scipy`, `pandas` (analysis/visualization)
  - `opencv-python` (computer vision)
  - `pytest` (testing)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/asrparker/duckieSim.git
   cd duckieSim
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up the simulator fork in `ext_libs/` (see that directory for any additional install steps specific to the modified gym-duckietown).

## Usage

Run the simulation:
```
python src/duckieSim.py
```

## Project Status

This is a personal/research project. It's not currently open to outside contributions — issues and pull requests are disabled. Feel free to fork it for your own experiments.

## License

No license is currently specified, which means default copyright applies: all rights reserved, and others don't have permission to reuse or redistribute this code. Add a `LICENSE` file if you ever want to grant specific permissions.
