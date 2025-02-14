# BACnet Device Reader

Source Code for BACnet device reader program, written in Python with the use of BAC0 and Tkinter.

## Installation

Developed with Python 3.12.4. Clone this repository. Install dependencies with:

```bash
pip install -r requirements.txt
```
**Important:** Please see the issues section

## Usage

```bash
python BACnetDeviceReader.py
```
Features lookup of BACnet devices and objects on these devices, and allows the user to save the objects in tags.txt and translate.txt formats.

## Issues
As part of this application, I had to modify the BAC0 library. Modified file is tracked in this repository under 
```bash
venv/Lib/site-packages/BAC0/tasks/TaskManager.py
```
After installing dependencies, replace the auto-installed file with this one.

## Authors
2024 - 2025. Brett Adams, Fedir Solomakha.

CIMCO Refrigeration
