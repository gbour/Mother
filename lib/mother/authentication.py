#!/usr/bin/env python
# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010, Guillaume Bour <guillaume@bour.cc>

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License along
	with this program; if not, write to the Free Software Foundation, Inc.,
	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

from tentacles               import *
from tentacles.fields        import *
from mother.dbfields         import *
from mother.pluggable        import Plugin

from zope.interface          import implements
from twisted.cred            import checkers
from twisted.cred.portal     import IRealm
from twisted.web.resource    import IResource


class User(Object):
	__stor_name__ = 'mother__authuser'

	uid           = Integer(pk=True)
	username      = String(unique=True, allow_none=False)
	#password      = Password()
	password      = String()

	firstname     = String()
	lastname      = String()
	#email         = Email()
	email         = String()

	active        = Boolean(default=True)

	creation      = Datetime(default='now')
	last_login    = Datetime()

	#icon          = Image()
	icon          = Binary()

class Group(Object):
	"""
	"""
	__stor_name__ = 'mother__authgroup'

	gid           = Integer(pk=True)
	name          = String(unique=True, allow_none=False)

class Members(Object):
	"""
		a user is member of a group for a *given* application

		NOTE: app == NULL is for default group membership
	"""
	__stor_name__ = 'mother__authmembers'
	id            = Integer(pk=True)

	grp           = Reference(Group)
	app           = Reference(Plugin, allow_none=True)
	
	user          = Reference(User)

class Acl(Object):
	__stor_name__ = 'mother__appacl'
	id            = Integer(pk=True)

	# we set either user or group
	user          = Reference(User, allow_none=True)
	grp           = Reference(Group, allow_none=True)

	app           = Reference(Plugin)

	#TODO:  extra fields


from twisted.web.resource import Resource
"""
	NOTE: the resource is independent from the url tree

	When anonymous, return PlopResource, but the tree remains the same,
		and returned resource must resolve it
"""
class PlopResource(Resource):
	def getChild(self , path, request):
		print 'plop::getchild=', path
		return self

	def render_GET(self, request):
		return 'PLOP'

class MotherRealm(object):
	implements(IRealm)

	def __init__(self, res):
		self.res = res

	def requestAvatar(self, avatarId, mind, *ifaces):
		print "request avatar:", avatarId, ifaces, avatarId == checkers.ANONYMOUS
		if IResource in ifaces:
			if avatarId is checkers.ANONYMOUS:
				return (IResource, PlopResource(), lambda: None)
			else:
				return (IResource, self.res, lambda: None)

	

