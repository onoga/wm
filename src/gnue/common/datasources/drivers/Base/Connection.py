# GNU Enterprise Common Library - Base database driver - Connection
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
# $Id: Connection.py 9551 2007-05-05 18:28:31Z johannes $

"""
Generic Connection class extended by all database driver plugins.
"""

__all__ = ['Connection']

from gnue.common.apps import GDebug, plugin
from gnue.common.datasources import GConnections, GSchema


# =============================================================================
# Basic connection class
# =============================================================================

class Connection(object):
	"""
	Generic database connection class.

	This class must be subclassed by all database drivers. It represents a
	connection to the backend.

	The Connection class offers three basic function group:
	  - Connecting to, authenticating at and disconnecting from the backend.
	  - Inserting, modifying and deleting records in the backend using a
	    dictionary with old field values to select the records to operate on as
	    well as committing and rolling back changes.
	  - Creating the actual database in the backend and creating as well as
	    introspecting the database schema. This is done using an assigned
	    L{Behavior.Behavior} class.

	All operations on the backend go through the connection object.

	@cvar _resultSetClass_: implementation of the ResultSet class to be used with
	  the connection.  Must be overwritten by descendants.
	@cvar _behavior_: Schema introspector class for this type of connection. If a
	  descendants overwrites this, the behavior cannot be set in
	  connections.conf.
	@cvar _defaultBehavior_: Standard schema introspector class for this type of
	  connection.  Can be overwritten by descendants to provide a default in case
	  the behavior can be set in connections.conf.
	@cvar _rowidField_: Field name of the rowid generated by the backend.  Can be
	  overwritten by descendants if the backend supports rowids.
	@cvar _primarykeyFields_: Field names of the primary key.  Can be overwritten
	  by descendants if the backend has a fixed fieldname for the primary key.
	@cvar _need_rollback_after_exception_: Can be set to False if the backend
	  does not require to rollback after an exception has happened. Most
	  prominent example of this is the appserver backend.

	@ivar name: Name of the connection from connections.conf.
	@ivar parameters: Parameters from connections.conf.
	@ivar manager: The connection manager (GConnections) instance responsible
	  for this connection.
	"""

	_resultSetClass_                = None
	_behavior_                      = None
	_defaultBehavior_               = None
	_rowidField_                    = None
	_primarykeyFields_              = None
	_need_rollback_after_exception_ = False


	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, connections, name, parameters):
		"""
		Create a new Connection instance.

		Usually, this is achieved via L{GConnections.GConnections.getConnection}.

		@param connections: Connection manager (instance of
		  L{GConnections.GConnections}.
		@param name: Name of the connection.
		@param parameters: Connection parameters from connections.conf.
		"""

		checktype (connections, GConnections.GConnections)
		checktype (name, basestring)
		checktype (parameters, dict)

		self.manager    = connections
		self.name       = name
		self.parameters = parameters

		# True if the connection has uncommitted changes
		self.__pending  = False

		# Find out Behavior class to use

		if self._behavior_ is not None:
			behaviorClass = self._behavior_

		elif self.parameters.get ('behavior') is not None:
			behaviorClass = plugin.find (self.parameters ['behavior'],
				'gnue.common.datasources.drivers', 'Behavior')

		elif self._defaultBehavior_ is not None:
			behaviorClass = self._defaultBehavior_

		else:
			behaviorClass = None

		if behaviorClass is not None:
			self.__behavior = behaviorClass (self)
		else:
			self.__behavior = None


	# ---------------------------------------------------------------------------
	# Nice string representation
	# ---------------------------------------------------------------------------

	def __repr__ (self):

		return "<Connection to %s at %d>" % (self.name, id (self))


	# ---------------------------------------------------------------------------
	# Define fields necessary for login
	# ---------------------------------------------------------------------------

	def getLoginFields (self):
		"""
		Return information about the necessary login parameters for the L{connect}
		method.

		The return value is a list of tuples in the form (label, fieldname,
		fieldtype, defaultvalue, masterfield, [(label, value-dict), ...]).
		The first element of the tuple is the label to display to the user. The
		second element of the tuple is the field name passed as a dictionary key to
		the connect method later. The third element is the fieldtype (label,
		string, password, dropdown, image) and 'defaultvalue' gives a default value
		for the field. The 'masterfield' and element-sequence are used for
		dropdowns, where 'masterfield' specifies a fielddefinition (a tuple like
		this one) defining a master value. The element-sequence holds a list of
		tuples (label, value-dictionary) describing the allowed values (per
		master-field if any).

		A typical return value would be::
		  [(u_('User Name'), '_username', 'string', None, None, []),
		   (u_('Password'), '_password', 'password', None, None, [])]

		@raise errors.AdminError: if the communication with the backend fails.
		"""

		assert gEnter (8)
		result = self._getLoginFields_ ()
		assert gLeave (8, result)
		return result


	# ---------------------------------------------------------------------------
	# Connect to the backend
	# ---------------------------------------------------------------------------

	def connect (self, connectData):
		"""
		Connect to the backend.

		@param connectData: A dictionary with the login fields as requested by
		  L{getLoginFields} and all parameters from connections.conf.
		@raise Exceptions.LoginError: if the authentication failed and can be tried
		  again.
		@raise Exception: if the connection fails. The exact exception class
		  depends on the backend.
		"""

		checktype (connectData, dict)

		assert gEnter (8)
		self._connect_ (connectData)
		self._beginTransaction_ ()
		assert gLeave (8)


	# ---------------------------------------------------------------------------
	# Initialize a new record with default data
	# ---------------------------------------------------------------------------

	def initialize (self, table, fields):
		"""
		Return default values for new records.

		@param table: Table name.
		@param fields: List of field names.
		@return: Dictionary with fieldname/value pairs.
		@raise Exception: if the retrieval of default values from the backend
		  fails. The exact exception class depends on the backend.
		"""

		checktype (table, basestring)
		checktype (fields, list)

		assert gEnter (8)
		result = self._initialize_ (table, fields)
		assert gLeave (8, result)
		return result


	# ---------------------------------------------------------------------------
	# Insert a new record in the backend
	# ---------------------------------------------------------------------------

	def insert (self, table, newfields):
		"""
		Insert a new record in the backend.

		@param table: Table name.
		@param newfields: Fieldname/Value dictionary of data to insert.
		@return: The rowid of the newly inserted record, or None if no rowid's are
		supported.
		@raise Exception: if the insert fails. The exact exception type depends on
		  the backend.
		"""

		checktype (table, basestring)
		checktype (newfields, dict)

		assert gEnter (8)
		rowid = self._insert_ (table, newfields)
		self.__pending = True
		assert gLeave (8, rowid)
		return rowid


	# ---------------------------------------------------------------------------
	# Update an existing record in the backend
	# ---------------------------------------------------------------------------

	def update (self, table, oldfields, newfields):
		"""
		Update an existing record in the backend.

		@param table: Table name.
		@param oldfields: Fieldname/Value dictionary of fields to find the existing
		  record (aka where-clause).
		@param newfields: Fieldname/Value dictionary of data to change.
		@raise Exception: if the update fails. The exact exception type depends on
		  the backend.
		"""

		checktype (table, basestring)
		checktype (oldfields, dict)
		checktype (newfields, dict)

		assert gEnter (8)
		self._update_ (table, oldfields, newfields)
		self.__pending = True
		assert gLeave (8)


	# ---------------------------------------------------------------------------
	# Delete a record from the backend
	# ---------------------------------------------------------------------------

	def delete (self, table, oldfields):
		"""
		Delete a record from the backend.

		@param table: Table name.
		@param oldfields: Fieldname/Value dictionary of fields to find the existing
		  record (aka where-clause).
		@raise Exception: if the deletion fails. The exact exception type depends
		  on the backend.
		"""

		checktype (table, basestring)
		checktype (oldfields, dict)

		assert gEnter (8)
		self._delete_ (table, oldfields)
		self.__pending = True
		assert gLeave (8)


	# ---------------------------------------------------------------------------
	# Requery an existing record to reflect changes done by the backend
	# ---------------------------------------------------------------------------

	def requery (self, table, oldfields, fields, parameters = None):
		"""
		Requery an existing record to reflect changes done by the backend.

		@param table: Table name.
		@param oldfields: Fieldname/Value dictionary of fields to find the existing
		  record (aka where-clause).
		@param fields: List of field names to query.
		@return: Fieldname/Value dictionary with data fresh from the backend.
		@raise Exception: if the requery fails. The exact exception type depends on
		  the backend.
		"""

		checktype (table, basestring)
		checktype (oldfields, dict)
		checktype (fields, list)

		assert gEnter (8)
		result = self._requery_ (table, oldfields, fields, parameters)
		assert gLeave (8, result)
		return result



	# ---------------------------------------------------------------------------
	# Call a backend function
	# ---------------------------------------------------------------------------

	def call (self, table, oldfields, methodname, parameters):
		"""
		Call a function of the backend.

		@param table: Table name.
		@param oldfields: Fieldname/Value dictionary of fields to find the existing
		  record (aka where-clause).
		@param methodname: Name of the function to call.
		@param parameters: parametername/value dictionary.
		@return: Result of the function that was called.
		@raise Exception: if the call fails. The exact exception type depends on
		  the backend.
		"""

		checktype (table, basestring)
		checktype (oldfields, dict)
		checktype (methodname, basestring)
		checktype (parameters, dict)

		assert gEnter (8)
		result = self._call_ (table, oldfields, methodname, parameters)
		# FIXME: Some calls should not make the connection pending, like requesting
		# the generated form. Most others should.
		# self.__pending = True
		assert gLeave (8, result)
		return result


	# ---------------------------------------------------------------------------
	# Check if the connection has posted but not yet committed changes
	# ---------------------------------------------------------------------------

	def isPending (self):
		"""
		Check whether there are changes that have been posted (via L{insert},
		L{update}, or L{delete}) but not yet committed.

		@return: True if there are pending changes.
		"""

		return self.__pending


	# ---------------------------------------------------------------------------
	# Commit pending changes in the backend
	# ---------------------------------------------------------------------------

	def commit (self):
		"""
		Commit pending changes in the backend and start a new transaction.

		@raise Exception: if the commit fails. The exact exception type depends on
		  the backend.
		"""

		assert gEnter (8)
		self._commit_ ()
		self.__pending = False
		self._beginTransaction_ ()
		assert gLeave (8)


	# ---------------------------------------------------------------------------
	# Undo any uncommitted changes in the backend
	# ---------------------------------------------------------------------------

	def rollback (self):
		"""
		Undo any uncommitted changes in the backend and start a new transaction.

		@raise Exception: if the rollback fails. The exact exception type depends
		  on the backend.
		"""

		assert gEnter (8)
		self._rollback_ ()
		self.__pending = False
		self._beginTransaction_ ()
		assert gLeave (8)


	# ---------------------------------------------------------------------------
	# Close the connection to the backend
	# ---------------------------------------------------------------------------

	def close (self):
		"""
		Close the connection to the backend.

		@raise Exception: if the close fails. The exact exception type depends on
		  the backend.
		"""

		assert gEnter (8)
		self._close_ ()
		self.manager._connectionClosed (self)
		assert gLeave (8)


	# ---------------------------------------------------------------------------
	# Create a new database for this connection
	# ---------------------------------------------------------------------------

	def createDatabase (self):
		"""
		Create the database in the backend.
		"""

		if self.__behavior is not None:
			self.__behavior.createDatabase ()


	# ---------------------------------------------------------------------------
	# Write a given schema to the connection's backend
	# ---------------------------------------------------------------------------

	def writeSchema (self, schema, simulate = False):
		"""
		Update the connection's backend database schema with the given schema
		object tree.

		@param schema: L{GSchema} object tree defining the schema to be integrated
		@param simulate: if True, create only the command sequence. No integration
		  takes place.

		@return: command sequence which could be used to integrate the given schema
		"""

		checktype (schema, GSchema.GSSchema)

		commands = []

		if self.__behavior is not None:
			commands = self.__behavior.writeSchema (schema, simulate)

		return commands


	# ---------------------------------------------------------------------------
	# Return the current schema information of the connection's backend
	# ---------------------------------------------------------------------------

	def readSchema (self):
		"""
		Return the schema information of the connection's backend or None if no
		behavior instance is available.

		@return: L{GSchema} object tree with the current schema or None
		"""

		if self.__behavior is not None:
			return self.__behavior.readSchema ()
		else:
			return None


	# ---------------------------------------------------------------------------
	# Virtual methods to be implemented by descendants
	# ---------------------------------------------------------------------------

	def _getLoginFields_ (self):
		"""
		Return information about the necessary login parameters for the L{connect}
		method (to be implemented by descendants).

		Descendants can overwrite this method to return a list of necessary login
		fields as defined in L{getLoginFields}.

		If this method is not overwritten, it returns an empty list.
		"""
		return []

	# ---------------------------------------------------------------------------

	def _connect_ (self, connectData):
		"""
		Connect to the backend (to be implemented by descendants).

		This method can be overwritten by the database drivers to connect to the
		backend.  If it is not overwritten, it does nothing.

		@param connectData: A dictionary with the login fields as requested by
		  getLoginFields and all parameters from connections.conf.
		"""
		pass

	# ---------------------------------------------------------------------------

	def _beginTransaction_ (self):
		"""
		Start a new transaction (to be implemented by descendants).

		Database drivers can overwrite this method that gets called after
		connecting to the database as well as after each commit and rollback.  If
		it is not overwritten, it does nothing.
		"""
		pass

	# ---------------------------------------------------------------------------

	def _initialize_ (self, table, fields):
		"""
		Return default values for new records (can be overwritten by descendants).

		The basic implementation of this method simply returns a dictionary where
		every fieldname is assigned a None value.

		Database drivers can overwrite this method to return default data.
		The appserver driver uses this to get the gnue_id and the result of the
		OnInit procedures for new records.

		@param table: Table name.
		@param fields: List of field names.
		@return: Dictionary with fieldname/value pairs.
		"""
		return dict.fromkeys (fields, None)

	# ---------------------------------------------------------------------------

	def _insert_ (self, table, newfields):
		"""
		Insert a new record in the backend (to be implemented by descendants).

		Database drivers can overwrite this method to send new data records to the
		backend.  If the backend supports rowids, the rowid of the newly inserted
		record must be returned from this method.

		@param table: Table name.
		@param newfields: Fieldname/Value dictionary of data to insert.
		@return: The rowid of the newly inserted record, or None if no rowid's are
		supported.
		"""
		return None

	# ---------------------------------------------------------------------------

	def _update_ (self, table, oldfields, newfields):
		"""
		Update an existing record in the backend.

		Database drivers can overwrite this method to send changes of existing data
		records to the backend (to be implemented by descendants).

		@param table: Table name.
		@param oldfields: Fieldname/Value dictionary of fields to find the existing
		  record (aka where-clause)
		@param newfields: Fieldname/Value dictionary of data to change.
		"""
		pass

	# ---------------------------------------------------------------------------

	def _delete_ (self, table, oldfields):
		"""
		Delete a record from the backend (to be implemented by descendants).

		Database drivers can overwrite this method to send removals of data records
		to the backend.

		@param table: Table name.
		@param oldfields: Fieldname/Value dictionary of fields to find the existing
		  record (aka where-clause)
		"""
		pass

	# ---------------------------------------------------------------------------

	def _requery_ (self, table, oldfields, fields, parameters):
		"""
		Requery an existing record to reflect changes done by the backend (to be
		implemented by descendants).

		This method must be overwritten by descendants to return current data that
		might have changed automatically by the backend (e.g. through database
		triggers or appserver triggers) after an insert or update has been issued.

		@param table: Table name.
		@param oldfields: Fieldname/Value dictionary of fields to find the existing
		  record (aka where-clause).
		@param fields: List of field names to query.
		@return: Fieldname/Value dictionary with data fresh from the backend, or
		  None if no record was found.
		"""
		return {}

	# ---------------------------------------------------------------------------

	def _call_ (self, table, oldfields, methodname, parameters):
		"""
		Call a function of the backend (to be implemented by descendants).

		This method can be overwritten by the database drivers to call a function
		that runs in the backend for a specific record.

		@param table: Table name.
		@param oldfields: Fieldname/Value dictionary of fields to find the existing
		  record (aka where-clause).
		@param methodname: Name of the function to call.
		@param parameters: parametername/value dictionary.
		@return: Result of the function that was called.
		"""
		pass

	# ---------------------------------------------------------------------------

	def _commit_ (self):
		"""
		Commit pending changes in the backend (to be implemented by descendants).

		This method can be overwritten by the database drivers to commit data to
		the backend.  If it is not overwritten, it does nothing.
		"""
		pass

	# ---------------------------------------------------------------------------

	def _rollback_ (self):
		"""
		Undo any uncommitted changes in the backend (to be implemented by
		descendants).

		This can should be overwritten by the database drivers to abort and roll
		back any running transaction.  If it is not overwritten, it does nothing.
		"""
		pass

	# ---------------------------------------------------------------------------

	def _close_ (self):
		"""
		Close the connection to the backend (to be implemented by descendants).

		This method can be overwritten by the database drivers to close the
		connection to the backend.  If it is not overwritten, it does nothing.
		"""
		pass
