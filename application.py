#!/usr/bin/python2

from flask import Flask
from flask import render_template
from flask import make_response
from flask import url_for
from flask import session
from flask import redirect
from flask import request
from flask import flash
from ftools import fname, fparms
from frontend import *
import properties as props
import server as mcserver
import os
import sys
import config
import signal
import urllib2
app = Flask(__name__)

@app.route('/status')
@app.route('/server')
@app.route('/server/<action>', methods=['GET', 'POST'])
@app.route('/')
def server(action=None):
	"Server"
	if 'username' not in session: return goto_login(fname(), fparms())
	if request.method == 'POST':
		if action == 'power':
			task = request.form.get('task')
			if task == 'start':
				if mcs.start():
					flash('Server started.', 'success')
				else:
					flash('Server already running.', 'info')
			elif task == 'stop':
				if mcs.stop():
					flash('Server stopped.', 'success')
				else:
					flash('Server not running.', 'info')
			elif task == 'restart':
				mcs.stop()
				if mcs.start():
					flash('Server restarted.', 'success')
				else:
					flash('Server did not start.', 'error')
		elif action == 'memory':
			memory = int(request.form.get('mem', 512))
			if 512 <= memory <= 64000:
				config.update(server_memory=memory)
				flash('Server memory updated. <span class="halflink" onclick="document.getElementById(\'restartform\').submit();">Restart</span> the server to apply your changes.', 'success')
			else:
				flash('Memory value out of range: %d.' % memory, 'error')
		elif action == 'autos':
			autostart = (request.form.get('auto') == 'on')
			flash('Server autostart %s.' % ('enabled' if autostart else 'disabled'), 'success')
			config.update(server_autostart=bool(autostart))
		return redirect(url_for('server'))
	info = mcs.info()
	mem = config.get('server_memory')
	autos = config.get('server_autostart')
	return render_template('server.html', navigation=get_navi(fname()), info=info, mem=mem, autos=autos)

@app.route('/properties', methods=['GET', 'POST'])
def properties():
	"Properties"
	if 'username' not in session: return goto_login(fname(), fparms())

	if request.method == 'POST':
		props.save(request.form)
		flash('Properties saved. <span class="halflink" onclick="document.getElementById(\'restartform\').submit();">Restart</span> the server to apply your changes.', 'success')
		return redirect(url_for('properties'))

	sproperties = []
	serverprops = props.load()
	for item in props.tpl:
		item['value'] = serverprops.get(item['key'], item['default'])
		sproperties.append(item)
	return render_template('properties.html', navigation=get_navi(fname()), properties=sproperties)

@app.route('/users')
@app.route('/users/<list>')
def users(name=None):
	"Users"
	if 'username' not in session: return goto_login(fname(), fparms())
	return render_template('base.html', navigation=get_navi(fname()))

# Skin proxy
@app.route('/skins/<username>.png')
def skins(username):
	if username != 'default':
		try:
			u = urllib2.urlopen('http://s3.amazonaws.com/MinecraftSkins/%s.png' % username)
			resp = make_response(u.read(), 200)
		except urllib2.HTTPError:
			resp = make_response(open('static/char.png').read())
	else:
		resp = make_response(open('static/char.png').read())
	resp.headers['Content-type'] = 'image/png'
	return resp

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
		u = urllib2.urlopen('http://s3.amazonaws.com/MinecraftDownload/launcher/minecraft_server.jar')
		f = open('mcs/minecraft_server.jar', 'w')
		f.write(u.read())
		f.close()
		print "\bDONE"

	# Server autostart (set in config)
	# Hack to get right process
	appname = open("/proc/%d/status" % os.getpid()).readline().split("\t")[1].strip()
	mcautostart = config.get('server_autostart')
	if appname != 'application.py':
		mcs = mcserver.Server()
		if mcautostart:
			mcs.start()

	app.debug = True
	app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
	app.run(host='0.0.0.0', port=5000)
