#!/usr/bin/python2

import config
import hashlib

def _hash(string):
	return hashlib.sha1(string.encode('UTF-8')).hexdigest()

def set(name, password):
	admin_accounts = config.get('admin_accounts')
	admin_accounts[name] = _hash(password)
	config.update(admin_accounts=admin_accounts)

def remove(name):
	admin_accounts = config.get('admin_accounts')
	if name not in admin_accounts:
		return False
	else:
		del admin_accounts[name]
		config.update(admin_accounts=admin_accounts)
		return True

def list():
	return [i for i in config.get('admin_accounts').keys()]

def auth(name, password):
	admin_accounts = config.get('admin_accounts')
	if name in admin_accounts:
		if admin_accounts[name] == _hash(password):
			return True
	return False
