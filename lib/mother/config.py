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
from simpleparse.common import numbers, strings#, comments
from simpleparse.parser import Parser
from simpleparse.dispatchprocessor import *

declaration = r'''
	root       := statements

	statements := tsn, (statement, tsn)*
	statement  := (comment/keyval)

	<comment>  := '#', -'\n'*
	keyval     := identifier,ts,':',ts,value

	identifier := [a-zA-Z],[a-zA-Z0-9_]*
	value      := string_single_quote/string_double_quote/int/bool/dict

	bool       := 'True'/'False'	
	dict       := tsn,'{',statements,'}'

	<ts>       := [ \t]*
	<tsn>      := [ \t\n]*
'''


class ConfigProcessor(DispatchProcessor):
	string_single_quote = strings.StringInterpreter()
	int                 = numbers.IntInterpreter()

	def __init__(self, target):
		self.target = target

	def statements(self, (tag, start, stop, subtags), buffer):
		return dict([stmt[0] for stmt in dispatchList(self, subtags, buffer) if len(stmt) > 0])

	def statement(self, (tag, start, stop, subtags), buffer):
		return dispatchList(self, subtags, buffer)

	def keyval(self, (tag, start, stop, subtags), buffer):
		ident = dispatch(self, subtags[0], buffer)
		value = dispatch(self, subtags[1], buffer)

		return (ident, value)

	def identifier(self, tag, buffer):
		return getString(tag, buffer)

	def value(self, (tag, start, stop, subtags), buffer):
		return dispatch(self, subtags[0], buffer)

	def bool(self, tag, buffer):
		return getString(tag, buffer) == 'True'

	def dict(self, (tag, start, stop, subtags), buffer):
		return dispatchList(self, subtags, buffer)[0]


class Config(object):
	def __init__(self, filename):
		with open(filename) as f:
			content = f.read()

		parser = Parser(declaration)
		success, tree, nextChar =  parser.parse(content, processor=ConfigProcessor(self))
		if not success:
			raise Exception

		for k, v in tree[0].iteritems():
			setattr(self, k, v)
