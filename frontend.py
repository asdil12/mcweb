#!/usr/bin/python2

from flask import session, redirect, url_for
import application

def get_navi(active=None):
	navigation_tabs = [
		'server',
		'properties',
		'users',
		'login'
	]
	if 'username' in session:
		navigation_tabs = ['logout' if t == 'login' else t for t in navigation_tabs]
	navigation = []
	for item in navigation_tabs:
		try:
			title = getattr(application, item).__doc__ or item
		except:
			title = item
		navigation.append({
			'name': item,
			'title': title + ' [%s]' % session['username'] if item == 'logout' else title,
			'active': (item == active),
			'args': {}
		})
	return navigation

def goto_login(fname, args={}):
	session['fname'] = fname
	session['args'] = args
	return redirect(url_for('login'))
