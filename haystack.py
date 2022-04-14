"""Place an image found by pifind in an image of first 10^8 hex digits of π.

Requires command line arguments <image>, whose pixel data must be somewhere
within the first 100,000,000 hex digits of π, and <output>, the name for a new
image (include the extension.)

The file pi_hex_1b.txt, or pi_hex_1b.zip, as downloaded from
https://archive.org/details/pi_hex_1b is required in the same directory.
"""
import io
import os
import sys
import argparse
from math import sqrt
from zipfile import ZipFile
from itertools import product
from PIL import Image

HEXFILE = 'pi_hex_1b.txt'
ZIPFILE = 'pi_hex_1b.zip'
HEXDIGS = 100_000_000

def valid_image(name):
    """Open the given filename as an image.
    Convert exceptions to ArgumentTypeError for use with argparse.
    """
    try:
        return Image.open(name)
    except FileNotFoundError:
        raise argparse.ArgumentTypeError(f'No such file: "{name}"')
    except (OSError, IOError) as e:
        raise argparse.ArgumentTypeError(e)

def check_ext(name):
    """Check if filename has an extension recognized by Pillow."""
    ext = name.split('.')[-1]
    return ('.'+ext) in Image.registered_extensions()

parser = argparse.ArgumentParser(description='Create a giant (50 megapixel) image containing the given image found in π.')
parser.add_argument('original', type=valid_image, help='The original image found in π')
parser.add_argument('newname', type=str, help='The new image which will be created')
args = parser.parse_args()

if not check_ext(args.newname):
    sys.exit(f'"{args.newname}" does not end in a recognized image extension')

if os.path.exists(HEXFILE):
    with open(HEXFILE) as fid:
        fid.read(2)
        pihex = fid.read(HEXDIGS)
elif os.path.exists(ZIPFILE):
    with ZipFile(ZIPFILE) as zf:
        with zf.open(HEXFILE) as fid:
            fid = io.TextIOWrapper(fid, encoding='ascii')
            fid.read(2)
            pihex = fid.read(HEXDIGS)
else:
    sys.exit(f'Either {HEXFILE} or {ZIPFILE} must be provided in the working directory.')

target = args.original
if target.mode != 'P':
    sys.exit('Given image must be paletted (as produced by pifind)')
width, height = target.size
numpix = width*height
palette = target.getpalette()
palette = list(zip(palette[::3], palette[1::3], palette[2::3]))
imgbytes = target.tobytes()
imghex = imgbytes.hex()

# Some of the palette entries may be unused.
# This results in a monotonous haystack with less variety of color than otherwise.
# Fill in the unused entries with some different colors (from the WebSafe palette).
unused = set(range(256)) - set(imgbytes)

def coldist(col1, col2):
    """Simple color distance metric."""
    return sum((a-b)**2 for a,b in zip(col1, col2))

def mindist(col):
    """Min distance of col from any member of palette."""
    return min(coldist(c, col) for c in palette)

def flatten(pal):
    """list of 256 triples -> list of 768"""
    flatpal = []
    for col in pal:
        flatpal.extend(col)
    return flatpal

if {palette[u] for u in unused} != {(0, 0, 0)}:
    print("The unused palette entries are not all black, as I'd expect (and as "
          "pifind or makeimage would produce them). So we'll use the palette "
          "as-is and not reassign unused entries.")
else:
    websafe = sorted(product(range(0,256,51), repeat=3), key=mindist, reverse=True)
    for byt, col in zip(unused, websafe):
        palette[byt] = col

try:
    index = pihex.index(imghex)
except ValueError:
    sys.exit(f'Could not find image bytes within first {HEXDIGS} hex digits of π!')

# We want to cut pihex so that an exact multiple of 2*numpix shows up before index,
# and after, too.
numhex = 2*numpix
offset = index % numhex
maxcopy = (HEXDIGS - offset) // numhex
pibytes = bytes.fromhex(pihex[offset:maxcopy*numhex+offset])

cols = round(sqrt(len(pibytes)) / width)
rows = round(len(pibytes) / (cols*width)) // height
haysize = (cols*width, rows*height)

# break pibytes into chunks of size numpix
tiles = [pibytes[numpix*i:numpix*(i+1)] for i in range(rows*cols)]
# break each tile into rows of target width
tiles = [[t[width*i:width*(i+1)] for i in range(height)] for t in tiles]

haydata = []

for r in range(rows):
    rowtiles = tiles[cols*r:cols*(r+1)]
    for h in range(height):
        for c in range(cols):
            haydata.extend(rowtiles[c][h])

haystack = Image.new('P', haysize)
haystack.putpalette(flatten(palette))
haystack.putdata(haydata)
haystack.save(args.newname)
