
#  Deep Positional Chess Analyzer

A highly analytical, interactive Streamlit dashboard that goes beyond standard Stockfish Centipawn evaluations. This tool calculates and visualizes advanced strategic metrics including **Space Control, Piece Mobility, King Safety, Tactical Threats**, and the custom **Fireteam Index** (a win-predictor based on sustained positional dominance).

##  Features

- **Move-by-Move Heuristics:** Analyzes every ply using `python-chess` to quantify strategic advantages.
    
- **Time-Series Visualization:** Interactive charts tracking evaluation swings, mobility, and space over the course of the game.
    
- **Critical Moments:** Automatically identifies the biggest evaluation swings and highlights them with rendered SVG board states and alternative move suggestions.
    
- **Fireteam Index:** A unique rolling-average algorithm to predict game outcomes based on sustained positional pressure.
    
- **Flexible Input:** Upload `.pgn` files or paste raw PGN text directly into the UI.
    

---

##  Installation & Usage

There are two ways to run this application: using **Docker** (Recommended for immediate, isolated setup) or a **Local Native Installation**.

### Method A: Docker (Recommended)

This method containerizes the Python environment and the Stockfish binary, meaning you don't have to install any dependencies directly on your host machine.

1. Clone the repository:
    
    Bash
    
    ``` bash
    git clone https://github.com/wdjoyner/chess
    cd chess-analyzer/UI
    ```
    
1. Build and start the container in detached mode:
    ```bash
    docker compose up -d --build
    ```
    
    _(Note: If your system uses the older compose plugin, the command is `docker-compose up -d --build`)_
    
2. Open your browser and navigate to `http://localhost:8501`.
    

_To stop the application, run `docker compose down`._

---

### Method B: Local Native Installation

If you prefer to run the app directly on your host machine, you will need **Python 3.11+** and the **Stockfish** engine binary.

#### 1. Install Stockfish & System Dependencies

**Linux (Fedora-based):**

Bash

```
sudo dnf update
sudo dnf install stockfish python3-pip git
```

_Stockfish will be installed to `/usr/bin/stockfish`._

**Linux (Debian/Ubuntu-based):**

Bash

```
sudo apt update
sudo apt install stockfish python3-pip git
```

_Stockfish will be installed to `/usr/games/stockfish` or `/usr/bin/stockfish`._

**Windows:**

1. Download the latest Stockfish binary from the [official Stockfish website](https://stockfishchess.org/download/).
    
2. Extract the `.zip` file.
    
3. Note the exact path to the `stockfish.exe` file (e.g., `C:\Users\YourName\Downloads\stockfish\stockfish.exe`). You will need to paste this path into the Streamlit UI sidebar.
    
4. Ensure you have [Python](https://www.python.org/downloads/) installed and added to your system PATH.
    

#### 2. Install Python Dependencies

Clone the repo and install the required libraries:

Bash

```
git clone https://github.com/yourusername/chess-analyzer.git
cd chess-analyzer

# Optional but recommended: Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

#### 3. Run the Application

Start the Streamlit server:

Bash

```
streamlit run app.py
```

The dashboard will automatically open in your default web browser at `http://localhost:8501`.

---

##  Configuration

Once the UI is open, use the left sidebar to configure your analysis:

- **Stockfish Path:** If you used Docker or a Linux package manager, the default path should work automatically. If you are on Windows, paste the full path to your `stockfish.exe` file here.
    
- **Analysis Depth:** Adjust the engine depth (default is 16). Higher depths provide more accurate centipawn loss and alternative move calculations but will take longer to process the full PGN.
    
