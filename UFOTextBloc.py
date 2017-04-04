from __future__ import division

from DrawBotComposer import *
from defcon.objects.font import Font


def splittext_linebreak(string, cmap, linebreaks="\n"):
    """ uses defconAppKit splittext, preserve line breaks """
    from defconAppKit.tools.textSplitter import splitText
    paragraphs = string.split(linebreaks)
    glyph_lists = [splitText(p, cmap) for p in paragraphs]
    return reduce(lambda a, b:a+[linebreaks]+b, glyph_lists)


class UFOTextBloc(DrawBotComposer):
    def __init__(self, 
                 width, 
                 height,
                 font, 
                 glyph_list, 
                 pt_size, 
                 line_space,
                 letter_space=0,  
                 vertical_alignment="baseline",
                 kern=True,
                 # justification prefs
                 text_align="left", 
                 text_align_last="left",
                 text_justify="inter-word", 
                 hyphenate=True,
                 max_word_length=15,
                 # drawing attr
                 draw_grid=False,
                 draw_sidebarings=False,
                 draw_vertical_metrics=False,
                 draw_baseline=False,
                 draw_kern=False,
                 draw_spacer=False,
                 draw_glyphs=True,
                 # drawing style attr 
                 grid_stroke = (0, 0, 1),
                 grid_strokeWidth = .4,
                 kern_fill = (0, 1, 1),
                 kern_caption_font = "Monaco",
                 kern_caption_fontSize = 1,
                 ):
                     
        super(UFOTextBloc, self).__init__()

        # init necessary attr
        self.slugs = []
        self.current_slug = []
        self._glyph_repr =  {}
        self.previous_glyph = None
        self.linebreaks = ["\n"]
        self.text_overflow = None

        # bloc attr
        self.width = width
        self.height = height

        # font attr
        self.kern = kern
        self.pt_size = pt_size
        self.font = None
        self.set_font(font)
        self.line_space = line_space
        self.letter_space = letter_space

        # justification attr
        self.text_align=text_align
        self.text_align_last=text_align_last
        self.text_justify=text_justify
        self.hyphenate=hyphenate
        self.max_word_length=max_word_length
        self.draw_vertical_metrics = draw_vertical_metrics
        self.draw_baseline = draw_baseline

        # grid drawing attr
        self.draw_grid = draw_grid
        self.draw_glyphs = draw_glyphs
        self.draw_kern = draw_kern
        self.draw_sidebarings = draw_sidebarings

        self.draw_spacer = draw_spacer

        # drawing style attr 
        self.grid_stroke = grid_stroke
        self.grid_strokeWidth = grid_strokeWidth
        self.kern_fill = kern_fill
        self.kern_caption_font = kern_caption_font
        self.kern_caption_fontSize = kern_caption_fontSize

        if self.draw_grid == True:
            self._draw_grid_box()
        
        self._set_vertical_alignment(vertical_alignment)
        
        
        self.addObserver(self, "width_overflow", "DrawBotComposer.didOverflowWidth")
        self.addObserver(self, "height_overflow", "DrawBotComposer.didOverflowHeight")
        
        self.add_text(glyph_list)

        
    def compose_text(self):
        """ draw the processed text """
        self.translate_back_to_origin()
        self._set_vertical_alignment(self.vertical_alignment)
        # add reamining slug to the slugs
        if len(self.current_slug) > 0 and self.text_overflow == None:
            self.current_slug.append({"type":"newline"})
            self.slugs.append(self.current_slug)
        # draw
        #while self.text_overflow == None:
        for s in self.slugs:
            if len(s) > 0:
                self._draw_slug(s, 
                        text_align=self.text_align,
                        text_align_last=self.text_align_last,
                        text_justify=self.text_justify,
                        hyphenate=self.hyphenate,
                        max_word_length=self.max_word_length)
        self.translate_back_to_origin()
        return self.text_overflow
        

    # OBSERVERS

    def width_overflow(self, sender):
        self._new_line()
        

    def height_overflow(self, sender):
        if sender.data['overflow_height'] > 0:
            pass
        else:
            self.text_overflow = self.glyph_list
       
    #  setter and getter
        
    def add_text(self, glyph_list, notdef=".notdef"):
        self.glyph_list = glyph_list[:]

        # trigger overwritten functio
        self.will_preprocess_line()
        
        while len(self.glyph_list) > 0 and self.text_overflow == None:
            n = self.glyph_list.pop(0)

            if n in self.linebreaks:
                self.current_slug.append({"type":"newline"})
                self._new_line()
            else:
                if n in self._font_keys:
                    g = self.font[n]
                elif notdef in self._font_keys:
                    g = self.font[notdef]
                else:
                    g = None
                if g != None:
                    # trigger overwritten function
                    self.will_preprocess_glyph()

                    p = self._get_glyph_representation(g)
                    path = BezierPath()
                    path.appendPath(p)
                    path.scale(self.ratio)

                    # check if the current glyph wont overshoot width boundaries
                    if path.bounds():
                        self.bump(g.width*self.ratio, 0)
                    
                    # fetch kern  
                    if self.kern_parser and self.previous_glyph:
                        k = self.kern_parser.get_kerning_pair_value((self.previous_glyph, n))
                        if k:
                            self.current_slug.append({"type":"kern", "width":k*self.ratio})
                            self.translate(k*self.ratio, 0)

                    # add glyph to the slug
                    self.current_slug.append({"type":"glyph", "path":path, "width":g.width*self.ratio, "glyph":g, "ratio":self.ratio})
                    self.translate(g.width*self.ratio, 0)
                    
                    # trigger overwritten function
                    self.did_preprocess_glyph()

                    self.previous_glyph = n


    def set_font(self, font, kern_parser=None):
        if font != self.font:
            self.font = font
            self._font_keys = font.keys()
            self._get_ratio()
            self.previous_glyph = None
            if self.kern == True and kern_parser == None:
                self.kern_parser = KernParser(font)
            else:
                self.kern_parser = kern_parser


    def set_pt_size(self, pt_size):
        self.pt_size = pt_size
        self._get_ratio()



    # overwritable functions

    def will_preprocess_glyph(self):
        pass

    def did_preprocess_glyph(self):
        pass

    def will_preprocess_line(self):
        pass

    def did_preprocess_line(self):
        pass

    def will_draw_glyph(self):
        pass

    def did_draw_glyph(self):
        pass

    def will_draw_slug(self):
        pass

    def did_draw_slug(self):
        pass
      

    # helpers

    def _new_line(self):
        """
        assert the current slug
        Move to the start of a new line.
        """
        if len(self.current_slug) > 0:
            rest = self._hyphenate_slug(self.current_slug, hyphenate=self.hyphenate)
        else:
            rest = None
        self.slugs.append(self.current_slug)

        # go to the start of the next line
        self.translate_back_to_origin_x()
        self.translate(0, -self.line_space)
        
        # trigger overwritten functio
        self.did_preprocess_line()

        # add a potential rest to the next current slug
        if rest:
            self.current_slug = rest
            self.previous_glyph = rest[-1].get("glyph", None)
            self.translate(self._get_slug_width(rest), 0)

        # or prep a new slug
        else:
            self.current_slug = []
            self.previous_glyph = None

        # trigger overwritten function
        self.will_preprocess_line()


    def _get_ratio(self):
        self.ratio = self.pt_size/self.font.info.unitsPerEm


    def _set_vertical_alignment(self, alignment):
        self.vertical_alignment = alignment
        self._get_ratio()
        if alignment == "lineSpace":
            self.translate(0, -self.line_space)
        elif alignment in ["ascender", "descender", "capHeight", "xHeight"]:
            align = getattr(self.font.info, alignment)
            self.translate(0, -align*self.ratio)


    def _get_glyph_representation(self, glyph):
        """ get a glyph repr, will cache the result """
        if not self._glyph_repr.has_key(glyph):
            self._glyph_repr[glyph] = glyph.getRepresentation('DBComposer_BezierPath')
        return self._glyph_repr[glyph]


    # Slug helpers

    def _hyphenate_slug(self, slug, hyphenate=True, max_word_length=15):
        rest = None
        if hyphenate == False:
             last_space_index = self._find_slug_last_nonmarking(slug)
             pre_rest = slug[last_space_index+1:]
             if self._get_slug_glyph_count(pre_rest) < max_word_length:
                 rest = pre_rest
                 self.current_slug = slug[:last_space_index+1]
        return rest
                  

    def _find_slug_last_nonmarking(self, slug):
        for i, g in reversed(list(enumerate(slug))):
            if g["type"] == "newline" or (g["type"] == "glyph" and not g["path"].bounds()):
                break
        return i


    def _get_slug_width(self, slug):
        return sum(i.get("width", 0) for i in slug)
        

    def _get_slug_spacer_count(self, slug):
        out = sum(i.get("type", None) == "spacer" for i in slug)
        # little hack to prevent division by 0
        # must investigate
        if out == 0:
            out = 1
        return out
        

    def _get_slug_glyph_count(self, slug):
        return sum(i.get("type", None) == "glyph" for i in slug)

    def _justify_slug(self, 
                      slug, 
                      text_align="justify", 
                      text_align_last="left",
                      text_justify="inter-word"):        
        if len(slug) > 0:
            if slug[-1]["type"] == "newline":
                text_align = text_align_last
                slug.pop()
        if len(slug) > 0:      
            # get rid of trailing space
            while len(slug) > 0 and slug[-1]["type"] == "glyph" and slug[-1]["path"].bounds() == None:
                slug.pop()
            # get rid of trailing kern on both side
            while len(slug) > 0 and slug[0]["type"] == "kern":
                slug.pop(0)
            while len(slug) > 0 and slug[-1]["type"] == "kern":
                  slug.pop()

        if len(slug) > 0:
            if text_align == "left":
                slug.append({"type":"spacer"})
            elif text_align == "right":
                slug.insert(0, {"type":"spacer"})
            elif text_align == "center":
                slug.insert(-1, {"type":"spacer"})
                slug.insert(0, {"type":"spacer"})
            elif text_align == "justify" :
                if text_justify == "distribute":
                    non_marking_only = False
                else:
                    non_marking_only = True
                slug = self._insert_spacers(slug, non_marking_only=non_marking_only)
        return slug
       

    def _insert_spacers(self, slug, non_marking_only=False):
        new_slug = []
        for i in slug:
            new_slug.append(i)
            if i["type"] == "glyph":
                if non_marking_only:
                    if not i["path"].bounds():
                       new_slug.append({"type":"spacer"})
                else:
                    new_slug.append({"type":"spacer"})
        # delete last spacer
        if new_slug[-1]["type"] == "spacer":
            new_slug.pop()
        return new_slug

    # DRAWERS      

    def _draw_slug(self, 
                  slug, 
                  text_align="justify", 
                  text_align_last="left",
                  text_justify="inter-word", 
                  hyphenate=True,
                  max_word_length=15):

        # trigger overwritten functio
        self.will_draw_slug()

        slug = slug[:]
        
                    
        slug = self._justify_slug(slug, 
                                  text_align=text_align, 
                                  text_align_last=text_align_last, 
                                  text_justify=text_justify)

        if len(slug) > 0:

            x = self.current_position_x
        
            if self.width:
                remaining = self.width-0.2 - self._get_slug_width(slug)
                spacer = remaining/(self._get_slug_spacer_count(slug))
            else:
                spacer = 0

            # draw the grid, if necessary 
            if self.draw_baseline:
                self._draw_baseline()

            last_vert_metrics_x_position = self.current_position_x
            current_ratio = None
            current_font = None

            for i in slug:
                if i["type"] == "glyph":
                    self.current_glyph = i["glyph"]
                    self.font = self.current_glyph.getParent()
                    self.ratio = i["ratio"]
                    width = i["width"]
                    if self.draw_sidebarings:
                        self._draw_grid_sidebarings(width, self.font, self.ratio)
                    if self.font != current_font or self.ratio != current_ratio:
                        if self.draw_vertical_metrics and current_font != None and current_ratio != None:
                            self._draw_vertical_metrics((last_vert_metrics_x_position, self.current_position_x), current_font, current_ratio)
                            last_vert_metrics_x_position = self.current_position_x
                    current_font = self.font
                    current_ratio = self.ratio

                    self.translate(width, 0)
                elif i["type"] == "kern":
                    k = i["width"]
                    if self.draw_kern:
                        self._draw_kern(k, self.font, self.ratio)
                    self.translate(k, 0)
                elif i["type"] == "spacer":
                    if self.draw_spacer:
                        self._draw_spacer(spacer, self.font, self.ratio)
                    self.translate(spacer, 0)

            if self.draw_vertical_metrics:
                self._draw_vertical_metrics((last_vert_metrics_x_position, self.current_position_x), current_font, current_ratio)


            self.translate(-self.current_position_x + x, 0)
        

            # draw the actual glyphs
            for i in slug:
                if i["type"] == "glyph":
                    self.current_glyph = i["glyph"]
                
                    # trigger overwritten function
                    self.will_draw_glyph()

                    path = i["path"]
                    width = i["width"]
                    if self.draw_glyphs:
                        drawPath(path)
                    self.translate(width, 0)

                    # trigger overwritten function
                    self.did_draw_glyph()

                elif i["type"] == "kern":
                    k = i["width"]
                    self.translate(k, 0)
                elif i["type"] == "spacer":
                    self.translate(spacer, 0)
            
            self.translate(-self.current_position_x + x, 0)
            self.translate(0, -self.line_space)
            # trigger overwritten functio
            self.did_draw_slug()

    
    # GRID DRAWERS

    def _draw_grid_box(self):
        save()
        self._apply_grid_param()
        if self.width == None:
            w = width()
        else:
            w = self.width
        if self.height == None:
            h = -height()
        else:
            h = self.height
        rect(0, 0, w, h)
        restore()
              

    def _draw_baseline(self):
        save()
        self._apply_grid_param()
        line((0, 0), (self.width, 0))
        restore()

    def _draw_vertical_metrics(self, (start, finish), font, ratio):
        save()
        self._apply_grid_param()
        width = -(finish-start)
        line((0, font.info.ascender*ratio), (width, font.info.ascender*ratio))
        line((0, font.info.descender*ratio), (width, font.info.descender*ratio))
        line((0, font.info.xHeight*ratio), (width, font.info.xHeight*ratio))
        line((0, font.info.capHeight*ratio), (width, font.info.capHeight*ratio))
        restore()
        

    def _draw_spacer(self, width, font, ratio):
        save()
        self._apply_grid_param()
        strokeWidth(.1)
        rect(0, font.info.descender*ratio, width, font.info.unitsPerEm*ratio)
        line((0, 0), (width, font.info.ascender*ratio))
        line((0, font.info.ascender*ratio), (width, 0))
        restore()
    

    def _draw_kern(self, width, font, ratio):
        save()
        self._apply_kern_param()
        rect(0, font.info.descender*ratio, width, font.info.unitsPerEm*ratio)
        textBox("%s" %int(width/ratio), (width/2-3, font.info.descender*ratio+(font.info.unitsPerEm*ratio-self.line_space)/2-2, 6, 4), align="center")
        restore()
        

    def _draw_grid_sidebarings(self, width, font, ratio):
        save()
        self._apply_grid_param()
        strokeWidth(.1)
        rect(0, font.info.descender*ratio, width, font.info.unitsPerEm*ratio)
        restore()
    
    # drawing params
    
    def _apply_grid_param(self):
        stroke(*self.grid_stroke)
        strokeWidth(self.grid_strokeWidth)
        fill(None)
        
    def _apply_kern_param(self):
        stroke(None)
        fill(*self.kern_fill)
        font(self.kern_caption_font)
        fontSize(self.kern_caption_fontSize)
            

#----------
# representation
#----------

# set up the required defcon representation factory

from defcon import addRepresentationFactory

def NSBezierPathFactory(glyph, f):
    from fontTools.pens.cocoaPen import CocoaPen
    pen = CocoaPen(f)
    glyph.draw(pen)
    return pen.path
    
    
def BezierPathFactory(glyph, f):
    from fontTools.pens.cocoaPen import CocoaPen
    pen = CocoaPen(f)
    glyph.draw(pen)
    p = pen.path
    path = BezierPath()
    path.setNSBezierPath(p)
    return path
    
    
addRepresentationFactory("DBComposer_NSBezierPath", NSBezierPathFactory)
addRepresentationFactory("DBComposer_BezierPath", BezierPathFactory)


#----------
# Kern Parser
#----------

"""
should be its own module
"""
GROUPPREFIX = "@"



class KernParser(object):
    """
    Parse kerning groups from the acutal kerning data (not the ufo groups) from a given font
    Return a custom KernPair object.
    """
    
    def __init__(self, font):
        self.font = font
        self.kern = self.font.kerning
        self.groups_1st, self.groups_2nd = self.extract_kerning_groups()
        self.groups_1st_reversed = self.reverse_kern_groups(self.groups_1st)
        self.groups_2nd_reversed = self.reverse_kern_groups(self.groups_2nd)


    # data collectors
    
    def extract_kerning_groups(self, prefix=GROUPPREFIX):
        """ 
        parse the kerning data looking for groups,
        return a list for each side
        """
        groups_1st = []
        groups_2nd = []
        for key_1st, key_2nd in self.kern.keys():
            if key_1st.startswith(prefix):
                groups_1st.append(key_1st)
            if key_2nd.startswith(prefix):
                groups_2nd.append(key_2nd)
            
        groups_1st = set(groups_1st)
        groups_1st = list(groups_1st)
        groups_1st.sort()
    
        groups_2nd = set(groups_2nd)
        groups_2nd = list(groups_2nd)
        groups_2nd.sort()

        return groups_1st, groups_2nd
   
    
    def reverse_kern_groups(self, groups_list):
        """
        Return a dict of glyphs a key and group as values,
        expect a single sided group list,
        will raise an error if a glyph is present in more than one group
        """
        reverse_dict = {}
        for key in groups_list:
            try:
                for g in self.font.groups[key]:
                  if g in reverse_dict:
                      raise ValueError("glyph in several classes")
                  reverse_dict[g] = key  
            except KeyError:
                print "WARNING - %s is present in the kerning table but cannot be found in you font's groups" %(key)
            except ValueError:
                print "WARNING - %s is present in several groups: %s %s" %(g, reverse_dict[g], key)
        return reverse_dict
   

    # kern pair extractors
            
    def get_kerning_pair(self, (a, b)):

        # get relevant glyph or class
        if a in self.groups_1st_reversed:
            target_1st = [self.groups_1st_reversed[a], a]
        else:
            target_1st = [a]
   
        if b in self.groups_2nd_reversed:
            target_2nd = [self.groups_2nd_reversed[b], b]
        else:
            target_2nd = [b] 
        
        # default output for non existing pair
        out = KernPair(a, b, target_1st[0], target_2nd[0], None)
        # get the data
        for t1 in target_1st:
            for t2 in target_2nd:
                if (t1, t2) in self.kern:
                    out = KernPair(a, b, t1, t2, self.kern[t1, t2])
        return out


    def get_kerning_pair_value(self, (a, b)):
        pair = self.get_kerning_pair((a,b))
        return pair.value
        

    def get_kerning_pair_list(self, pairlist):
        out = []
        for p in pairlist:
            out.append(self.get_kerning_pair(p))
        return out
        

    def print_kerning_pair_list(self, pairlist):
        for p in self.get_kerning_pair_list(pairlist):
            print p
        
        
class KernPair(object):
    """
    A custom kerning pair object (mostly for repr purposes)
    containing the actual pair, the kerning value and the 2 relevant masters
    """
    def __init__(self, glyph_1st, glyph_2nd, relevant_1st, relevant_2nd, value):
        self.value = value
        self.glyph_1st = glyph_1st
        self.glyph_2nd = glyph_2nd
        self.relevant_1st = relevant_1st
        self.relevant_2nd = relevant_2nd
    
    def __repr__(self):
        return "/%s /%s: %s\t[%s %s]" %(self.glyph_1st, self.glyph_2nd, self.value, self.relevant_1st, self.relevant_2nd)
        