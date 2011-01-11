#!/usr/bin/env python
# -*- coding: utf8 -*-

from mother.eurl import *
from twisted.trial.unittest import TestCase

class EUrlTests(TestCase):
	def setUp(self):
		pass

	def test_base(self):
		d = eURL()
		self.assertEqual(len(d), 0)

		d[('/foo', 'text/plain')] = 'MyResource'
		self.assertEqual(len(d), 1)
		self.assertEqual(d.has_key(('/foo', 'text/plain')), True)
		self.assertEqual(d.has_key(('/foo', 'text/*'))    , True)
		self.assertEqual(d.has_key(('/foo', '*/*'))       , True)
		self.assertEqual(d.has_key(('/foo', 'text/html')) , False)
		self.assertEqual(d.has_key(('/bar', 'text/plain')), False)

		self.assertEqual(d[('/foo', 'text/plain')], 'MyResource')
		self.assertEqual(d[('/foo', 'text/*')]    , 'MyResource')
		self.assertEqual(d[('/foo', '*/*')]       , 'MyResource')
		#HOW TO DO THAT? self.assertRaises(KeyError, d[('/foo', 'text/html')])


		d[('/foo', 'text/html')]  = 'MyResource2'
		self.assertEqual(len(d), 2)
		self.assertEqual(d.has_key(('/foo', 'text/html')), True)

	def test_getWithBaseContentType(self):
		d = eURL()
		d[('/foo', 'text/plain')] = 'MyResource'
		d[('/foo', 'text/html')]  = 'MyResource2'

		self.assertEqual(d.getWithBaseContentType(('/foo', 'text/html')), 
			('text/html',	'MyResource2'))
		self.assertEqual(d.getWithBaseContentType(('/foo', 'text/*')), 
			('text/plain',	'MyResource'))
		self.assertRaises(KeyError, d.getWithBaseContentType, ('/foo', 'text/foo'))

	def test_getURL(self):
		d = eURL()
		d[('/foo', 'text/plain')] = 'MyResource'
		d[('/foo', 'text/html')]  = 'MyResource2'

		self.assertEqual(d.getURL('/foo'), {
			'*/*'        : [None, ('text/plain', 'MyResource'), ('text/html', 'MyResource2')],
			'text/*'     : [None, ('text/plain', 'MyResource'), ('text/html', 'MyResource2')],
			'text/plain' : ['MyResource'],
			'text/html'  : ['MyResource2'],
		})

		self.assertRaises(KeyError, d.getURL, '/bar')

	def test_getContentType(self):
		d = eURL()
		d[('/foo', 'text/plain')] = 'MyResource'

		self.assertEqual(d.getContentType('/foo', 'text/plain')      , 'text/plain')
		self.assertEqual(d.getContentType('/foo', 'text/html')       , 'text/*')
		self.assertEqual(d.getContentType('/foo', 'application/json'), '*/*')
		self.assertEqual(d.getContentType('/bar', 'application/json'), None)
		#self.assertRaises(KeyError, d.getContentType, '/bar', 'text/plain')

	

