# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
The Quick Insert panel spanners Tool.
"""

from __future__ import unicode_literals

import app
import cursortools
import tokeniter
import music
import symbols

from . import tool
from . import buttongroup


class Spanners(tool.Tool):
    """Dynamics tool in the quick insert panel toolbox."""
    def __init__(self, panel):
        super(Spanners, self).__init__(panel)
        self.layout().addWidget(ArpeggioGroup(self))
        self.layout().addWidget(GlissandoGroup(self))
        self.layout().addWidget(SpannerGroup(self))
        self.layout().addStretch(1)

    def icon(self):
        """Should return an icon for our tab."""
        return symbols.icon("spanner_phrasingslur")
    
    def title(self):
        """Should return a title for our tab."""
        return _("Spanners")
  
    def tooltip(self):
        """Returns a tooltip"""
        return _("Slurs, spanners, etcetera.")


class ArpeggioGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Arpeggios"))
    
    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None
    
    def actionTexts(self):
        """Should yield name, text for very action."""
        yield 'arpeggio_normal', _("Arpeggio")
        yield 'arpeggio_arrow_up', _("Arpeggio with Up Arrow")
        yield 'arpeggio_arrow_down', _("Arpeggio with Down Arrow")
        yield 'arpeggio_bracket', _("Bracket Arpeggio")
        yield 'arpeggio_parenthesis', _("Parenthesis Arpeggio")
        
    def actionTriggered(self, name):
        # convert arpeggio_normal to arpeggioNormal, etc.
        name = _arpeggioTypes[name]
        cursor = self.mainwindow().textCursor()
        # which arpeggio type is last used?
        lastused = '\\arpeggioNormal'
        types = set(_arpeggioTypes.values())
        block = cursor.block()
        while block.isValid():
            s = types.intersection(tokeniter.tokens(block))
            if s:
                lastused = s.pop()
                break
            block = block.previous()
        # where to insert
        source = tokeniter.Source.from_cursor(cursor, True, -1)
        with cursortools.compress_undo(cursor):
            for p in music.music_items(source, tokens=source.tokens):
                c = source.cursor(p[-1], start=len(p[-1]))
                c.insertText('\\arpeggio')
                if name != lastused:
                    cursortools.strip_indent(c)
                    import indent
                    indent.insert_text(c, name + '\n')
                # just pick the first place
                return
        

class GlissandoGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Glissandos"))
    
    def actionData(self):
        """Should yield name, icon, function (may be None) for every action."""
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None
    
    def actionTexts(self):
        """Should yield name, text for very action."""
        yield 'glissando_normal', _("Glissando")
        yield 'glissando_dashed', _("Dashed Glissando")
        yield 'glissando_dotted', _("Dotted Glissando")
        yield 'glissando_zigzag', _("Zigzag Glissando")
        yield 'glissando_trill', _("Trill Glissando")

    def actionTriggered(self, name):
        cursor = self.mainwindow().textCursor()
        style = _glissandoStyles[name]
        source = tokeniter.Source.from_cursor(cursor, True, -1)
        for p in music.music_items(source, tokens=source.tokens):
            c = source.cursor(p[-1], start=len(p[-1]))
            if style:
                text = "-\\tweak #'style #'{0} \\glissando".format(style)
            else:
                text = '\\glissando'
            c.insertText(text)
            return


class SpannerGroup(buttongroup.ButtonGroup):
    def translateUI(self):
        self.setTitle(_("Spanners"))
    
    def actionData(self):
        for name, title in self.actionTexts():
            yield name, symbols.icon(name), None

    def actionTexts(self):
        yield 'spanner_slur', _("Slur")
        yield 'spanner_phrasingslur', _("Phrasing Slur")
        yield 'spanner_beam16', _("Beam")
        yield 'spanner_trill', _("Trill")

    def actionTriggered(self, name):
        d = ['_', '', '^'][self.direction()+1]
        if name == "spanner_slur":
            spanner = d + '(', ')'
        elif name == "spanner_phrasingslur":
            spanner = d + '\\(', '\\)'
        elif name == "spanner_beam16":
            spanner = d + '[', ']'
        elif name == "spanner_trill":
            spanner = '\\startTrillSpan', '\\stopTrillSpan'

        cursor = self.mainwindow().textCursor()
        with cursortools.compress_undo(cursor):
            for s, c in zip(spanner, spanner_positions(cursor)):
                c.insertText(s)


def spanner_positions(cursor):
    if cursor.hasSelection():
        source = tokeniter.Source.selection(cursor, True)
        tokens = None
    else:
        source = tokeniter.Source.from_cursor(cursor, True, -1)
        tokens = source.tokens # only current line
    
    positions = [source.cursor(p[-1], start=len(p[-1]))
        for p in music.music_items(source, tokens=tokens)]
    
    if cursor.hasSelection():
        del positions[1:-1]
    else:
        del positions[2:]
    return positions



_arpeggioTypes = {
    'arpeggio_normal': '\\arpeggioNormal',
    'arpeggio_arrow_up': '\\arpeggioArrowUp',
    'arpeggio_arrow_down': '\\arpeggioArrowDown',
    'arpeggio_bracket': '\\arpeggioBracket',
    'arpeggio_parenthesis': '\\arpeggioParenthesis',
}

_glissandoStyles = {
    'glissando_normal': '',
    'glissando_dashed': 'dashed-line',
    'glissando_dotted': 'dotted-line',
    'glissando_zigzag': 'zigzag',
    'glissando_trill':  'trill',
}

