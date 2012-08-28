#!/usr/bin/python2

import os
import re

class BaseList:
	def __init__(self, server):
		self.server = server
		self.filename = None
		self.search_regex = re.compile(r"^([^#].*)$", re.M)
		self.delete_regex = "^%s\n"
		self.addcmd = None
		self.delcmd = None
		self.tpl = "%s\n"
		self.printedname = None

	def get(self):
		listfile = os.path.join('mcs', self.filename)
		if os.path.isfile(listfile):
			return self.search_regex.findall(open(listfile).read())
		else:
			return []
	
	def add(self, name):
		if name in self.get():
			return False
		else:
			if self.server.running() and self.addcmd:
				self.server.cmd('%s %s' % (self.addcmd, name))
			else:
				listfile = os.path.join('mcs', self.filename)
				open(listfile, 'a').write(self.tpl % name)
			return True

	def remove(self, name):
		if name not in self.get():
			return False
		else:
			if self.server.running() and self.delcmd:
				self.server.cmd('%s %s' % (self.delcmd, name))
			else:
				listfile = os.path.join('mcs', self.filename)
				listcontent = open(listfile).read()
				listcontent = re.sub(self.delete_regex % re.escape(name), '', listcontent, flags=re.M)
				open(listfile, 'w').write(listcontent)
			return True

class OpList(BaseList):
	def __init__(self, server):
		BaseList.__init__(self, server)
		self.filename = 'ops.txt'
		self.addcmd = 'op'
		self.delcmd = 'deop'
		self.printedname = 'Game Operators'

class WhiteList(BaseList):
	def __init__(self, server):
		BaseList.__init__(self, server)
		self.filename = 'white-list.txt'
		self.printedname = 'White-List'

class Lists:
	def __init__(self, server):
		self.operators = OpList(server)
		self.whitelist = WhiteList(server)
	
	def getall(self):
		return {
			"operators": self.operators.get(),
			"whitelist": self.whitelist.get(),
		}
