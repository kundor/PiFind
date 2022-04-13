"""Verify a given image contains bytes from π.

Given command line arguments <start> and <file>, open the image file and check
if the data inside matches the hexadecimal expansion of π starting at the given
(1-indexed) starting point. (i.e. with π beginning 3.243f6a…, starting with the digit 2
corresponds to index 1, starting with f corresponds to index 4, etc.)
"""
from PIL import Image
import sys
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
    return result

start = int(sys.argv[1])
imgname = sys.argv[2]
img = Image.open(imgname)
pixdata = img.tobytes().hex()

pihexits = getpihex(start, len(pixdata))

print(pixdata)
print(pihexits)
print(pixdata == pihexits)
