import os
import sys
from pathlib import Path


def data_dir():
    root = Path(os.environ.get('GAS_HUNAR_DATA', Path(os.environ.get('LOCALAPPDATA', Path.home() / '.local/share')) / 'GAS HUNAR'))
    root.mkdir(parents=True, exist_ok=True)
    return root


def resource(name):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1])) / name
