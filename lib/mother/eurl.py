#!/usr/bin/env python
# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010-2011, Guillaume Bour <guillaume@bour.cc>

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License version 3
	as published by the Free Software Foundation.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.

	You should have received a copy of the GNU Affero General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
#from odict import odict

class eURL(dict):
	def __init__(self, *args, **kwargs):
		self.__privlen__ = 0

	def __setitem__(self, key, value):
		"""
		"""
		if not isinstance(key, (list, tuple)) or len(key) != 2:
			raise Exception("Invalid key. Must be (url, content-type) tuple")

		# value must be a Resource ?
		subdict = self.setdefault(key[0], dict())

		# primary content-type: append first
		items = subdict.setdefault(key[1], list((None,)))
		if items[0] is not None:
			# replacing value
			self.__delitem__(key)
			subdict = self.setdefault(key[0], dict())
			items   = subdict.setdefault(key[1], list((None,)))
		items[0] = value

		self.__privlen__ += 1
		if key[1].startswith('internal/'):
			return
		
		for _ctype in ('%s/*' % key[1].split('/',1)[0], '*/*'):
			items = subdict.setdefault(_ctype, list((None,)))
			if items[0] != value:
				items.append((key[1], value))


	def getWithBaseContentType(self, key):
		"""
			Get value exactly matching (url, content-type) key
		"""

		if not isinstance(key, (list, tuple)) or len(key) != 2:
			raise Exception("Invalid key. Must be (url, content-type) tuple")

		# raise KeyError if not found
		ret = dict.__getitem__(self, key[0])[key[1]]
		if ret[0] is None:
			if len(ret) > 1:
				return ret[1]
			raise KeyError

		return (key[1], ret[0])


	def __getitem__(self, key):
		return self.getWithBaseContentType(key)[1]


	def __delitem__(self, key):
		if not isinstance(key, (list, tuple)) or len(key) != 2:
			raise Exception("Invalid key. Must be (url, content-type) tuple")

		subdict = dict.__getitem__(self, key[0])
		items   = subdict[key[1]]

		if items[0] is None:
			raise KeyError(key[1])

		self.__privlen__ -= 1
		if key[1].startswith('internal/'):
			return

		#TODO: flawless: the same value could have be set with another content-type
		# but works as a 1st approach
		for _ctype in ('%s/*' % key[1].split('/',1)[0], '*/*'):
			if _ctype == key[1]:
				continue

			ctypedict = subdict[_ctype]
			ctypedict.remove((key[1], items[0]))

			if len(ctypedict) == 1 and ctypedict[0] is None:
				del subdict[_ctype]

		if len(items) == 1:
			del subdict[key[1]]
			if len(subdict) == 0:
				dict.__delitem__(self, key[0])
		else:
			items[0] = None


	def __contains__(self, key):
		"""
			NOTE: d.has_key() and
		"""
		if not isinstance(key, (list, tuple)) or len(key) != 2:
			raise Exception("Invalid key. Must be (url, content-type) tuple")

		if not dict.__contains__(self, key[0]):
			return False

		return dict.__getitem__(self, key[0]).__contains__(key[1])
	has_key = __contains__


	def __len__(self):
		return self.__privlen__


	def getURL(self, url):
		return dict.__getitem__(self, url)

	def hasURL(self, url):
		return dict.has_key(self, url)

	def getContentType(self, url, ctype):
		"""Return the most-specific content-type associated with the url.

			If url not found, raise KeyError exception, else return the most-specific
			content-type found for the given url/ctype.

			For example, url '/foo' as 'text/plain' associated with
			If you search for 'text/html' Content-Type, function will return 'text/*'

			>>> urlDict = eUrl()
			>>> urlDict[('/foo', 'text/plain')] = 'MyResource'

			>>> print urlDict.getContentType('/foo', 'text/plain')
			text/plain

			>>> print urlDict.getContentType('/foo', 'text/html')
			text/*

			>>> print urlDict.getContentType('/foo', 'application/json')
			*/*

			>>> print urlDict.getContentType('/bar', 'text/plain')
			None

		"""
		# return None if url not found
		subdict = dict.get(self, url, None)
		if subdict is None:
			return None

		for _ctype in (ctype, '%s/*' % ctype.split('/',1)[0], '*/*'):			
			if _ctype in subdict:
				return _ctype
		
		return None

	def getMatchContentType(self, url, ctype):
		"""
			>>> urlDict = eUrl()
			>>> urlDict[('/foo', 'text/plain')] = 'MyResource'

			>>> print urlDict.getContentType('/foo', 'text/plain')
			text/plain

			>>> print urlDict.getContentType('/foo', 'text/html')
			text/plain

			>>> print urlDict.getContentType('/foo', 'application/json')
			text/plain

			>>> print urlDict.getContentType('/bar', 'text/plain')
			None
		"""
		subdict = dict.get(self, url, None)

		if subdict is None:
			return None

		for _ctype in (ctype, '%s/*' % ctype.split('/',1)[0], '*/*'):			
			if _ctype in subdict:
				data = subdict[_ctype]
				return _ctype if data[0] is not None else data[1][0]
		
		return None

