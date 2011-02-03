#!/usr/bin/env python
# -*- coding: utf8 -*-

from odict import odict
from twisted.web2 import http_headers

# BUG dans MimeType.__ne__
#    def __ne__(self, other):
#	        if not isinstance(other, MimeType): return NotImplemented
#	        return not self.__eq__(other)
def myneq(self, other):
	if not isinstance(other, http_headers.MimeType): return NotImplemented

	return not (self.mediaType == other.mediaType and
		self.mediaSubtype == other.mediaSubtype and
		self.params == other.params)


class mydict(odict):
	def __init__(self, _iter):
		l = list(_iter)
		for mime, weight in l:
			setattr(mime, '__ne__', myneq)
		odict.__init__(self, l)

# hot-patching MimeType class
http_headers.MimeType.__ne__ = myneq
# //

head = http_headers.Headers(handler=http_headers.DefaultHTTPHandler)
head.setRawHeaders('accept',['text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8,application/json',])
head.handler.updateParsers({'Accept':(http_headers.tokenize, http_headers.listParser(http_headers.parseAccept), mydict)})
print head._toParsed('accept')
