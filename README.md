# ASTControl

ASTControl is a comprehensive control system for an automated solar telescope system at Morehead Planetarium on the campus of UNC-Chapel Hill. This project aims to automate various aspects of solar telescope operation, including initialization, tracking, weather monitoring, and peripheral control. The control system is built using Python and Tkinter for the GUI binded with the indigo_prop_tool command line interface.

## Features

- **Automated Mount Initialization**: Runs a startup script to set up the telescope mount.
- **Sun Tracking**: Automatically tracks the sun using a dedicated tracking script.
- **Weather Monitoring**: Continuously monitors weather conditions to ensure safe operation.
- **FireCapture Integration**: Includes scripts to run and manage FireCapture sessions.
- **Server Control**: Start and stop server operations with ease.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/nkahassai-unc/ASTControl.git
   cd ASTControl
