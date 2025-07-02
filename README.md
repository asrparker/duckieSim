# Duckietown Simulation

This project is a simulation environment for Duckietown, designed to facilitate the development and testing of autonomous driving algorithms.

## Project Structure

```
sim
├── src
│   ├── duckieSim.py          # Main entry point for the Duckietown simulation
│   ├── utils
│   │   └── __init__.py       # Utility functions and classes
│   ├── models
│   │   └── __init__.py       # Data models for the simulation
│   └── config
│       └── settings.py       # Configuration settings for the simulation
├── requirements.txt           # Python dependencies for the project
├── .gitignore                 # Files and directories to ignore by Git
└── README.md                  # Documentation for the project
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd sim
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To start the simulation, run the following command:
```
python src/duckieSim.py
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.