# FDC1004Q GUI
This is a Kivy-based GUI for interfacing with a FDC1004Q capacitive sensor connected to a PSoC device.
You can find the companion firmware for this GUI at the following [repository](https://github.com/dado93/PSoC-FDC1004Q).

## Setup
- Install Python > 3
- Install [virtualenv](https://docs.python-guide.org/dev/virtualenvs/)
- Activate the virtualenv using either:
    - source ./venv/bin/activate on MacOS
    - .\venv\Scripts\activate on Windows
- Install [Kivy](https://kivy.org/#home)
- Install [PySerial](https://pypi.org/project/pyserial/)
- Install firwmare on PSoC Microcontroller
- Start the GUI: `(venv) python main.py`