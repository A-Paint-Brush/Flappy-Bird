# Flappy Bird

This is a recreation of the game "Flappy Bird" written in Python, and with SDL2 as the graphics library.

![Game Screenshot](https://github.com/A-Paint-Brush/Flappy-Bird/assets/96622265/6c31d578-5eea-4d91-ad7d-9e749b0e652c)

## Installation Instructions

There are two ways of running the game. You can either run the code directly with a Python interpreter, or you can run the compiled version (for Windows). The compiled version is useful if you don't have a Python interpreter installed.

### Source-code Version

Download the files of this repository, then open a terminal and navigate into the root directory of this project. After that, simply run `pip3 install -r requirements.txt` to install the packages required to run this project. Once this is done, you should be able to launch the game by running `main.py`. On Windows, if you want to hide the console window while the game is running, you can either rename `main.py` to `main.pyw`, or create a shortcut file with the target set to `pythonw main.py`.

#### Unused Files

If you want to save disk space, there are some files and folders that can be deleted. Only the `./Fonts`, `./Help`, `./Images`, and `./Sounds` folders are used by the game at run-time. The remaining folders can be safely deleted. As for files, all files in the root directory of the project that isn't a Python file (.py) can be deleted. Therefore, you can delete this README file, `requirements.txt`, and `compile_info.spec`.

### Frozen Version

If you don't need an installer, download this repository and keep the folder `./Installer/Flappy Bird`. After that, run the `Flappy Bird.exe` file in the folder to launch the game. If you need an installer, [download](https://github.com/A-Paint-Brush/Flappy-Bird/raw/main/Installer/Installer.msi) the file `Installer.msi` and double click it to launch the installer.

## Compiling

If you're using an OS other than Windows, and want to create a Pyinstaller bundle for your OS, you can do so simply by opening a terminal in this folder and running `pyinstaller compile_info.spec`. After the bundle has been created, copy the `./Fonts`, `./Help`, `./Images`, and `./Sounds` folders into the bundle's root directory, and the bundle should be ready to run.

## How to Play

Game-play instructions are stored in the file `./Help/Instructions.txt`. The file can also be accessed in the game by clicking the "How to Play" button in the main menu.

## Credits

The fonts in `./Fonts` are provided by Microsoft. The images in the `./Images/Digits` and `./Images/Sprites` folder were found on the internet and probably were extracted from the original game. The images in `./Images/Icons` were all drawn by me except for the `window_icon.png` file, which is just a resized version of `./Images/Sprites/flap up.png`. The `./Unused Assets/SVGs` folder contains the SVG versions of the images in `./Images/Icons`, and they were all drawn in Inkscape by me. The files in the `./Unused Assets/Window Icons` folder are all resized/modified versions of `./Images/Sprites/flap up.png`. The audio file `./Sounds/Rickroll.wav` is a short audio clip of the song ["Rick Astley - Never Gonna Give You Up"](https://www.youtube.com/watch?v=dQw4w9WgXcQ) on YouTube.
