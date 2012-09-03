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
		name = name.lower()
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
		name = name.lower()
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

class BanList(BaseList):
	def __init__(self, server):
		BaseList.__init__(self, server)
		self.filename = 'banned-players.txt'
		self.addcmd = 'ban'
		self.delcmd = 'pardon'
		self.printedname = 'Banned Users'
		self.search_regex = re.compile(r"^([^#\n].+?)\|.+$", re.M)
		self.delete_regex = "^%s\|.+\n"
		self.tpl = "%s|1970-01-01 00:00:00 +0000|Server|Forever|Banned by an operator.\n"

class BanIPList(BaseList):
	def __init__(self, server):
		BaseList.__init__(self, server)
		self.filename = 'banned-ips.txt'
		self.addcmd = 'ban-ip'
		self.delcmd = 'pardon-ip'
		self.printedname = 'Banned IPs'
		self.search_regex = re.compile(r"^([^#\n].+?)\|.+$", re.M)
		self.delete_regex = "^%s\|.+\n"
		self.tpl = "%s|1970-01-01 00:00:00 +0000|Server|Forever|Banned by an operator.\n"

class Lists:
	def __init__(self, server):
		self._server = server
		self.operators = OpList(server)
		self.whitelist = WhiteList(server)
		self.banned = BanList(server)
		self.banned_ips = BanIPList(server)
	
	def getall(self):
		return {
			"operators": self.operators.get(),
			"whitelist": self.whitelist.get(),
			"banned": self.banned.get(),
			"banned_ips": self.banned_ips.get(),
		}

	def get_user_info(self, username):
		username = username.lower()
		#if self._server.running():
		#	online = (username in self._server.connected_users())
		#else:
		#	online = False
		return {
			"operators": (username in self.operators.get()),
			"whitelist": (username in self.whitelist.get()),
			"banned": (username in self.banned.get()),
		#	"online": online,
		}
