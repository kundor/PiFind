"""Create an image with bytes from π.

Given command line arguments <start> <target> <out>, create a new image <out>
of the same size as <target> whose pixel data are bytes from π starting at the
<start>th hexadecimal digit after the decimal point, and add a palette
attempting to make it look like the original.
"""
from PIL import Image
import sys
import json
from urllib import request
from collections import Counter

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

def flatten(pal):
    """list of 256 triples -> list of 768"""
    flatpal = []
    for col in pal:
        flatpal.extend(col)
    return flatpal

start = int(sys.argv[1])
imgname = sys.argv[2]
newname = sys.argv[3]
target = Image.open(imgname).convert('RGB')
numpix = target.size[0] * target.size[1]
colors = list(target.getdata())

pihexits = getpihex(start, numpix*2)
pixbytes = bytes.fromhex(pihexits)

bytarr = [Counter() for _ in range(256)]
for byt, col in zip(pixbytes, colors):
    bytarr[byt][col] += 1
palette = [colavg(b) for b in bytarr]

img = Image.new('P', target.size)
img.putpalette(flatten(palette))
img.putdata(pixbytes)
img.save(newname)
