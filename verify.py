"""Verify a given image contains bytes from π.

Given command line arguments <start> and <file>, open the image file and check
if the data inside matches the hexadecimal expansion of π starting at the given
(1-indexed) starting point. (i.e. with π beginning 3.243f6a…, starting with the digit 2
corresponds to index 1, starting with f corresponds to index 4, etc.)
"""
from PIL import Image
import argparse
from urllib import request
import json

def getcontent(url):
    with request.urlopen(url) as req:
        return json.load(req)['content']

def getpihex(start, number):
    base = 'https://api.pi.delivery/v1/pi'
    result = ''
    while number:
        fetch = min(number, 1000)
        url = f'{base}?start={start}&numberOfDigits={fetch}&radix=16'
        hexits = getcontent(url)
        result += hexits
        number -= len(hexits)
        start += len(hexits)
    return result

def valid_image(name):
    """Open the given filename as an image.
    Convert exceptions to ArgumentTypeError for use with argparse.
    """
    try:
        return Image.open(name)
    except FileNotFoundError:
        raise argparse.ArgumentTypeError(f"No such file: '{name}'")
    except (OSError, IOError) as e:
        raise argparse.ArgumentTypeError(e)

parser = argparse.ArgumentParser(description="Verify an image contains bytes from π.")
parser.add_argument('start', type=int, help='Which hexadecimal digit to start with (1=first after decimal point)')
parser.add_argument('image', type=valid_image, help='The image to check')
args = parser.parse_args()

pixdata = args.image.tobytes().hex()
pihexits = getpihex(args.start, len(pixdata))

print(pixdata)
print(pihexits)
print(pixdata == pihexits)
