# Copyright (C) 2005 Dan Loda <danloda@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


class ColorMap:

    really_old_color = "#0046FF"

    colors =  {
        20.: "#FFCC00",
        40.: "#FF6666",
        60.: "#FF6600",
        80.: "#FF3300",
        100.: "#FF00FF",
        120.: "#FF0000",
        140.: "#CCCC00",
        160.: "#CC00CC",
        180.: "#BC8F8F",
        200.: "#99CC00",
        220.: "#999900",
        240.: "#7AC5CD",
        260.: "#66CC00",
        280.: "#33CC33",
        300.: "#00CCFF",
        320.: "#00CC99",
        340.: "#0099FF"
    }

    def __init__(self, span=340.):
        self.set_span(span)

    def set_span(self, span):
        self._span = span
        self._scale = span / max(self.colors.keys())

    def get_color(self, days_old):
        color = self.really_old_color
        days = self.colors.keys()
        days.sort()
        
        for day in days:
            if (days_old <= day * self._scale):
                color = self.colors[day]
                break

        return color


class GrannyColorMap(ColorMap):

    colors = {
        20.: "#FF0000",
        40.: "#FF3800",
        60.: "#FF7000",
        80.: "#FFA800",
        100.:"#FFE000",
        120.:"#E7FF00",
        140.:"#AFFF00",
        160.:"#77FF00",
        180.:"#3FFF00",
        200.:"#07FF00",
        220.:"#00FF31",
        240.:"#00FF69",
        260.:"#00FFA1",
        280.:"#00FFD9",
        300.:"#00EEFF",
        320.:"#00B6FF",
        340.:"#007EFF"
    }

