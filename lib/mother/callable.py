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
	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""

import sys, inspect, types

#def callback(fnc):
#	print "callback(%s)" % fnc.__name__
#	fnc.__dict__['__callable__'] = fnc.__name__

#	# we get root module
#	modname = fnc.func_globals['__name__'].split('.',1)[0]
#	module  = sys.modules[modname]

#	if '__callbacks__' not in dir(module):
#		module.__callbacks__ = {}
#	module.__callbacks__[fnc.__name__] = True

#	return fnc

def callback(method='GET', *args, **kwargs):
	def deco(fnc):
		fnc.__dict__['__callable__'] = {
			'name': kwargs['name'] if 'name' in kwargs else fnc.__name__, 
			'method': method
		}
		return fnc

	# special case where invoking callback as keyword, not function 
	# (@callback instead of @callback())
#	print method, type(method)
	if isinstance(method, types.FunctionType):
		fnc	 = method
		method  = ['GET']
		return deco(fnc)
		
	if isinstance(method, str):
		method = (method,)

	return deco


class Callable(object):
	pass

