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
from simpleparse.common import numbers, strings, comments
from simpleparse.parser import Parser
from simpleparse.dispatchprocessor import *

declaration = r'''
	root       := [ \t\n]*, statement*
	statement  := nullline/keyval
	nullline   := ts, '\n'
	keyval     := ts,identifier,ts,':',ts,value,ts,'\n'
	identifier := [a-zA-Z0-9_]+
	value      := '\'', [a-zA-Z-_0-9/.]+, '\''
	ts         := [ \t]*
'''


class ConfigProcessor(DispatchProcessor):
	def __init__(self, target):
		self.target = target

	def statement(self, (tag, start, stop, subtags), buffer):
		dispatchList(self, subtags, buffer)

	def nullline(self, tag, buffer):
		pass

	def keyval(self, (tag, start, stop, subtags), buffer):
		ident = dispatch(self, subtags[1], buffer)
		value = dispatch(self, subtags[4], buffer)
		
		setattr(self.target, ident, value)

	def identifier(self, tag, buffer):
		return getString(tag, buffer)

	def value(self, tag, buffer):
		return getString(tag, buffer)[1:-1]

class Config(object):
	def __init__(self, filename):
		with open(filename) as f:
			content = f.read()

		parser = Parser(declaration)
		success, tree, nextChar =  parser.parse(content, processor=ConfigProcessor(self))
		if not success:
			raise Exception
