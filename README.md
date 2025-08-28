# SWalkers-TEW-IX-Pal Rework

A graphical tool for editing and managing TEW IX save files (MDB/ACCDB), including tournament, dojo, and alliance management. Designed for use with the Microsoft Access Database Engine and compatible with both Python and standalone EXE.

## IMPORTANT
**Always back up your save file beforehand and don't try to rely on the internal backup functionality in this application. This tool is still in development and may not function properly. So use it on your own risk. On the plus side, I've done some Watcher simulations after using this tool. So that is a plus!**

## Installation & Usage

### 1. Install Microsoft Access Database Engine (MDB Driver)
This application requires the Microsoft Access Database Engine 2016 Redistributable to access MDB/ACCDB files.
- Download from: https://www.microsoft.com/en-us/download/details.aspx?id=54920
- Install the driver before running the application (required for both Python and EXE usage).

### 2. Download the EXE
You can download the standalone executable from the [GitHub Releases](https://github.com/SWalkerDDT/SWalkers-TEW-IX-Pal/releases) page.
- **Note:** The Microsoft Access Database Engine driver must still be installed on your system for the EXE to work.

### 3. Python Setup

#### a. Create a virtual environment
```
python -m venv venv
```

#### b. Activate the virtual environment
```
venv\Scripts\activate
```

#### c. Install requirements
```
pip install -r requirements.txt
```

#### d. Run the application
```
python app.py
```

## Future Features
- TBD

## Contact:
- Mail: swalkerddt@gmail.com
- X: @swalkerDDT
- Bluesky: @swalkerddt.bsky.social
---
