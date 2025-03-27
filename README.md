# BACnet Device Reader

Source Code for BACnet device reader program. Written in Python with the use of BAC0 and Tkinter.

## Usage

Download latest version of the BACnet Device Reader from "Releases" section. Run the executable.

Features lookup of BACnet devices and objects on these devices, and allows the user to save the objects in `tags.txt`, `translate.txt` and `.csv` formats.

## Contributing
Developed with Python 3.12.4. Clone this repository. Install dependencies with:

```bash
pip install -r requirements.txt
```
**Important:** Please see the "Issues" section

Main logic for the reader is in `BACnetDeviceReader.py`. After making modifications, test the new version by running it in command line with:
```bash
python BACnetDeviceReader.py
```
After new version has been tested, compile into an executible by running compile script with:
```bash
.\compile.ps1
```
You need to have pyinstaller installed for this. It should be installed together with other requirements from `requirements.txt`.

## Issues
As part of this application, I had to modify the BAC0 library. Modified file is tracked in this repository under `venv/Lib/site-packages/BAC0/tasks/TaskManager.py`. After installing dependencies, replace the auto-installed file with this one.

This path assumes that python virtual environment is used under `.\venv`. If installing globally, replace file in appropriate package directory in Python's global `Lib` folder.



## Authors
2024 - 2025. Brett Adams, Fedir Solomakha.

CIMCO Refrigeration
