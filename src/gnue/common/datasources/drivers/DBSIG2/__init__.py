# GNU Enterprise Common Library - Generic DBSIG2 database driver
#
# Copyright 2000-2007 Free Software Foundation
#
# This file is part of GNU Enterprise.
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
# $Id: __init__.py 9222 2007-01-08 13:02:49Z johannes $

"""
Generic Database driver plugin for SQL based backends using a DBSIG2 compatible
Python module.
"""

__noplugin__ = True


# =============================================================================
# Driver info
# =============================================================================

class DriverInfo:
	name = "SQL based backends"


from Behavior import *
from ResultSet import *
from Connection import *
