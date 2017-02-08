#----------
# imports
#----------

from drawBot import *
from defcon.tools.notifications import NotificationCenter



#----------
# object
#----------

translate_notification_name = "DrawBotComposer.didTranslate"
overflow_width_notification_name = "DrawBotComposer.didOverflowWidth"
overflow_height_notification_name = "DrawBotComposer.didOverflowHeight"
overflow_notification_name = "DrawBotComposer.didOverflow"



class DrawBotComposer(object):
    """
    Record its own position change (translate)
    Can go back to its origin
    Can send a notification when its optional height or width limits are reached.
    When set to None width and height are limitless
    """
    def __init__(self, width=None, height=None):
        self.current_position_x = 0
        self.current_position_y = 0
        self.width = width
        self.height = height
        self.dispatcher = NotificationCenter()

    def set_size(self, width, height):
        self.width = width
        self.height = height

    def reset(self):
        self.current_position_x = 0
        self.current_position_y = 0

    def translate(self, x, y):
        translate(x,y)
        self.current_position_x += x
        self.current_position_y += y
        # notification
        data = {"value":(x,y)}
        self.dispatcher.postNotification(notification=translate_notification_name, observable=self, data=data)
        self._test_overflow(self.current_position_x, self.current_position_y)

    def bump_translate(self, x, y):
        """test overflow without doing the acutal translation"""
        bump_x = self.current_position_x + x
        bump_y = self.current_position_y + y
        self._test_overflow(bump_y, bump_y)
    
    # Back to origin

    def translate_back_to_origin(self):
        translate(-self.current_position_x, -self.current_position_y)
        self.current_position_x = 0
        self.current_position_y = 0

    def translate_back_to_origin_x(self):
        translate(-self.current_position_x, 0)
        self.current_position_x = 0

    def translate_back_to_origin_y(self):
        translate(0, -self.current_position_y)
        self.current_position_y = 0

    # Overflow notification

    def _test_overflow(self, x, y):
        if self.width == None:
            overflow_width = 0
        else:
            overflow_width = self._test_overflow_width(x)
        if self.height == None:
            overflow_height = 0
        else:
            overflow_height = self._test_overflow_height(y)
        if overflow_width != 0 or overflow_height != 0:
            data = {"overflow":(overflow_width, overflow_height)}
            self.dispatcher.postNotification(notification=overflow_notification_name, observable=self, data=data)
        return (overflow_width, overflow_height)
    
    def _test_overflow_width(self, x):
         overflow = self._test_limit(x, self.width)
         if overflow != 0:
            data = {"overflow_width":overflow}
            self.dispatcher.postNotification(notification=overflow_width_notification_name, observable=self, data=data)
         return overflow

    def _test_overflow_height(self, y):
        overflow = self._test_limit(y, self.height)
        if overflow != 0:
           data = {"overflow_height":overflow}
           self.dispatcher.postNotification(notification=overflow_height_notification_name, observable=self, data=data)
        return overflow
            

    def _test_limit(self, value, limit):
        _min = min(0, limit)
        _max = max(0, limit)
        if limit == None:
            return 0
        if _min <= value <= _max:
            return 0
        elif value < _min:
            return value - _min
        elif value > _max:
            return value - _max

    # Observer management

    def addObserver(self, observer, methodName, notification):
        self.dispatcher.addObserver(observer=observer, methodName=methodName, notification=notification, observable=self)

#----------
# various helpers
#----------


def set_formattedString_from_glyph_list(glyph_name_list, font_name, pt_size):
        t = FormattedString()
        t.font(font_name)
        t.fontSize(pt_size)
        slug = tuple(glyph_name_list)
        t.appendGlyph(*slug)
        text(t, (0, 0))


def set_slug_from_ufo(glyph_name_list, font, pt_size, kernParser=None):
    """
    Set a line of text (a glyph name list) in a UFO font
    Translate back to the origin of the line
    For performance issue, the glyph are assumed to be in the font,
    this wont be tested.
    An optional kernparser object can be provided for kerning support
    (I dont like this dependancy here...)
    """
    ratio = pt_size/1000.0
    scale(ratio)
    composer = DrawBotComposer()
    previous_glyph = None
    for n in glyph_name_list:
        if kernParser != None:
            if previous_glyph != None:
                p = kernParser.get_kerning_pair((previous_glyph, n))
                if p.value == None:
                    k = 0
                else:
                    k = p.value
                composer.translate(k, 0)
        g = font[n]
        drawGlyph(g)
        composer.translate(g.width, 0)
        previous_glyph = n
    composer.translate_back_to_origin()
    scale(1/ratio)



def set_slug_list_from_ufo(slug_list, font, pt_size, line_height, kernparser=None, align="capHeight"):
    """
    set a list of slug as a paragraph
    """
    composer = DrawBotComposer()
    offset = get_vertical_alignment_offset(font, pt_size, align=align)
    composer.translate(*offset)
    for slug in slug_list:
        set_slug_from_ufo(slug, font, pt_size, kernParser=kernParser)
        composer.translate(0, -line_height)


def get_vertical_alignment_offset(font, pt_size, align="capHeight"):
    """
    return the offset required for vertical alignment as a tupple  
    The following values can be set for the align argument:
    "capHeight", "ascender", "xHeight", "decsender"
    any other will trigger baseline alignment
    """
    if align in ["capHeight", "ascender", "xHeight", "decsender"]:
        a = getattr(font.info, align)
        a = -a*pt_size/1000
        return a
    else:
        return 0


def go_to_top():
    """move the origin to the top of the page"""
    translate(0, height())
