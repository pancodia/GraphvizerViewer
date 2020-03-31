# Graphvizer Viewer

An image viewer for Graphvizer

# Introduction

[Graphvizer](https://github.com/hao-lee/Graphvizer) is a plugin for Sublime Text 3 to render image in real-time while you are writing. If you have tried it, you may find that its convenience is limited because Sublime Text is not a suitable image viewer as mentioned in [issue #14](https://github.com/hao-lee/Graphvizer/issues/14).

Sublime Text can view image but it doesn't support zoom or pan the image. If the image is large, it will be very difficult to navigate it. That's why I write this viewer. GraphvizerViewer is an awesome supplement of Graphvizer. I bet you will like it.

![](gif/graphvizerviewer.gif)

# Features

* Zoom in/out
* Reset zoom
* Pan (Drag)
* Refresh automatically when the image is modified
* Multiple Tabs

> For other features, please open an issue.

# Shortcoming

The program is written using PySide2, so the executable file size is a bit large.

# Installation

## Method 1: Download the standalone executable file

[Download from releases](https://github.com/hao-lee/GraphvizerViewer/releases)

## Method 2: Install dependencies manually

### Windows

```
# After install Python 3.x
pip install PySide2
python GraphvizerViewer.py
```

### Linux/OSX

```
dnf install python3 libxkbcommon-x11 # apt-get, yum ...
pip3 install PySide2
python3 GraphvizerViewer.py
```

### MacOS and Anaconda Python

If you installed Python 3 via Anaconda distribution, then you need to install PySide2 in the conda way. Otherwise, I had similar issue describe in this [SO thread](https://stackoverflow.com/questions/51912816/pyside2-qt-creator-run-issue-could-not-load-the-qt-platform-plugin-cocoa-in/60955108#60955108)

```
conda install -c conda-forge pyside2
python3 GraphvizerViewer.py
```

# Usage

#### Open an image

Just drag the image into the program window.

#### Zoom

Use mouse wheel to zoom in and zoom out.

#### Pan

Keep left mouse button pressed and drag the image.

#### Zoom in a selected rectangle area

Use right mouse button to select an area. The selected area will be zoomed in to fit the window automatically when you release the right mouse button.

#### Reset zoom

Double click the right mouse button to reset zoom.

#### Multiple Tabs

Click `New Tab` button to new an empty tab.

# To-Do List

* Support opening image with file dialog
* Reduce the executable file size
