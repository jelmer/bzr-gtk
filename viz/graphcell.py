#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""Cell renderer for directed graph.

This module contains the implementation of a custom GtkCellRenderer that
draws part of the directed graph based on the lines suggested by the code
in graph.py.

Because we're shiny, we use Cairo to do this, and because we're naughty
we cheat and draw over the bits of the TreeViewColumn that are supposed to
just be for the background.
"""

__copyright__ = "Copyright © 2005 Canonical Ltd."
__author__    = "Scott James Remnant <scott@ubuntu.com>"


import math

import gtk
import gobject
import pango
import cairo


class CellRendererGraph(gtk.GenericCellRenderer):
    """Cell renderer for directed graph.

    Properties:
      node              (column, colour) tuple to draw revision node,
      in_lines          (start, end, colour) tuple list to draw inward lines,
      out_lines         (start, end, colour) tuple list to draw outward lines.
    """

    __gproperties__ = {
        "node":         ( gobject.TYPE_PYOBJECT, "node",
                          "revision node instruction",
                          gobject.PARAM_WRITABLE
                        ),
        "in-lines":     ( gobject.TYPE_PYOBJECT, "in-lines",
                          "instructions to draw lines into the cell",
                          gobject.PARAM_WRITABLE
                        ),
        "out-lines":    ( gobject.TYPE_PYOBJECT, "out-lines",
                          "instructions to draw lines out of the cell",
                          gobject.PARAM_WRITABLE
                        ),
        }

    def do_set_property(self, property, value):
        """Set properties from GObject properties."""
        if property.name == "node":
            self.node = value
        elif property.name == "in-lines":
            self.in_lines = value
        elif property.name == "out-lines":
            self.out_lines = value
        else:
            raise AttributeError, "no such property: '%s'" % property.name

    def box_size(self, widget):
        """Calculate box size based on widget's font.

        Cache this as it's probably expensive to get.  It ensures that we
        draw the graph at least as large as the text.
        """
        try:
            return self._box_size
        except AttributeError:
            pango_ctx = widget.get_pango_context()
            font_desc = widget.get_style().font_desc
            metrics = pango_ctx.get_metrics(font_desc)

            ascent = pango.PIXELS(metrics.get_ascent())
            descent = pango.PIXELS(metrics.get_descent())

            self._box_size = ascent + descent + 6
            return self._box_size

    def set_colour(self, ctx, colour, bg, fg):
        """Set the context source colour.

        Picks a distinct colour based on an internal wheel; the bg
        parameter provides the value that should be assigned to the 'zero'
        colours and the fg parameter provides the multiplier that should be
        applied to the foreground colours.
        """
        colours = [
            ( 1.0, 0.0, 0.0 ),
            ( 1.0, 1.0, 0.0 ),
            ( 0.0, 1.0, 0.0 ),
            ( 0.0, 1.0, 1.0 ),
            ( 0.0, 0.0, 1.0 ),
            ( 1.0, 0.0, 1.0 ),
            ]

        colour %= len(colours)
        red   = (colours[colour][0] * fg) or bg
        green = (colours[colour][1] * fg) or bg
        blue  = (colours[colour][2] * fg) or bg

        ctx.set_source_rgb(red, green, blue)

    def on_get_size(self, widget, cell_area):
        """Return the size we need for this cell.

        Each cell is drawn individually and is only as wide as it needs
        to be, we let the TreeViewColumn take care of making them all
        line up.
        """
        box_size = self.box_size(widget)

        cols = self.node[0]
        for start, end, colour in self.in_lines + self.out_lines:
            cols = max(cols, start, end)

        width = box_size * (cols + 1)
        height = box_size

        # FIXME I have no idea how to use cell_area properly
        return (0, 0, width, height)

    def on_render(self, window, widget, bg_area, cell_area, exp_area, flags):
        """Render an individual cell.

        Draws the cell contents using cairo, taking care to clip what we
        do to within the background area so we don't draw over other cells.
        Note that we're a bit naughty there and should really be drawing
        in the cell_area (or even the exposed area), but we explicitly don't
        want any gutter.

        We try and be a little clever, if the line we need to draw is going
        to cross other columns we actually draw it as in the .---' style
        instead of a pure diagonal ... this reduces confusion by an
        incredible amount.
        """
        ctx = window.cairo_create()
        ctx.rectangle(bg_area.x, bg_area.y, bg_area.width, bg_area.height)
        ctx.clip()

        box_size = self.box_size(widget)

        ctx.set_line_width(box_size / 8)
        ctx.set_line_cap(cairo.LINE_CAP_SQUARE)

        # Draw lines into the cell
        for start, end, colour in self.in_lines:
            ctx.move_to(cell_area.x + box_size * start + box_size / 2,
                        bg_area.y - bg_area.height / 2)

            if start - end > 1:
                ctx.line_to(cell_area.x + box_size * start, bg_area.y)
                ctx.line_to(cell_area.x + box_size * end + box_size, bg_area.y)
            elif start - end < -1:
                ctx.line_to(cell_area.x + box_size * start + box_size,
                            bg_area.y)
                ctx.line_to(cell_area.x + box_size * end, bg_area.y)

            ctx.line_to(cell_area.x + box_size * end + box_size / 2,
                        bg_area.y + bg_area.height / 2)

            self.set_colour(ctx, colour, 0.0, 0.65)
            ctx.stroke()

        # Draw lines out of the cell
        for start, end, colour in self.out_lines:
            ctx.move_to(cell_area.x + box_size * start + box_size / 2,
                        bg_area.y + bg_area.height / 2)

            if start - end > 1:
                ctx.line_to(cell_area.x + box_size * start,
                            bg_area.y + bg_area.height)
                ctx.line_to(cell_area.x + box_size * end + box_size,
                            bg_area.y + bg_area.height)
            elif start - end < -1:
                ctx.line_to(cell_area.x + box_size * start + box_size,
                            bg_area.y + bg_area.height)
                ctx.line_to(cell_area.x + box_size * end,
                            bg_area.y + bg_area.height)

            ctx.line_to(cell_area.x + box_size * end + box_size / 2,
                        bg_area.y + bg_area.height / 2 + bg_area.height)

            self.set_colour(ctx, colour, 0.0, 0.65)
            ctx.stroke()

        # Draw the revision node in the right column
        (column, colour) = self.node
        ctx.arc(cell_area.x + box_size * column + box_size / 2,
                cell_area.y + cell_area.height / 2,
                box_size / 4, 0, 2 * math.pi)

        self.set_colour(ctx, colour, 0.0, 0.5)
        ctx.stroke_preserve()

        self.set_colour(ctx, colour, 0.5, 1.0)
        ctx.fill()