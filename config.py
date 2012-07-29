#!/usr/bin/python2

import json

filename = 'config.json'

default = {
		'server_memory': 512,
		'server_autostart': True,
}

cache = None

def get(*args):
	global cache
	if not cache:
		try:
			cache = json.load(open(filename))
		except:
			cache = default.copy()
	if len(args) == 1:
		return cache[args[0]]
	return cache

def set(cfg):
	global cache
	cache = cfg
	json.dump(cfg, open(filename, 'w'))

def update(**kwargs):
	upcfg = get()
	upcfg.update(kwargs)
	set(upcfg)
