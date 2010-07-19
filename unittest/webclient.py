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

import httplib, urllib, base64
import cjson

class WebClient(object):
	def __init__(self, address='localhost', port=80, debug=False):
		self.headers = {
			"Content-type": "application/json",
			"Accept"      : "text/plain"
		}
		
		self.conn  = httplib.HTTPConnection(address, port)
		self.debug = debug

	def request(self, method, uri, headers={}, params={}, qargs={}, json=True):
		if json:
			params = cjson.encode(params)

		if len(qargs) > 0:
			uri    += '?' + urllib.urlencode(qargs)

		_headers = self.headers.copy()
		_headers.update(headers)
		if self.debug:
			print 'querying= %s %s' % (method, uri), _headers, params if json else ''
		
		self.conn.request(method, uri, params, _headers)
		response = self.conn.getresponse()
		data	 = response.read()
		
		if self.debug:
			print response.status,
			if response.getheader('content-type', '') == 'application/json':
				print data
			else:
				print ''

		return (response, data)

