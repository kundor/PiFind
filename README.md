# PiFind

This searches the digits of π for a sequence of bytes which can match the pattern
in a target image, so that a palette can be chosen to approximate the target image
using a contiguous sequence from π as the pixel data.

See https://kundor.github.io/Finding-Waldo/ for an example.

The script requires the Python package [Pillow](https://python-pillow.org/).
You can probably install it by running the command

`python3 -m pip install Pillow`.

Otherwise, I've written it to only use the standard library, so it should run
with Python 3 (probably with versions 3.6+).

1. Download the script `pifind.py`  (Note: you only need this file, not the whole repository.)
2. Optionally, download `pi_hex_1b.zip` from [archive.org/details/pi\_hex\_1b](https://archive.org/details/pi_hex_1b)
   and place it in the same directory.
   This will speed up the search. Otherwise, digits will be fetched from the Web at https://pi.delivery.
3. In the same directory, place the image to search for as `target.png`. It should be not
   much more than 500 pixels (around 22x23 or smaller) and use at most 6 distinct colors.
4. Run `python3 pifind.py`

The "best" image found so far will be saved as `found.gif`.

What the script considers "best" might not match what a human thinks looks good.
You might want to check out the candidates as they're found and save ones you like
under a different name.

The script output includes the digit index where the current best image starts.
You probably want to make a note of that.

PiFind has been tested on Ubuntu, Funtoo, and Windows (in `cmd.exe`), using Python versions from 3.6 to 3.10,
so with luck it will work for you.

Some additional little utility scripts are present:

* `verify.py` verifies if any image file contains hex digits from π starting from a given index.  
  Call it like `python3 verify.py <index> <image file name>`
* `makeimage.py` creates an image approximating a given image with hex digits starting from a given index.
  This is handy if you already know the offset and don't want to spend time searching through π.  
  Call it like `python3 makeimage.py <index> <target image> <new image>`
* `haystack.py` creates a giant image of the first 100 million hexadecimal digits of π, colored with the
  palette from a found image, and aligned so that the image shows up.
  The image has to be present in the first 100 million hex digits!
  This one requires `pi_hex_1b.zip` to be present, unlike the other scripts (which require an
  internet connection instead).  
  Call it like `python3 haystack.py <found image> <new image>`
* `depalette.py` removes the palette from an image and saves the same data interpreted as grayscale
  and with the [Plan9 palette](https://purisa.me/blog/plan9-cube/).  
  Call it like `python3 depalette.py <found image> <new grayscale image> <new plan9 image>`
