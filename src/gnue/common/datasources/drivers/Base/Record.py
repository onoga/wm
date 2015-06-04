# GNU Enterprise Common Library - Base database driver - Record set
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
# $Id: Record.py,v 1.19 2011/12/09 16:02:55 oleg Exp $

"""
Record class used by all database driver plugins.
"""

__all__ = ['Record']

from gnue.common.datasources import Exceptions
import weakref


class ACCESS(object):

	UPDATE = 4
	INSERT = 2
	DELETE = 1
	NONE   = 0
	WRITE  = UPDATE | INSERT
	FULL   = WRITE | DELETE


# =============================================================================
# Basic Record class
# =============================================================================

class Record(object):
	"""
	Representation of a database record.

	A Record instance encapsulates a database record. Field values can be read
	and written, and the Record keeps track of which fields have been changed.
	Read and write access to fields happens as if the Record object was a
	dictionary::
	        print myRecordSet [fieldname]
	        myRecordSet [fieldname] = 'foo'
	        field_dict = myRecordSet.copy ()
	        myRecordSet.update (updateDict)

	The Record object allows deletion of the underlying record from the
	database with L{delete}, and - if used in a 3 tier environment - calling of a
	server side procedure with L{call}.

	A Record keeps track of its own status. The L{isEmpty}, L{isInserted},
	L{isModified}, L{isDeleted}, and L{isPending} functions are available to
	check the current status of the record.

	When the L{_post} method is called, the Record uses the assigned
	L{Connection} object to store the changes in the backend. After L{_post} has
	been called, L{_requery} should be called subsequently to make sure that the
	Record can requery all its field values from the database in case a server
	side trigger has changed any of the fields. The L{_post} and L{_requery}
	methods are separated so a caller can call the Connection's commit method in
	between. Both functions are called by the L{ResultSet} this Record belongs
	to.

	If the Record is the master in a master/detail relationship, it is aware
	of all its details. It notifies all its detail L{GDataSource.GDataSource}
	objects whenever it becomes the current record, and it posts/requeries all
	detail L{ResultSet} objects after posting/requerying its own data.

	If the Record is the detail in a master/detail relationship, it is not
	aware of the master. It is the full responsibility of the master to keep its
	details in sync.
	"""

	# ---------------------------------------------------------------------------
	# Constructor
	# ---------------------------------------------------------------------------

	def __init__ (self, resultSet,
		initialData      = {},
		defaultData      = {},
		connection       = None,
		tablename        = '',
		rowidField       = None,
		primarykeyFields = [],
		primarykeySeq    = None,
		boundFields      = [],
		requery          = True,
		access           = ACCESS.FULL,
		details          = {},
		eventController  = None):
		"""
		Create a new Record instance.

		@param initialData: Dictionary with the record's data if it's an existing
		        record. Keys of the dictionary are field names.
		@param defaultData: Dictionary with default data to be used if it is a new
		        record (i.e. initialData is an empty dictionary).
		@param connection: GConnection object the Record object can use to post
		        changes.
		@param tablename: Table name.
		@param rowidField: Field name of the field containing a unique row id
		        generated by the backend, if available.
		@param primarykeyFields: List of field names that make up a unique key, if
		        available.
		@param primarykeySeq: If this is set to the name of a backend sequence,
		        the Record calls the getSequence method of the Connection object to
		        fill the primarykeyField before posting a new record to the backend.  If
		        primarykeySeq is given, the primarykeyFields may only contain a single
		        field name.
		@param boundFields: List of fields to be included when posting changes to
		        the backend. All fields not in this list are considered unbound fields
		        and are not persistent.
		@param requery: If this is set to True, the Record reqeries its values
		        from the backend after posting, in case a backend trigger has changed
		        something. This happens in the L{_requery} method that has to be called
		        after L{_post}.
		@param access: True if the Record is read only. If set, an attempt to
		        modify or delete this record raises an exception.
		@param details: Dictionary defining all details of this ResultSet, where
		        the key is the @L{GDataSource.GDataSource} object and the values are
		        tuples containing a list of primary key fields and a list of the
		        corresponding foreign key fields.
		@param eventController: EventController instance to notify of data events.
		"""

		# weakref for better garbage collection
		self.__resultSet        = weakref.proxy(resultSet)

		self.__connection       = connection
		self.__tablename        = tablename
		self.__rowidField       = rowidField
		self.__primarykeyFields = primarykeyFields
		self.__primarykeySeq    = primarykeySeq
		self.__boundFields      = boundFields
		self.__requery          = requery
		self.__access           = access
		self.__details          = details
		self.__eventController  = eventController

		# Record status
		self.__inserted = False             # True = new record, False = existing
		self.__modified = False             # True = dirty, False = clean
		self.__deleted = False              # True = deleted, False = still alive

		# If field name is present as a key, then field has been modified
		self.__modifiedFields = None         # lazy set()

		# The detail ResultSets where this record is the master
		self.__cachedDetailResultSets = None # lazy {}

		# All field names that are used to link detail records (i.e. all fieldnames
		# that appear as masterfield in any of my detail result sets)
		self.__detailLinkFlags = None        # lazy {}
		for (dataSource, (pkFields, fkFields)) in self.__details.items ():
			for fieldname in pkFields:
				if self.__detailLinkFlags is None:
					self.__detailLinkFlags = {}
				self.__detailLinkFlags [fieldname] = True

		# Dictionary with field:value pairs of initial data. This dictionary always
		# represents the committed state of the backend.
		self.__initialData = initialData.copy ()     # don't touch the parameter!

		# Requery status:
		# None = no requery necessary
		# 'posted' = record has been posted, requery necessary
		# 'commit' = record has been requeried after the last post but needs to be
		#            requeried again after the following commit
		self.__requeryStatus = None

		# While this is true, changes don't mark the record as dirty.
		self.__initializing = True

		if self.__initialData:

			# Existing record:
			# Set the current state of all fields as given in the parameter
			self.__fields = self.__initialData
			# memory optimization: no need to copy if resultSet not editable
			if self.__access & ACCESS.WRITE:
				self.__fields = self.__fields.copy()

			self.__dispatchEvent ('dsRecordLoaded')

		else:

			# New record:
			# 1. mark as new
			self.__inserted = True

			# 2. Get the default values from the backend
			if self.__connection:
				self.__fields = self.__connection.initialize(self.__tablename, self.__boundFields)
			else:
				self.__fields = dict.fromkeys(self.__boundFields, None)

			self.__initialData = self.__fields
			# memory optimization: no need to copy if resultSet not editable
			if self.__access & ACCESS.WRITE:
				self.__initialData = self.__initialData.copy()

			# 3. Set the primary key fields to dirty, so they will be included in the
			#    insert statement in any case.
			for fieldname in self.__primarykeyFields:
				if self.__modifiedFields is None:
					self.__modifiedFields = set()
				self.__modifiedFields.add(fieldname)

			# 4. Get default values from DataSource (includes link to master).
			for (fieldname, value) in defaultData.items ():
				self [fieldname] = value

			# 5. Notify event listener about new record
			self.__dispatchEvent ('dsRecordInserted')

		self.__initializing = False

	# ---------------------------------------------------------------------------
	# String representation
	# ---------------------------------------------------------------------------

	def __repr__ (self):
		"""
		Show a string representation of the Record.
		"""

		if self.__tablename:
			return "<Record for %s at %d>" % (self.__tablename, id (self))
		else:
			return "<Unbound/Static Record at %d>" % id (self)


	# ---------------------------------------------------------------------------
	# Dictionary emulation
	# ---------------------------------------------------------------------------

	def __getitem__ (self, fieldname):
		"""
		Return the current value of a field, so the Record can be used like a
		dictionary.

		@param fieldname: Field name.
		@return: Field value.
		"""
		# FIXME: Does it really make sense to return None for undefined field
		# names?
		return self.__fields.get(fieldname)

	# ---------------------------------------------------------------------------

	def __setitem__ (self, fieldname, value):
		"""
		Set a new value for a field, so the Record can be used like a
		dictionary.

		@param fieldname: Field name.
		@param value: Value to set.
		@raise L{Exceptions.ReadOnlyModifyError}: if the Record is read only.
		"""
		# TODO: better access checks
		#if fieldname in self.__boundFields and not self.__access & ACCESS.WRITE:
		#	raise Exceptions.ReadOnlyModifyError

		# Don't touch the field if nothing has changed. This prevents a recordset
		# from getting dirty even no value is changing
		if (fieldname in self.__fields) and (self.__fields [fieldname] == value):
			return

		#rint "+ field %s value changed: %s (%s) -> %s (%s)" % (fieldname, self.__fields.get(fieldname), type(self.__fields.get(fieldname)), value, type(value))

		self.__fields [fieldname] = value

		if self.__modifiedFields is None:
			self.__modifiedFields = set()
		self.__modifiedFields.add(fieldname)

		if not self.__initializing:
			if fieldname in self.__boundFields and not self.__modified:
				self.__modified = True
				self.__resultSet._setPending(True)
				self.__dispatchEvent ('dsRecordTouched')

			# this was under "if fieldname in self.__boundFields:"
			# i removed this conditions since there where no unbound field update in java client
			# hovever, unbound field update for calculated fields seems to be uneeded
			self.__dispatchEvent ('dsRecordChanged', fields=(fieldname,))


	def unmodify(self):
		if self.__modified:

			fieldsChanged = []
			for fieldname in self.__modifiedFields or ():
				if self.__initialData.has_key(fieldname):
					if fieldname not in self.__fields or self.__fields[fieldname] != self.__initialData[fieldname]:
						fieldsChanged.append(fieldname)
						self.__fields[fieldname] = self.__initialData[fieldname]
				else:
					assert fieldname.startswith('__GNUe__'), 'field must be in initial data: %s' % fieldname

			self.__modifiedFields = None
			self.__modified = False
			self.__resultSet._setPending(None)
			self.__dispatchEvent ('dsRecordChanged', fields=tuple(fieldsChanged))


	# ---------------------------------------------------------------------------

	def items (self):
		"""
		Return a list of tuples of fieldname/value pairs, as if the Record was a
		dictionary.
		"""
		return self.__fields.items ()

	# ---------------------------------------------------------------------------

	def keys (self):
		"""
		Return the list of fieldnames, as if the Record was a dictionary.
		"""
		return self.__fields.keys ()

	# ---------------------------------------------------------------------------

	def values (self):
		"""
		Return the list of field values, as if the Record was a dictionary.
		"""
		return self.__fields.values ()

	# ---------------------------------------------------------------------------

	def copy (self):
		"""
		Return all fieldnames and values as a dictionary, as if the Record was a
		dictionary itself.
		"""
		return self.__fields.copy ()

	# ---------------------------------------------------------------------------

	def update (self, updateDict):
		"""
		Set new values for several fields at once, as if the Record was a
		dictionary.

		@param updateDict: dictionary with the keys being the field names and the
		        values being the new values for the fields.
		@raise Exceptions.ReadOnlyModifyError: if the Record is read only.
		"""
		checktype (updateDict, dict)
		for (fieldname, value) in updateDict.items ():
			self [fieldname] = value


	# ---------------------------------------------------------------------------
	# Find out if a field is modified
	# ---------------------------------------------------------------------------

	def isFieldModified (self, fieldname):
		"""
		Determine whether a field of this record has local modifications.

		This function seems to be used nowhere and might be removed at some point
		because it can return unexpected results in a 3-tier environment: If a
		server side procedure is called, all modification flags are reset (because
		the record is posted to the backend), but the changes are not committed.

		Please do not use this function.

		@param fieldname: Field name.
		@return: True if the field has local modifications, False otherwise.
		"""

		checktype (fieldname, basestring)

		return self.__modifiedFields is not None and fieldname in self.__modifiedFields


	# ---------------------------------------------------------------------------
	# Mark record as deleted
	# ---------------------------------------------------------------------------

	def delete (self, deleted=True):
		"""
		Mark the record as deleted.

		The actual deletion occurs on the next call to the L{_post} method (to be
		called via L{ResultSet.post}).

		@raise Exceptions.ReadOnlyDeleteError: if the Record is read only.
		"""

		# TODO: make trees to normal work with access
		#if not self.__access & ACCESS.DELETE:
		#	raise Exceptions.ReadOnlyDeleteError

		if self.__deleted != deleted:
			self.__deleted = deleted
			self.__resultSet._setPending(deleted or None)
			self.__dispatchEvent(deleted and 'dsRecordDeleted' or 'dsRecordUndeleted')

	# ---------------------------------------------------------------------------
	# Call backend code
	# ---------------------------------------------------------------------------

	def call (self, methodname, parameters):
		"""
		Call a function of the backend.

		It is highly recommended to post this record, it's chain of master records
		and all of it's details before calling this function, so the backend is up
		to date when executing the called backend method.
		L{GDataSource.GDataSource.postAll} provides a convenient way to do this.

		It is also recommended to requery all these records afterwards, so the
		changes done to the data by the called function become visible.
		L{GDataSource.GDataSource.requeryAll} provides a convenient way to do this.

		@param methodname: Name of the function to call.
		@param parameters: Dictionary with parametername/value pairs.
		@return: Return value of the function that was called.
		@raise Exceptions.FunctionCallOfEmptyRecordError: if the record is
		        empty.
		@raise Exception: whatever the called function raises
		"""

		checktype (methodname, basestring)
		checktype (parameters, dict)

		if self.isEmpty():
			raise Exceptions.FunctionCallOfEmptyRecordError

		return self.__connection.call (self.__tablename, self.__wherefields(),
			methodname, parameters)


	# ---------------------------------------------------------------------------
	# Status of this record
	# ---------------------------------------------------------------------------

	def isEmpty (self):
		"""
		Return True if the record is empty.

		"Empty" means that it has been newly inserted, but neither has any field
		been changed nor has a detail for this record been inserted with a status
		other than empty.
		"""
		return self.__inserted and not self.__modified and not self.__deleted \
			and not self.__hasPendingChildren()

	# ---------------------------------------------------------------------------

	def isVoid (self):
		"""
		Return True if the record has been inserted and then deleted.
		"""
		return self.__inserted and self.__deleted

	# ---------------------------------------------------------------------------

	def isInserted (self):
		"""
		Return True if the record has been newly inserted and has either changes
		or a detail has been inserted.

		Records with this status will be inserted into the database on post.
		"""
		return self.__inserted \
			and (self.__modified or self.__hasPendingChildren()) \
			and not self.__deleted

	# ---------------------------------------------------------------------------

	def isModified (self):
		"""
		Return True if the record is an existing record with local changes.

		Records with this status will be updated in the database on post.
		"""
		return not self.__inserted \
			and (self.__modified or self.__hasPendingChildren()) \
			and not self.__deleted

	# ---------------------------------------------------------------------------

	def isDeleted (self):
		"""
		Return True if the record is an existing record that has been deleted.

		Records with this status will be deleted in the database on post.
		"""
		return not self.__inserted and self.__deleted

	# ---------------------------------------------------------------------------

	def isPending (self):
		"""
		Return True if the record has any local changes that make it necessary to
		post it to the database.

		The result is True if either isInserted, isModified, or isDeleted is True.

		If the record is void (i.e. has been inserted and then deleted again),
		isPending also returns True even though no changes will be written to the
		backend.
		"""
		# ... but we check status fields instead of isXxxx to not have to evaluate
		# __hasPendingChildren several times.
		return self.__modified or self.__hasPendingChildren() or self.__deleted

	# ---------------------------------------------------------------------------

	def __hasPendingChildren (self):
		if self.__cachedDetailResultSets:
			for child in self.__cachedDetailResultSets.values ():
				if child.isPending():
					return True
		return False


	# ---------------------------------------------------------------------------
	# Make this Record the current one (notify all details)
	# ---------------------------------------------------------------------------

	def _activate (self):
		"""
		Make this the current record, notifying all detail datasources.

		This is called by the ResultSet whenever the record pointer is moved to
		this record.
		"""

		for dataSource in self.__details.keys ():

			# If we already have it in our cache, activate it
			if self.__cachedDetailResultSets and self.__cachedDetailResultSets.has_key(dataSource):
				resultset = self.__cachedDetailResultSets [dataSource]
				if resultset.isPending() or int (gConfig ('CacheDetailRecords')):
					dataSource._activateResultSet (resultset)
					continue

			# If this record is new, it can't have any detail records yet anyway, so
			# create empty detail result sets.  Query the matching details otherwise.
			# TODO: must send here access (oleg)
			if self.__inserted:
				resultset = dataSource.createEmptyResultSet (masterRecord = self)
			else:
				resultset = dataSource.createResultSet (masterRecord = self)

			# Remember it
			if self.__cachedDetailResultSets is None:
				self.__cachedDetailResultSets = {}
			self.__cachedDetailResultSets [dataSource] = resultset

			# need to know resultset only to invalidate isPending (isPending optimizaion)
			resultset._setMasterResultSet(self.__resultSet)

			# remove cached pending
			self.__resultSet._setPending(None)


	# ---------------------------------------------------------------------------
	# Post changes to database
	# ---------------------------------------------------------------------------

	def _post (self, parameters):
		"""
		Write all local changes for this record to the backend, as
		well as for all detail records where this record is the master.

		This is called by L{ResultSet.post} for each record with pending changes.

		This function does not change the record's status; the record remains dirty
		and the list of modified fields remains intact. In case the whole
		transaction succeeds, the L{_requery} method must be called subsequently,
		which will set the record status to "clean". However, if an exception in a
		later operation of the same transaction happens and causes a rollback on
		the backend, the record's _post method can simply be called again.
		"""
		# Just to make sure - you never know who calls us...
		if not self.isPending() or self.isVoid():
			return

		self.__resultSet._setPending(None)

		# Call the hooks for commit-level hooks
		# A trigger code could change the status from empty/inserted/modified to
		# deleted. In that case, both triggers would be called.
		if self.__inserted:
			self.__dispatchEvent ('dsCommitInsert')
		elif self.__modified:
			self.__dispatchEvent ('dsCommitUpdate')
		if self.__deleted:
			self.__dispatchEvent ('dsCommitDelete')

		# Check for empty primary key and set with the sequence value if so
		if self.__inserted:
			if len (self.__primarykeyFields) == 1 and \
				self [self.__primarykeyFields [0]] is None and \
				self.__primarykeySeq is not None and \
				hasattr (self.__connection, 'getSequence'):
				pk = self.__connection.getSequence (self.__primarykeySeq)
				self [self.__primarykeyFields [0]] = pk

		# If we have a connection (i.e. we aren't static or unbound), do the post
		if self.__connection is not None:
			if self.__deleted:
				self.__connection.delete (self.__tablename, self.__wherefields())
			elif self.__inserted or self.__modified:
				modifiedFields = {}
				for field in self.__boundFields:
					#if self.isFieldModified(field):
					# WORKAROUND: stored procedure always needs all fields
					# TODO: think about it
					if self.__rowidField and field != self.__rowidField or self.isFieldModified(field):
						modifiedFields [field] = self.__fields [field]

				# oleg:
				# for postgresql_fn: pass parameters with modifiedFields
				if parameters:
					p = parameters.copy()
					p.update(modifiedFields)
					modifiedFields = p

				if self.__inserted:
					rowid = self.__connection.insert (self.__tablename, modifiedFields)
					if self.__rowidField:
						assert rowid is not None, 'insert not returned new row id for %s' % self.__tablename
						self.__fields [self.__rowidField] = rowid
						# Also set initialData so the requery can work
						self.__initialData [self.__rowidField] = rowid
						# Requery all the fields that are important for inserting details.
						# A backend trigger could have e.g. generated a primary key.
						# TODO: We could save this work for cases where the detail
						# resultsets don't have any inserted records.
						if self.__detailLinkFlags:
							self.__do_requery (self.__detailLinkFlags.keys (), parameters)
				else:
					self.__connection.update (self.__tablename, self.__wherefields(),
						modifiedFields)

		# Record needs a requery now
		self.__requeryStatus = 'posted'

		if self.__inserted:
			self.__dispatchEvent ('dsPostCommitInsert')
		elif self.__modified:
			self.__dispatchEvent ('dsPostCommitUpdate')
		if self.__deleted:
			self.__dispatchEvent ('dsPostCommitDelete')

		# Post all detail records
		if self.__cachedDetailResultSets:
			for (dataSource, resultSet) in (self.__cachedDetailResultSets.items ()):
				fkData = {}
				for (pkField, fkField) in zip (*self.__details [dataSource]):
					fkData [fkField] = self [pkField]
				resultSet.post (fkData = fkData)


	# ---------------------------------------------------------------------------
	# Return whether this record must be requeried or not
	# ---------------------------------------------------------------------------

	def _needsRequery (self, commit):
		"""
		Return True if this record should be requeried.

		Records are requeried after a post and after a commit.

		@param commit: indicate whether the transaction in which the last post
		        happened has been committed.
		"""
		return (self.__requeryStatus == 'posted') \
			or (self.__requeryStatus == 'commit' and commit) \
			or self.isEmpty() or self.isVoid()


	# ---------------------------------------------------------------------------
	# Requery the record data from the backend
	# ---------------------------------------------------------------------------

	def _requery (self, commit, parameters):
		"""
		Requery this record to reflect changes done by the backend.

		This is called by L{ResultSet.requery} for each record that has been posted
		in the last L{ResultSet.post} call.

		Note that this method also updates the record status, so it has to be
		called even if the requery feature is not used.

		@param commit: True if a commit happened since the L{_post} call. If no
		        commit has happened, the record will be requeried again after the
		        following commit.
		"""

		if self.__requeryStatus is None:
			return

		# The record is now "clean" again
		self.__inserted = False
		self.__modified = False
		self.__modifiedFields = None
		self.__initialData = self.__fields
		# memory optimization: no need to copy if resultSet not editable
		if self.__access & ACCESS.WRITE:
			self.__initialData = self.__initialData.copy()

		# self.__modified changed, reset cahced pending
		self.__resultSet._setPending(None)
		
		if commit:
			self.__requeryStatus = None
		else:
			self.__requeryStatus = 'commit'

		# First, requery ourselves
		if self.__requery:
			if self.__rowidField or self.__primarykeyFields:
				self.__do_requery (self.__boundFields, parameters)

		# Now, requery detail resultsets
		if self.__cachedDetailResultSets:
			for (dataSource, resultSet) in self.__cachedDetailResultSets.items ():
				dataSource._requeryResultSet (self, resultSet)


	# ---------------------------------------------------------------------------
	# Set clean data from a dictionary
	# ---------------------------------------------------------------------------

	def _initialDataFromDict (self, data):
		"""
		Set the clean data of the record from a dictionary.

		This is used when this record is in a detail ResultSet that has been
		requeried completely.

		@param data: Fieldname/value dictionary with the new clean data.
		"""

		self.__initialData.update (data)

		if self.__requeryStatus == 'posted':
			# record has been written to the backend - everything is clean now
			self.__fields.update (data)
			self.__inserted = False
			self.__modified = False
			self.__modifiedFields = None
			self.__requeryStatus = None
			self.__resultSet._setPending(None)

		else:
			# record may have unsaved changes because the last _post to this record
			# (or a preceding record) failed - we have to be cautious not to
			# overwrite changes the user has done
			for (fieldname, value) in data.items ():
				if not self.isFieldModified(fieldname):
					self.__fields [fieldname] = value

		# Now, requery detail resultsets
		if self.__cachedDetailResultSets:
			for (dataSource, resultSet) in self.__cachedDetailResultSets.items ():
				dataSource._requeryResultSet (self, resultSet)


	# ---------------------------------------------------------------------------
	# Requery this record
	# ---------------------------------------------------------------------------

	def __do_requery (self, fields, parameters):
		newfields = self.__connection.requery (self.__tablename,
			self.__wherefields(), fields, parameters)
		fieldsChanged = tuple((k for k, v in newfields.iteritems() if k not in self.__fields or self.__fields[k] != v))
		self.__fields.update (newfields)
		self.__dispatchEvent ('dsRecordChanged', fields=fieldsChanged)


	# ---------------------------------------------------------------------------
	# Fields to be used in WHERE clauses for UPDATE and DELETE.
	# ---------------------------------------------------------------------------

	def __wherefields (self):

		result = {}

		# First priority: row id
		if self.__rowidField:
			result [self.__rowidField] = self.__initialData [self.__rowidField]

		# Second priority: primary key
		elif self.__primarykeyFields:
			for field in self.__primarykeyFields:
				result [field] = self.__initialData [field]

		# If all else fails, use all fields in the where clause
		else:
			for field in self.__boundFields:
				if self.__initialData.has_key (field):
					result [field] = self.__initialData [field]

		return result


	# ---------------------------------------------------------------------------
	# Dispatch an event
	# ---------------------------------------------------------------------------

	def __dispatchEvent (self, event, **params):
		if self.__eventController is not None:
			self.__eventController.dispatchEvent (event, record = self, **params)


	# ---------------------------------------------------------------------------
	# Depreciated methods (replaced by dictionary functions)
	# ---------------------------------------------------------------------------

	def getField (self, fieldname):
		"""
		Depreciated: use [fieldname] instead!
		"""
		return self [fieldname]

	# ---------------------------------------------------------------------------

	def setField (self, fieldname, value):
		"""
		Depreciated: use [fieldname] instead!
		"""
		self [fieldname] = value

	# ---------------------------------------------------------------------------

	def getFieldsAsDict (self):
		"""
		Depreciated: use L{copy} instead!
		"""
		return self.copy()

	# ---------------------------------------------------------------------------

	def setFields (self, updateDict):
		"""
		Depreciated: use L{update} instead!
		"""
		self.update (updateDict)

	def dump(self):
		print self
		for key in self.__initialData.iterkeys():
			print "\t %s = %s" % (key, self[key]),
			if key in (self.__modifiedFields or ()):
				print "modified"
			else:
				print
