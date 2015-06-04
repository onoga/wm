# GNU Enterprise Forms - wx 2.6 UI Driver - Toolbar widget
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
# $Id: toolbar.py,v 1.2 2009/07/27 20:17:14 oleg Exp $

from _base import UIWidget
from _remote import ToolBar

# =============================================================================
# Wrap an UI layer around a wxMenu widget
# =============================================================================

class UIToolbar(UIWidget):
	"""
	Implements a toolbar object.
	"""

	def __init__(self, event):
		UIWidget.__init__(self, event)

	# -------------------------------------------------------------------------
	# Create a menu widget
	# -------------------------------------------------------------------------

	def _create_widget_(self, event):
		"""
		Creates a new toolbar widget.
		"""

		if self._gfObject.name == '__main_toolbar__' and not self._form._features['GUI:TOOLBAR:SUPPRESS']:
			# Toolbar of the form
			self._uiForm.toolBar = self._container = self.widget = ToolBar(self)




# =============================================================================
# Configuration data
# =============================================================================

configuration = {
	'baseClass': UIToolbar,
	'provides' : 'GFToolbar',
	'container': 1,
}
