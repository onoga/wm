# GNU Enterprise Forms - GF Object Hierarchy - Box
#
# Copyright 2001-2007 Free Software Foundation
#
# This file is part of GNU Enterprise
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# GNU Enterprise is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#
# $Id: GFTreeColumn.py,v 1.5 2008/11/10 17:21:57 oleg Exp $
"""
TreeNodeStyle
"""

from GFObj import GFObj

__all__ = ['GFTreeColumn']

# =============================================================================
# <TreeNodeStyle>
# =============================================================================

class GFTreeColumn(GFObj):

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		GFObj.__init__(self, parent, "GFTreeColumn")

		self.icon      = None
		self.icon_off  = None
		self.icon_description = None
		self.icon_off_description = None

	# -------------------------------------------------------------------------
	# Initialisation
	# -------------------------------------------------------------------------

	def _phase_1_init_(self):
		GFObj._phase_1_init_(self)
