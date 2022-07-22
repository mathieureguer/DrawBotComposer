import time 
from . import UFOTextBloc
import importlib
importlib.reload(UFOTextBloc)
from .UFOTextBloc import *


t = time.time()

f = Font(path="/Users/Mathieu/Dropbox/10 current work/00 clients/Madeleine Creative/2014 Jardiland Font/30 ufos/Jardiland_Thin.ufo")
kp = KernParser(f)
f2 = Font(path="/Users/Mathieu/Dropbox/10 current work/00 clients/Madeleine Creative/2014 Jardiland Font/30 ufos/Jardiland_Black.ufo")
kp2 = KernParser(f2)
t = time.time()-t
print("opened fonts —", t)
t = time.time()

string = "This file contains information about the font itself, such as naming and dimensions. This file is optional. Not all values are required for a proper file. Changes from UFO 1 The key value pairs in the property list were modified and significantly expanded for UFO 2. The design of the structure follows these rules: All keys should be tagged for the format and//or table that they represent. For example, openTypeHheaAscender. \nIf data can be used for more than one format and/slash or table, it is considered generic and the format specific tag is removed. For example, familyName. In several cases, data moved to generic keys can be used in a controlled, slightly altered form for format specific fields. In these cases, information about how this can be done is provided. These are merely suggestions for the sake of clarity. Compiler developers are free to interpret these as they wish."

glyph_list = splittext_linebreak(string, f.unicodeData)

t = time.time()-t
print("splitted text —", t)
t = time.time()

newPage("A4")
translate((0), height())
translate(10, -10)
fill(0)
stroke(None)
comp = UFOTextBloc(
                 500, 
                 -400,
                 f, 
                 glyph_list, 
                 15, 
                 24,
                 letter_space=0,  
                 vertical_alignment="lineSpace",
                 kern=True,
                 # justification prefs
                 text_align="justify", 
                 text_align_last="center",
                 text_justify="distibuted", 
                 hyphenate=False,
                 max_word_length=15,
                 # drawing prefs
                 draw_grid=True,
                 draw_sidebarings=False,
                 draw_baseline=True,
                 draw_vertical_metrics=True,
                 draw_kern=False,
                 draw_spacer=False,
                 draw_glyphs=True)
comp.set_font(f2, kp2)
comp.set_pt_size(42)
comp.add_text(["h", "e", "l", "l", "o", "ampersand"])
comp.set_font(f, kp)
comp.set_pt_size(15)
comp.add_text(glyph_list)
comp.compose_text()
print(comp.text_overflow)

t = time.time()-t
print("composed text —", t)
t = time.time()

f = None
f2 = None