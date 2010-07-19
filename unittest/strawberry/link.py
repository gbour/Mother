# -*- coding: utf-8 -*-
from __future__ import with_statement

__version__ = "$Revision$ $Date$"
__author__  = "Guillaume Bour <guillaume@bour.cc>"
__license__ = """
	Copyright (C) 2010, Guillaume Bour <guillaume@bour.cc>

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; version 3 of the License

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License along
	with this program; if not, write to the Free Software Foundation, Inc.,
	51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""
import sys, unittest, cjson, hashlib, magic
from webclient import *


#r, data = w.request('DELETE', '/strawberry/link', qargs={'id': linkid})
#print 'deleted=', data

class Test12Link(unittest.TestCase):
	def setUp(self):
		# WARNING: is runned before each test
		self.w      = WebClient(address='localhost', port=9998)
		self.linkid = 100

#	def test_01_defaultvalue(self):
#		# getting default link
#		(resp, data) = self.w.request('GET', '/strawberry/link', qargs={'id': 1})
#		self.assertEqual(resp.status, 200)
#		
	def test_02_create(self):
		(resp, data) = self.w.request('PUT', '/strawberry/link', params={
			'id'  : self.linkid,
			'link': 'http://linuxfr.org',
			'name': 'Da Linux French Page',
			'tags': ['bookmarks service', 'linux', 'journals'],
		})
		
		self.assertEqual(resp.status, 200)

		try:
			data = int(data)
		except ValueError:
			self.fail('newly created link id must be int (is %s)' % data)

	def test_03_createtwice(self):
		# duplicate ID
		(resp, data) = self.w.request('PUT', '/strawberry/link', params={
			'id'  : self.linkid,
			'link': 'http://linuxfr.org',
			'name': 'Da Linux French Page',
		})
		
		self.assertEqual(resp.status, 400)

		# duplicate NAME
		(resp, data) = self.w.request('PUT', '/strawberry/link', params={
			'link': 'http://linuxfr.org',
			'name': 'Da Linux French Page',
		})
		
		self.assertEqual(resp.status, 400)

		# unknown field (foo)
		(resp, data) = self.w.request('PUT', '/strawberry/link', params={
			'link': 'http://linuxfr.org/1234',
			'name': 'Da Linux French Page',
			'foo' : 'baz'
		})
		
		self.assertEqual(resp.status, 409)

	def test_03_seticon(self):
		with open('./strawberry/py.png', 'rb') as fd:
			icon = fd.read()
			
		m = magic.open(magic.MAGIC_MIME)
		m.load()
		mime = m.buffer(icon).split(';')[0]
		m.close()

		(resp, data) = self.w.request('PUT', '/strawberry/link/icon', params=icon, \
			qargs={'id': self.linkid}, json=False, headers={'Content-type': mime})
			
		self.assertEqual(resp.status, 200)

	def test_04_geticon(self):
		with open('./strawberry/py.png', 'rb') as fd:
			icon = fd.read()
		src_hash = hashlib.md5(icon).digest()
		
		(resp, data) = self.w.request('GET', '/strawberry/link/icon', qargs={'id': self.linkid})
		self.assertEqual(resp.status, 200)
		self.assertEqual(resp.getheader('content-type', ''), 'image/png')

		dst_hash = hashlib.md5(data).digest()
		self.assertEqual(dst_hash, src_hash)

	def test_05_delicon(self):
		(resp, data) = self.w.request('DELETE', '/strawberry/link/icon', qargs={'id': self.linkid})
		self.assertEqual(resp.status, 200)

	def test_05_icon_errorcases(self):
		# delete always true (set to None)
		(resp, data) = self.w.request('DELETE', '/strawberry/link/icon', qargs={'id': self.linkid})
		self.assertEqual(resp.status, 200)

		# found, but no data (icon is empty)
		(resp, data) = self.w.request('GET', '/strawberry/link/icon', qargs={'id': self.linkid})
		self.assertEqual(resp.status, 204)

	def test_06_setscreenshot(self):
		with open('./strawberry/py.png', 'rb') as fd:
			icon = fd.read()
			
		m = magic.open(magic.MAGIC_MIME)
		m.load()
		mime = m.buffer(icon).split(';')[0]
		m.close()

		(resp, data) = self.w.request('PUT', '/strawberry/link/screenshot', params=icon, \
			qargs={'id': self.linkid}, json=False, headers={'Content-type': mime})
			
		self.assertEqual(resp.status, 200)

	def test_07_getscreenshot(self):
		with open('./strawberry/py.png', 'rb') as fd:
			icon = fd.read()
		src_hash = hashlib.md5(icon).digest()
		
		(resp, data) = self.w.request('GET', '/strawberry/link/screenshot', \
			qargs={'id': self.linkid})
		self.assertEqual(resp.status, 200)
		self.assertEqual(resp.getheader('content-type', ''), 'image/png')

		dst_hash = hashlib.md5(data).digest()
		self.assertEqual(dst_hash, src_hash)

	def test_08_delscreenshot(self):
		(resp, data) = self.w.request('DELETE', '/strawberry/link/screenshot', \
			qargs={'id': self.linkid})
		self.assertEqual(resp.status, 200)

	def test_09_screenshot_errorcases(self):
		# delete always true (set to None)
		(resp, data) = self.w.request('DELETE', '/strawberry/link/screenshot', \
			qargs={'id': self.linkid})
		self.assertEqual(resp.status, 200)

		# found, but no data (icon is empty)
		(resp, data) = self.w.request('GET', '/strawberry/link/screenshot', \
			qargs={'id': self.linkid})
		self.assertEqual(resp.status, 204)


	def test_10_getone(self):
		(resp, data) = self.w.request('GET', '/strawberry/link', qargs={'id': self.linkid})
		self.assertEqual(resp.status, 200)
		data = cjson.decode(data)

		self.assertTrue('name' in data)
		self.assertEqual(data['name'], 'Da Linux French Page')

		self.assertTrue('link' in data)
		self.assertEqual(data['link'], 'http://linuxfr.org')

	def test_11_getall(self):
		(resp, data) = self.w.request('GET', '/strawberry/link/all')
		self.assertEqual(resp.status, 200)
		data = cjson.decode(data)
		self.assertTrue(isinstance(data, list))
		self.assertEqual(len(data), 2)

	def test_20_delete(self):
		(resp, data) = self.w.request('DELETE', '/strawberry/link', qargs={'id': self.linkid})
		self.assertEqual(resp.status, 200)

		# delete non existing link => error 404
		(resp, data) = self.w.request('DELETE', '/strawberry/link', qargs={'id': self.linkid})
		self.assertEqual(resp.status, 404)


if __name__ == '__main__':
	unittest.main()



#		(resp, data) = self.client.list(self.obj)
#		self.assertEqual(resp.status, 200)
#		
##		pprint.pprint(data)
#		data = cjson.decode(data)
##		pprint.pprint(data[0])
#		count = len(data)
#		
#		# ADD
#		with open('xivojson/user.json') as f:
#			content = cjson.decode(f.read())
#			
##		print content
#		(resp, data) = self.client.add(self.obj, content)
#		pprint.pprint(data)
#		self.assertEqual(resp.status, 200)

##		# LIST / Check add
##		(resp, data) = self.client.list('incall')
##		self.assertEqual(resp.status, 200)
###		
##		data = cjson.decode(data)
###		pprint.pprint(data)
##		count2 = len(data)
##		self.assertEqual(count2, count+1)
##		self.assertTrue('exten' in data[1])
##		self.assertTrue(data[1]['exten'] == '1001')
##		
##		id = data[1]['id']

##		# SEARCH
##		(resp, data) = self.client.view('incall', id)
##		self.assertEqual(resp.status, 200)

##		data = cjson.decode(data)
###		pprint.pprint(data)
##		self.assertTrue('incall' in data)
##		self.assertTrue(data['incall']['exten'] == '1001')

##		# DELETE
#		id = 3
#		(resp, data) = self.client.delete(self.obj, id)
#		self.assertEqual(resp.status, 200)
#		pprint.pprint(data)

##		# try to redelete => must return 404
##		(resp, data) = self.client.delete('incall', id)
##		self.assertEqual(resp.status, 404)
##		

