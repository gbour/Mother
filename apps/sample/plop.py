#!/usr/bin/env python
# -*- coding: UTF8 -*-

from mother.callable import Callable, callback
class Plop(object):
	@callback
	def root(self, request):
		return 'ROOT'

	@callback
	def plop(self, request):
		return 'PLOP'

	def plip(self, request, arg1):
		return 'PLIP(%s)' % arg1

	def plup(self, request, arg1):
		return 'PLUP(%s)' % arg1
