"""Create an image with bytes from π.

Given command line arguments <start> <target> <out>, create a new image <out>
of the same size as <target> whose pixel data are bytes from π starting at the
<start>th hexadecimal digit after the decimal point, and add a palette
attempting to make it look like the original.
"""
import json
import argparse
from urllib import request
from itertools import chain
from collections import Counter
from PIL import Image

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

def colavg(wts):
    """Given a dictionary of RGB triples : counts, return an averaged color."""
    R = G = B = 0
    totct = 0
    for (cr, cg, cb), num in wts.items():
        R += cr*num
        G += cg*num
        B += cb*num
        totct += num
    if not totct:
        return (0, 0, 0)
    return (round(R/totct), round(G/totct), round(B/totct))

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

def check_ext(name):
    """Check if filename has an extension recognized by Pillow."""
    ext = name.split('.')[-1]
    if ('.'+ext) not in Image.registered_extensions():
        raise argparse.ArgumentTypeError(f'"{name}" does not end in a recognized image extension')
    return name

parser = argparse.ArgumentParser(description='Create an image containing bytes from π.')
parser.add_argument('start', type=int, help='Which hexadecimal digit to start with (1=first after decimal point)')
parser.add_argument('target', type=valid_image, help='The image to approximate')
parser.add_argument('out', type=check_ext, help='New image to make')
args = parser.parse_args()

target = args.target.convert('RGB')
numpix = target.size[0] * target.size[1]
colors = list(target.getdata())

pihexits = getpihex(args.start, numpix*2)
pixbytes = bytes.fromhex(pihexits)

bytarr = [Counter() for _ in range(256)]
for byt, col in zip(pixbytes, colors):
    bytarr[byt][col] += 1
palette = [colavg(b) for b in bytarr]

img = Image.new('P', target.size)
img.putpalette(chain(*palette))
img.putdata(pixbytes)
img.save(args.out)
