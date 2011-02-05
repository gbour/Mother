#!/usr/bin/env python
# -*- coding: utf8 -*-


class LoopbackSelf(object):
	def __init__(self, called=None):
		self.called = called

	def __getattr__(self, name):
		if self.called is None:
			return LoopbackSelf(name)

		self.called += "." + name
		return self

	def __str__(self):
		return "LoopbackSelf(%s)" % self.called

	def __repr__(self):
		return self.__str__()

print LoopbackSelf().toto
try:
	print LoopbackSelf.tutu
except Exception,e:
	print e

import inspect

loop = LoopbackSelf()
print type(LoopbackSelf), type(loop)
print inspect.isclass(LoopbackSelf), inspect.isclass(loop)

# hot-patching (fixed in python 2.7+). see
# http://stackoverflow.com/questions/4081819/why-does-python-inspect-isclass-think-an-instance-is-a-class
import types
inspect.isclass = lambda obj: isinstance(obj, (type, types.ClassType))
print inspect.isclass(LoopbackSelf), inspect.isclass(loop)

## HOWTO check python version
import sys
print sys.version_info, sys.hexversion, sys.version_info < (2,7), sys.version_info < (2,6)
