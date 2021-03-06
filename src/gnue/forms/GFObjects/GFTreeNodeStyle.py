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
# $Id: GFTreeNodeStyle.py,v 1.7 2008/12/12 14:12:13 oleg Exp $
"""
TreeNodeStyle
"""

from GFStyle import GFStyle

__all__ = ['GFTreeNodeStyle']

# =============================================================================
# <TreeNodeStyle>
# =============================================================================

class GFTreeNodeStyle(GFStyle):

	# -------------------------------------------------------------------------
	# Constructor
	# -------------------------------------------------------------------------

	def __init__(self, parent=None):
		GFStyle.__init__(self, parent)

		self.icon      = None
		self.button    = None
		self.bold      = False
		self.italic    = False
		self.checked   = False
		self.expanded  = False
		self.textcolor = None
		self.bgcolor   = None

	def merge(self, i, *args, **kwargs):
		flags1 = self.flags
		flags2 = i.flags
		super(GFTreeNodeStyle, self).merge(i, *args, **kwargs)
		self.flags = flags1 + flags2
