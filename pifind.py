"""Look for target.png in the digits of π.

This script should be executed in the same directory as an image, target.png,
which should be as small as possible (max around 22x22 pixels) and use
as few distinct colors as possible (max about six).

If the file pi_hex_1b.txt, or pi_hex_1b.zip, as downloaded from
https://archive.org/details/pi_hex_1b is present in the same directory,
it will be used as a source of hexadecimal digits from π. Otherwise, digits
will be fetched from the API provided by Google at https://pi.delivery.

In the case of using the online service, it will continue until stopped
(e.g. Ctrl-C) because there are 50 trillion digits available.

In the case of using pi_hex_1b.txt, it will continue until finishing the
billion digits, which might take a few days.

The best image found so far is saved as found.gif.
"""
import os
import sys
import signal
from collections import Counter, deque
from itertools import islice
from PIL import Image

HEXFILE = 'pi_hex_1b.txt'
ZIPFILE = 'pi_hex_1b.zip'

def PiFileReader(fid, numread=10_000_000):
    """Given a file-like object, containing text hexadecimal digits,
    yield lists of numread digits. fid should provide bytes."""
    fid.seek(2) # skip '3.'
    while True:
        data = fid.read(numread)
        yield data
        if len(data) < numread: # hit end of file
            break

def PiZipFileReader(filename):
    import zipfile
    zf = zipfile.ZipFile(filename)
    if zf.namelist() != [HEXFILE]:
        raise FileNotFoundError(f'zip file does not contain exactly one file, {HEXFILE}, as expected')
    fid = zf.open(HEXFILE)
    yield from PiFileReader(fid)

def PiDelivery(numread=1000): # 1000 is the max digits supported per request
    from urllib import request
    import json
    base = 'https://api.pi.delivery/v1/pi'
    start = 1
    while True:
        with request.urlopen(f'{base}?start={start}&numberOfDigits={numread}&radix=16') as req:
            j = json.load(req)
            yield j['content'].encode()
        start += numread

def colhex(col):
    """RGB hex code #000000 for a color triple."""
    return '#' + ''.join(f'{c:02X}' for c in col)

def colorsummary(C, maxlist=10):
    """Summarize a Counter of RGB colors."""
    for i, (col, num) in enumerate(C.most_common(maxlist), 1):
        print(f'{i:2}. {colhex(col)}, {num:3}')

def coldist(col1, col2):
    """Simple color distance metric."""
    # could be math.dist in Python 3.8+
    return sum((a-b)**2 for a,b in zip(col1, col2))

def colpick(colors, col):
    """Given a list of colors, pick the one closest to col."""
    return min(colors, key=lambda c: coldist(col, c))

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

def colorfamilies(C, dist=250):
    """Find sets of colors (from a Counter) which are near each other.
    We use a very simple color-nearness metric: the sum of squared differences
    between R, G, and B being less than 250.
    The returned set of colors is the weighted means of the constitutent
    colors in each family.
    This does not find the most optimal breakdown, even with such a simple metric,
    because it compares each color in the image to the most common color of each family so far,
    and does not explore the color space for potential "family centers" closer to more colors.
    If you want a better breakdown into few colors, recolor your target image manually!
    """
    families = {}
    for col, num in C.most_common():
        for famcol in families:
            if coldist(col, famcol) < dist:
                families[famcol][col] = num
                break
        else: # not close to any family
            families[col] = {col: num}
    return Counter({colavg(wts) : sum(wts.values()) for wts in families.values()})

def sievecolors(C, numpix):
    """Make a list of the colors in a Counter with non-trivial numbers of pixels.
    Ignore colors covering less than 1% of the image.
    """
    thresh = max(round(.01*numpix), 2)
    return [col for col in C if C[col] > thresh]

def reducecolors(C, numpix):
    """Iterate color family reduction, trying to merge families."""
    numcol = len(C)
    oldnum = numcol + 1
    dist = 250
    while 6 < numcol and dist < 1000:
        if numcol == oldnum:
            dist += 20
        oldnum = numcol
        C = colorfamilies(C, dist)
        numcol = len(C)
    return sievecolors(C, numpix)

def recolor(img, colors):
    """Create a version of img with colors limited to those given."""
    newimg = Image.new('RGB', img.size)
    newimg.putdata([colpick(colors, c) for c in img.getdata()])
    return newimg

def printpattern(pat, width, height):
    """Print a list of ints in the shape given."""
    lines = [''.join(str(i) for i in pat[width*j:width*(j+1)]) for j in range(height)]
    print(*lines, sep='\n')

if os.path.exists(HEXFILE):
    pigen = PiFileReader(open(HEXFILE, 'rb'))
elif os.path.exists(ZIPFILE):
    pigen = PiZipFileReader(ZIPFILE)
else:
    pigen = PiDelivery()

target = Image.open('target.png').convert('RGB')
numpix = target.size[0] * target.size[1] # math.prod in Python 3.8+

C = Counter(target.getdata())
numcol = len(C)
if numcol > 6:
    print(f'target.png has {numcol} colors, which is too many.')
    colorsummary(C)
    print('Should we:',
          '1. Limit to the most common {3, 4, 5, or 6} colors?',
          '2. Try to identify colors which are close to eachother?',
          '3. Quit to edit the image?', sep='\n\t')
    choice = input('Choose 1, 2, or 3: ')
    if choice == '1':
        numcol = int(input('Limit to 3, 4, 5, or 6? '))
        if numcol < 3 or numcol > 6:
            sys.exit('Invalid choice')
        colors = [col for col, num in C.most_common(numcol)]
    elif choice == '2':
        colors = reducecolors(C, numpix)
        numcol = len(colors)
        if numcol > 6:
            print(f'Sorry, I was only able to reduce it to {numcol} families of nearby colors,'
                  ' which is still too many.')
            sys.exit('Please edit target.png manually to have fewer distinct colors.')
    else:
        sys.exit('Quitting')
    print('Saving color-limited file as newtarget.png')
    recolor(target, colors).save('newtarget.png')
else:
    colors = list(C.keys())

print(f'Selected {numcol} colors for the pattern.')
pattern = [colors.index(colpick(colors, c)) for c in target.getdata()]
colorsummary(Counter(colors[i] for i in pattern))
print('Pattern of colors to try to match:')
printpattern(pattern, *target.size)

def dribble(gen):
    for bunch in gen:
        for digit in bunch:
            yield digit - (48 if digit < 58 else 87)
            # converts 0..9, a..f (ASCII 48..57, 97..102) to int

def countmismatch(bytarr):
    """Given a list of 256 lists, with # of each color, determine least mismatches.
    This is the number of pixels not matching the 'dominant' (most common) color
    for that byte.
    Also return the number of "muddled" pixels that mix every color (as a tiebreaker).
    """
    mis = 0
    muddle = 0
    for colcounts in bytarr:
        totpix = sum(colcounts) # total pixels mapped by this byte
        mis += totpix - max(colcounts) # if we use the byte to map the most frequent color,
        # the rest are mismatches.
        if min(colcounts): # byte needs to map all colors
            muddle += totpix
    return mis, muddle

def headline():
    """Print headers for the status line."""
    print('Digits checked  Best match at  Pixel mismatches  Bytes in match')
    print('--------------  -------------  ----------------  --------------')

def status(startpos, minmisrpt, index, bestbytes):
    """Print a status line (overwriting current line)."""
    bytepreview = bestbytes[:12].hex()
    print(f'\r{startpos:14,}  {index:13,}  {minmisrpt!s:16}  {bytepreview}…', end='', flush=True)

def makepalette(bytarr, colors):
    """Create a palette (list of 256 RGB triples) mapping each byte to the weighted
    average of its colors.
    """
    return [colavg(dict(zip(colors, b))) for b in bytarr]

def flatten(pal):
    """list of 256 triples -> list of 768"""
    flatpal = []
    for col in pal:
        flatpal.extend(col)
    return flatpal

def saveimg(name, size, palette, byts):
    img = Image.new('P', size)
    img.putpalette(flatten(palette))
    img.putdata(byts)
    img.save(name)

def deferinterrupt(signum, frame):
    """Wait for nice point before quitting, unless re-signaled."""
    if deferinterrupt.nomore:
        raise KeyboardInterrupt
    deferinterrupt.nomore = True

def ordinal(n):
    """Ordinal version (1st, 2nd, 3rd, 4th, ...) of n."""
    ends = ['th', 'st', 'nd', 'rd', 'th']
    if (n % 100) // 10 == 1:
        return f'{n:,}th'
    return f'{n:,}' + ends[min(n%10, 4)]

deferinterrupt.nomore = False

cur = deque(maxlen=numpix)  # bytes constructed from even-aligned hex digits 3.'24','3f','6a', etc.
other = deque(maxlen=numpix) # bytes constructed from odd-aligned hex digits '32' '43', 'f6', 'a8', etc.
oldhalf = 3
minmisrpt = (numpix, numpix)

signal.signal(signal.SIGINT, deferinterrupt)
signal.signal(signal.SIGTERM, deferinterrupt)
if hasattr(signal, 'SIGBREAK'):
    signal.signal(signal.SIGBREAK, deferinterrupt)
if hasattr(signal, 'SIGQUIT'):
    signal.signal(signal.SIGQUIT, deferinterrupt)

headline()

for startpos, halfbyte in enumerate(dribble(pigen)):
    cur, other = other, cur
    cur.append(oldhalf << 4 | halfbyte)
    oldhalf = halfbyte
    if len(cur) < numpix:
        continue
    bytarr = [[0]*numcol for _ in range(256)]
    for b, p in zip(cur, pattern):
        bytarr[b][p] += 1
    misrpt = countmismatch(bytarr)
    if misrpt < minmisrpt:
        minmisrpt = misrpt
        index = startpos - numpix*2 + 1
        bestbytes = bytes(cur)
        status(startpos, minmisrpt, index, bestbytes)
        fitpal = makepalette(bytarr, colors)
        saveimg('found.gif', target.size, fitpal, bestbytes)
        if misrpt[0] == 0:
            print(f"\nSuccess at {index}")
            break
    if not startpos % 5000:
        print(f'\r{startpos:14,}', end='', flush=True)
    if deferinterrupt.nomore:
        break
sys.exit('\nInterrupted. Best result is saved as found.gif.\n'
         f'It contains the {ordinal(index+1)} through {ordinal(index+2*numpix)} hexadecimal digits of π.\n'
         f'Equivalently, the {ordinal(4*index+1)} through {ordinal(4*index+8*numpix)} bits.')
