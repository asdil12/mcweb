#!/usr/bin/python2

from flask import Flask
from flask import render_template
from flask import url_for
from flask import session
from flask import redirect
from flask import request
from ftools import fname, fparms
from frontend import *
import properties as props
import server as mcs
import os
import sys
app = Flask(__name__)

@app.route('/status')
@app.route('/server')
@app.route('/')
def server():
	"Server"
	if 'username' not in session: return goto_login(fname(), fparms())
	info = mcs.info()
	return render_template('base.html', navigation=get_navi(fname()))

@app.route('/properties', methods=['GET', 'POST'])
def properties():
	"Properties"
	if 'username' not in session: return goto_login(fname(), fparms())

	if request.method == 'POST':
		return "<pre>\n%s\n</pre>" % props.get_string(request.form)

	sproperties = []
	for item in props.tpl:
		item['value'] = item['default']
		sproperties.append(item)
	return render_template('properties.html', navigation=get_navi(fname()), properties=sproperties)

@app.route('/lists/')
@app.route('/lists/<name>')
def hello(name=None):
	if 'username' not in session: return goto_login(fname(), fparms())
	return render_template('base.html', navigation=get_navi(fname()))

# Login / Logout
@app.route('/login', methods=['GET', 'POST'])
def login():
	"Login"
	if request.method == 'POST':
		funcname = session.pop('fname', 'server')
		args = session.pop('args', {})
		session['username'] = 'tux'
		return redirect(url_for(funcname, **args))
	return render_template('login.html', navigation=get_navi(fname()))

@app.route('/logout')
def logout():
	"Logout"
	session.pop('username', None)
	return redirect(url_for('server'))

if __name__ == '__main__':
	if not os.path.isfile('mcs/minecraft_server.jar'):
		print "Downloading minecraft_server.jar ... ",
		sys.stdout.flush()
		import urllib2
		u = urllib2.urlopen('http://s3.amazonaws.com/MinecraftDownload/launcher/minecraft_server.jar')
		f = open('mcs/minecraft_server.jar', 'w')
		f.write(u.read())
		f.close()
		print "DONE"
	app.debug = True
	app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
	app.run()
