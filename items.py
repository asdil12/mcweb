#!/usr/bin/python2

import csv

filename = 'items.csv'

cache = None

def get():
	global cache
	if not cache:
		cache = []
		i = 0
		for row in csv.reader(open('items.csv', 'r'), delimiter=';'):
			cache.append({
				'index': i,
				'id': row[0],
				'name': row[1],
			})
			i += 1
	return cache

def get_by_id(dataid):
	try:
		lst = get()
		index = next(index for (index, d) in enumerate(lst) if d["id"] == dataid)
		return lst[index]
	except StopIteration:
		raise KeyError
