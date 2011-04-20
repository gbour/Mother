#!/usr/bin/env python
# -*- coding: utf8 -*-
__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010-2011, Guillaume Bour <guillaume@bour.cc>

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU Affero General Public License as
	published by the Free Software Foundation, version 3.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Affero General Public License for more details.

	You should have received a copy of the GNU Affero General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from tentacles               import *
from tentacles.fields        import *
from mother.dbfields         import *
from mother.pluggable        import Plugin
from mother                  import routing

from zope.interface          import implements
from twisted.cred            import checkers
from twisted.cred.portal     import IRealm
from twisted.web.resource    import IResource
from twisted.web             import http


class User(Object):
	__stor_name__ = 'mother__authuser'

	uid           = Integer(pk=True)
	username      = String(unique=True, allow_none=False)
	password      = String()

	firstname     = String()
	lastname      = String()
	email         = String()

	active        = Boolean(default=True)

	creation      = Datetime(default='now')
	last_login    = Datetime()

	icon          = Binary()

	#TODO
	#password      = Password()
	#email         = Email()
	#icon          = Image()


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


class UnauthorizedResource(Resource):
	isLeaf = True
	
	def __init__(self):
		pass

	def render(self, request):
		ctype = request.getHeader('content-type')
		request.setResponseCode(401)

		print 'Zzzz', ctype
		if ctype == 'text/html':
			print 'yop'
			return '<html><body><b>Unauthorized</b></body></html>'

		return 'Unauthorized'

	def getChildWithDefault(self, path, request):
		return self

from twisted.web.server import Session
from twisted.python.components import registerAdapter
from zope.interface import Interface, Attribute, implements


class IMotherSession(Interface):
	logged = Attribute("True if authenticated (logged)")
	user   = Attribute("User logged")


class MotherSession(object):
	implements(IMotherSession)

	def __init__(self, session):
		self.logged = False
		self.user   = None

registerAdapter(MotherSession, Session, IMotherSession)

class HTTPAuthResource(Resource):
	def render(self, request):
		request.setResponseCode(http.UNAUTHORIZED)
					#request.responseHeaders.addRawHeader(
					#	'www-authenticate', "Basic realm=\"bozo\""
					#)

		return '<html><body><b>MUST LOG</b></body></html>'

	def getChildWithDefault(self, path, request):
		return self


class AuthWrapper(Resource):
	#TODO: use implements(IResource) instead
	isLeaf = False

	def __init__(self, portal, credentialFactories):
			Resource.__init__(self)

			self._portal              = portal
			self._credentialFactories = credentialFactories

	#def render(self, request):
	#	# called 
	#	print 'auth::rendering', request.path

	def getChildWithDefault(self, path, request):
		# Don't consume any segments of the request - this class should be
		# transparent!
		request.postpath.insert(0, request.prepath.pop())

		# no resource for this url
		if path not in self.children:
			return UnauthorizedResource()

		## child is a plugin root Resource
		child = self.children[path]
		mod   = child.plugin.MODULE

		# get Accept mime-types, by preference descendant order
		print request.getHeader('Accept')
		from twisted.web2 import http_headers
		head = http_headers.Headers(handler=http_headers.DefaultHTTPHandler)
		head.setRawHeaders('Accept', (request.getHeader('Accept'),))
		accept = head.getHeader('Accept')
		print accept

		accept = sorted([(mime, prio) for mime, prio in accept.iteritems()], key=lambda	x: -x[1])
		print 'Accept=', accept

		# AUTH deactivated for application
		if not mod.AUTHENTICATION:
			return child

		# get login resource if set
		login = child.getChild(routing.LOGIN, request)

		# Does requested target require authentication
		print path, request.postpath, request.prepath
		path = request.postpath.pop(0)
		request.prepath.append(path)

		target = child.getChild(path, request)
		from twisted.web.resource import NoResource
		if isinstance(target, NoResource):
			return target

		if hasattr(target, 'func'):
			print 'auth req=', target.func.__callable__.get('auth_required', True)
		# auth required for this target ?
		if hasattr(target, 'func') and not target.func.__callable__.get('auth_required', True):
			return target

		# Is user authenticated ?
		# we have 2 methods of authentication:
		#		. http auth
		#		. cookie/session

		#NOTE: if App. does not set callback for LOGIN i/o LOGOUT urls, 
		# we use HTTP authentication
		http_auth = request.getHeader('authorization')
		sess      = IMotherSession(request.getSession())
		print 'SESS=', sess.logged, sess.user
		if not http_auth and not sess.logged:
			print 'No authenticated'
			#NOTE: this ressource MUST return a 404
			return child.getChild(routing.LOGIN, request)

			"""
			class LoginResource(Resource):
				def render(self, request):
					request.setResponseCode(401)
					#request.responseHeaders.addRawHeader(
					#	'www-authenticate', "Basic realm=\"bozo\""
					#)

					return '<html><body><b>MUST LOG</b></body></html>'
			"""
			#return LoginResource()

			# when redirecting, we should memorize current request 
			# to redisplay page after login
			#   + GET params
			#   + POST/PUT params
			# => VIEWSTATE
			"""
			class RedirectResource(Resource):
				def render(self, request):
					request.redirect('/' + path + routing.LOGIN.url)
					return ''
			"""
			#return RedirectResource()

			

		"""
            return util.DeferredResource(self._login(Anonymous()))
        factory, respString = self._selectParseHeader(authheader)
        if factory is None:
            return UnauthorizedResource(self._credentialFactories)
        try:
            credentials = factory.decode(respString, request)
        except error.LoginFailed:
            return UnauthorizedResource(self._credentialFactories)
        except:
            log.err(None, "Unexpected failure from credentials factory")
            return ErrorPage(500, None, None)
        else:
            return util.DeferredResource(self._login(credentials))

       @return: A two-tuple of a factory and the remaining portion of the
            header value to be decoded or a two-tuple of C{None} if no
            factory can decode the header value.

        elements = header.split(' ')
        scheme = elements[0].lower()
        for fact in self._credentialFactories:
            if fact.scheme == scheme:
                return (fact, ' '.join(elements[1:]))
        return (None, None)
		"""
		return child


