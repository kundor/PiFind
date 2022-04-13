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
from math import sqrt
from zipfile import ZipFile
from PIL import Image

HEXFILE = 'pi_hex_1b.txt'
ZIPFILE = 'pi_hex_1b.zip'
HEXDIGS = 100_000_000

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

imgname = sys.argv[1]
newname = sys.argv[2]
target = Image.open(imgname)
if target.mode != 'P':
    sys.exit('Given image must be paletted (as produced by pifind)')
width, height = target.size
numpix = width*height
palette = target.getpalette()
imgbytes = target.tobytes()
imghex = imgbytes.hex()

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
haystack.putpalette(palette)
haystack.putdata(haydata)
haystack.save(newname)
