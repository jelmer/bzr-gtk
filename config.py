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

"""Configuration options."""

from bzrlib import (
    config,
    version_info as bzrlib_version,
    )

if bzrlib_version < (2, 5):
    def Option(*args, **kwargs):
        if 'help' in kwargs:
            del kwargs['help']
        return config.Option(*args, **kwargs)
else:
    Option = config.Option

opt_nautilus_integration = Option('nautilus_integration', default=True,
               from_unicode=config.bool_from_store,
               help='''\
Whether to enable nautilus integration.

Defines whether Nautilus integration should be enabled.
''')
