#!/usr/bin/python2

from flask import Flask
from flask import Markup
from flask import render_template
from flask import make_response
from flask import url_for
from flask import session
from flask import redirect
from flask import request
from flask import flash
from flask import jsonify
from ftools import fname, fparms
from frontend import *

import config
import items
import properties as props
import server as mcserver
import admin as webadm
from lists import Lists as UserLists

import os
import sys
import signal
import urllib2
import json

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
		elif action == 'update':
			old_version = mcs.get_version()
			update_server_binary()
			new_version = mcs.get_version()
			if old_version != new_version:
				flash('Server updated. <span class="halflink" onclick="document.getElementById(\'restartform\').submit();">Restart</span> the server to apply your changes.', 'success')
			else:
				flash('Server version unchanged. You already have the current version.', 'info')
		elif action == 'announce':
			message = request.form.get('message').replace("\n", '')
			try:
				mcs.cmd('say %s' % message)
				flash('Announcement sent.', 'success')
			except mcserver.NotRunning:
				flash('Announcement impossible when server is not running.', 'error')
		elif action == 'timeset':
			newtime = int(request.form.get('time', '1')) % 24000
			try:
				mcs.cmd('time set %d' % newtime)
				flash('Time set to value <i>%s</i>.' % newtime, 'success')
			except mcserver.NotRunning:
				flash('Time setting impossible when server is not running.', 'error')
		return redirect(url_for('server'))
	info = mcs.info()
	mem = config.get('server_memory')
	autos = config.get('server_autostart')
	username = request.args.get('username', 'default')
	mcs.prepare_nbt()
	return render_template('server.html', navigation=get_navi(fname()), info=info, mem=mem, autos=autos, username=username, servertime=mcs.get_time())

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

@app.route('/users', methods=['GET', 'POST'])
def users():
	"Users"
	if 'username' not in session: return goto_login(fname(), fparms())
	if request.method == 'POST':
		username = request.form.get('name')
		if username:
			return redirect(url_for('user_details', username=request.form.get('name')))
		else:
			return redirect(url_for('users'))
	info = mcs.info()
	return render_template('users.html', navigation=get_navi(fname()), info=info)

@app.route('/users/<username>')
def user_details(username):
	if 'username' not in session: return goto_login(fname(), fparms())
	user_info = userlists.get_user_info(username, check_online=True)
	items_json = {}
	for item in items.get():
		items_json[item['id']] = item['name']
	items_json = json.dumps(items_json)
	mcs.prepare_nbt()
	try:
		pxp = mcs.get_player_xp(username)
	except mcserver.NBT_IO_Exception:
		pxp = None
	return render_template('user_details.html', navigation=get_navi('users'), info=user_info, name=username, items=items.get(), items_json=items_json, pxp=pxp)

@app.route('/user', methods=['GET', 'POST'])
def user_action():
	if 'username' not in session: return goto_login(fname(), fparms())
	if request.method == 'GET':
		return redirect(url_for('users'))
	elif request.method == 'POST':
		username = request.form.get('username')
		action = request.form.get('action')
		try:
			if action == 'kick':
				mcs.cmd('kick %s' % username)
				flash('<i>%s</i> kicked.' % Markup.escape(username), 'success')
			elif action == 'tell':
				message = request.form.get('message')
				mcs.cmd('tell %s %s' % (username, message))
				flash('Message sent to <i>%s</i>.' % Markup.escape(username), 'success')
			elif action == 'xp':
				try:
					amount = int(request.form.get('amount'))
					if not 0 < amount <= 5000:
						raise ValueError
					mcs.cmd('xp %s %s' % (amount, username))
					flash('Gave %d XP\'s to <i>%s</i>.' % (amount, Markup.escape(username)), 'success')
				except ValueError:
					flash('Amount of XP\'s out of range of 1 - 5000.', 'error')
			elif action == 'teleport':
				try:
					target = request.form.get('target')
					if target == 'user':
						destuser = request.form.get('destuser')
						if userlists.get_user_info(destuser, check_online=True)['online']:
							mcs.cmd('tp %s %s' % (username, destuser))
							flash('Teleported <i>%s</i> to <i>%s</i>.' % (Markup.escape(username), Markup.escape(destuser)), 'success')
						else:
							flash('Destination user <i>%s</i> is not online.' % Markup.escape(destuser), 'error')
					elif target == 'position':
						x = int(request.form.get('dest_x'))
						y = int(request.form.get('dest_y'))
						z = int(request.form.get('dest_z'))
						mcs.cmd('tp %s %d %d %d' % (username, x, y, z))
						flash('Teleported <i>%s</i> to x:<i>%d</i>, y:<i>%d</i>, z:<i>%d</i>.' % (Markup.escape(username), x, y, z), 'success')
						# server needs some time to answer after tp
				except ValueError:
					flash('Invalid target position.', 'error')
			elif action == 'give':
				try:
					amount = int(request.form.get('amount'))
					itemid = request.form.get('itemid')
					if not 0 < amount <= 64:
						raise ValueError
					if itemid.find(':') != -1:
						item, data = itemid.split(':')
						mcs.cmd('give %s %d %d %d' % (username, int(item), amount, int(data)))
					else:
						mcs.cmd('give %s %d %d' % (username, int(itemid), amount))
					try:
						itemname = items.get_by_id(itemid)['name']
					except KeyError:
						itemname = idemid
					flash('Gave %d <i>%s</i> to <i>%s</i>.' % (amount, Markup.escape(itemname), Markup.escape(username)), 'success')
				except ValueError:
					flash('Amount of item\'s out of range of 1 - 64.', 'error')
		except mcserver.NotRunning:
			flash('User interaction impossible when server is not running.', 'error')
		returnpage = request.form.get('returnpage', 'user_details')
		return redirect(url_for(returnpage, username=username))

@app.route('/_users/<name>')
def users_json(name):
	if 'username' not in session: return goto_login(fname(), fparms())
	return jsonify(**userlists.get_user_info(name))

@app.route('/lists')
def lists():
	"Lists"
	if 'username' not in session: return goto_login(fname(), fparms())
	return render_template('lists.html', navigation=get_navi(fname()), userlists=userlists.getall())

@app.route('/lists/')
@app.route('/lists/<name>', methods=['GET', 'POST'])
def lists_edit(name=None):
	if 'username' not in session: return goto_login(fname(), fparms())
	action = 'delete' if request.args.get('action', request.form.get('action')) == 'delete' else 'add'
	item = request.args.get('item', request.form.get('item'))
	if not name or not action or not item:
		return redirect(url_for('lists'))
	listname = getattr(userlists, name).printedname
	if request.method == 'POST':
		if name == 'whitelist':
			restartstring = '<span class="halflink" onclick="document.getElementById(\'restartform\').submit();">Restart</span> the server to apply your changes.'
		else:
			restartstring = ''
		if action == 'add':
			if getattr(userlists, name).add(item):
				flash('<i>%s</i> added to %s. %s' % (Markup.escape(item), listname, restartstring), 'success')
			else:
				flash('<i>%s</i> is already in %s.' % (Markup.escape(item), listname), 'info')
		elif action == 'delete':
			if getattr(userlists, name).remove(item):
				flash('<i>%s</i> deleted from %s. %s' % (Markup.escape(item), listname, restartstring), 'success')
			else:
				flash('<i>%s</i> is not in %s.' % (Markup.escape(item), listname), 'info')
		returnpage = request.form.get('returnpage', 'lists')
		return redirect(url_for(returnpage, username=item))
	return render_template('lists_delete.html', navigation=get_navi('lists'), name=name, action=action, item=item, listname=listname)

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

@app.route('/admins', methods=['GET', 'POST'])
def admins():
	"Admins"
	if request.method == 'POST':
		return redirect(url_for('admins_edit', name=request.form.get('newname')))
	admin_list = webadm.list()
	return render_template('admins.html', navigation=get_navi(fname()), admin_list=admin_list)

@app.route('/admins/')
@app.route('/admins/<name>', methods=['GET', 'POST'])
def admins_edit(name=None):
	action = 'delete' if request.args.get('action', request.form.get('action')) == 'delete' else 'edit'
	if 'username' not in session: return goto_login(fname(), fparms())
	if not name:
		return redirect(url_for('admins'))
	if request.method == 'POST':
		if action == 'edit':
			password = request.form.get('new_password')
			if password:
				webadm.set(name, password)
				flash('User <i>%s</i> updated.' % Markup.escape(name), 'success')
			else:
				flash('Password must not be empty.', 'error')
				return redirect(url_for('admins_edit', name=name))
		elif action == 'delete':
			if len(webadm.list()) == 1:
				flash('You can\'t delete the last user.', 'error')
				return redirect(url_for('admins'))
			webadm.remove(name)
			flash('User <i>%s</i> deleted.' % Markup.escape(name), 'success')
		return redirect(url_for('admins'))
	return render_template('admins_edit.html', navigation=get_navi('admins'), admin=name, action=action)

# Login / Logout
@app.route('/login', methods=['GET', 'POST'])
def login():
	"Login"
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		if webadm.auth(username, password):
			funcname = session.pop('fname', 'server')
			args = session.pop('args', {})
			session['username'] = username
			flash('Login successfull.', 'success')
			return redirect(url_for(funcname, **args))
		else:
			flash('Login failed.', 'error')
	return render_template('login.html', navigation=get_navi(fname()))

@app.route('/logout')
def logout():
	"Logout"
	session.pop('username', None)
	return redirect(url_for('server'))

def update_server_binary():
	u = urllib2.urlopen('http://s3.amazonaws.com/MinecraftDownload/launcher/minecraft_server.jar')
	f = open('mcs/minecraft_server.jar', 'w')
	f.write(u.read())
	f.close()

if __name__ == '__main__':
	if not os.path.isfile('mcs/minecraft_server.jar'):
		print "Downloading minecraft_server.jar ... ",
		sys.stdout.flush()
		update_server_binary()
		print "\bDONE"

	# Server autostart (set in config)
	# Hack to get right process
	appname = open("/proc/%d/status" % os.getpid()).readline().split("\t")[1].strip()
	mcautostart = config.get('server_autostart')
	if appname != 'application.py':
		mcs = mcserver.Server()
		if mcautostart:
			mcs.start()
		userlists = UserLists(mcs)

	app.debug = True
	app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
	app.run(host='0.0.0.0', port=5000)
