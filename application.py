#!/usr/bin/python2

from flask import Flask
from flask import render_template
from flask import url_for
from flask import session
from flask import escape
from flask import redirect
from flask import request
import inspect
import time
app = Flask(__name__)

def fname():
	return inspect.stack()[1][3]

def parms(only=None, exclude=None, ignore='self'):
	"""Returns a dictionary of the calling functions
	   parameter names and values.

	   The optional arguments can be used to filter the result:

		   only           use this to only return parameters
						  from this list of names.

		   exclude        use this to return every parameter
						  *except* those included in this list
						  of names.

		   ignore         use this inside methods to ignore
						  the calling object's name. For
						  convenience, it ignores 'self'
						  by default.
	"""
	args, varargs, varkw, defaults = inspect.getargvalues(inspect.stack()[1][0])
	if only is None:
		only = args[:]
		if varkw:
			only.extend(defaults[varkw].keys())
			defaults.update(defaults[varkw])
	if exclude is None:
		exclude = []
	exclude.append(ignore)
	return dict([(attrname, defaults[attrname])
		for attrname in only if attrname not in exclude])

def get_navi(active=None):
	navigation_tabs = [
		'status',
		'properties',
		'login'
	]
	if 'username' in session:
		navigation_tabs = ['logout' if t == 'login' else t for t in navigation_tabs]
	navigation = []
	for item in navigation_tabs:
		try:
			title = eval(item).__doc__ or item
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

@app.route('/status')
@app.route('/')
def status():
	"Status"
	if 'username' not in session: return goto_login(fname(), parms())
	return render_template('base.html', navigation=get_navi(fname()))

@app.route('/properties', methods=['GET', 'POST'])
def properties():
	"Properties"
	if 'username' not in session: return goto_login(fname(), parms())
	properties_tpl = [
		{'key': 'allow-flight', 'type': 'bool', 'default': False,
			'desc': 'Allows users to use flight on your server while in Survival mode, if they have a mod that provides flight installed.'},
		{'key': 'allow-nether', 'type': 'bool', 'default': True,
			'desc': 'Allows Portals to send players to the Nether.'},
		{'key': 'difficulty', 'type': 'enum', 'default': 1,
			'enum': [{'key': 0, 'value': 'Peaceful'}, {'key': 1, 'value': 'Easy'}, {'key': 2, 'value': 'Normal'}, {'key': 3, 'value': 'Hard'}],
			'desc': 'Defines the difficulty (such as damage dealt by mobs and the way hunger and poison affects players) of the server.'},
		{'key': 'enable-query', 'type': 'bool', 'default': False,
			'desc': 'Enables GameSpy4 protocol server listener. Used to get information about server.'},
		{'key': 'enable-rcon', 'type': 'bool', 'default': False,
			'desc': 'Enables remote access to the server console.'},
		{'key': 'gamemode', 'type': 'enum', 'default': 0,
			'enum': [{'key': 0, 'value': 'Survival'}, {'key': 1, 'value': 'Creative'}, {'key': 2, 'value': 'Adventure'}],
			'desc': 'Defines the mode of gameplay.'},
		{'key': 'generate-structures', 'type': 'bool', 'default': True,
			'desc': 'Defines whether structures (such as NPC Villages) will be generated.'},
		{'key': 'level-seed', 'type': 'string', 'default': '',
			'desc': 'Seed for your world, as in Singleplayer.'},
		{'key': 'level-type', 'type': 'enum', 'default': 'DEFAULT',
			'enum': [
				{'key': 'DEFAULT', 'value': 'Standard', 'hint': 'Standard world with hills, valleys, water, etc.'},
				{'key': 'FLAT', 'value': 'Flat', 'hint': 'A flat world with no features, meant for building.'},
				{'key': 'LARGEBIOMES', 'value': 'Large Biomes', 'hint': 'Same as default but all biomes are larger.'}
			], 'hidekey': True,
			'desc': 'Defines the mode of gameplay.'},
		{'key': 'max-build-height', 'type': 'string', 'default': 256,
			'desc': 'The maximum height in which building is allowed.'},
		{'key': 'max-players', 'type': 'string', 'default': 20,
			'desc': 'The maximum number of players that can play on the server at the same time.'},
		{'key': 'motd', 'type': 'string', 'default': 'A Minecraft Server', 'maxlength': 59,
			'desc': 'This is the message that is displayed in the server list of the client, below the name.'},
		{'key': 'texture-pack', 'type': 'string', 'default': '',
			'desc': 'Server prompts client to download texture pack upon join. Put web url link to the texture pack you want players on your server to download in this space.'},
		{'key': 'online-mode', 'type': 'bool', 'default': True,
			'desc': 'Server checks connecting players against minecraft\'s account database.'},
		{'key': 'pvp', 'type': 'bool', 'default': True,
			'desc': 'Allow players to kill each other.'},
		{'key': 'query.port', 'type': 'string', 'default': 25565,
			'desc': 'Sets the port for the query server (see enable-query).'},
		{'key': 'rcon.password', 'type': 'string', 'default': '',
			'desc': 'Sets the password to rcon.'},
		{'key': 'rcon.port', 'type': 'string', 'default': 25575,
			'desc': 'Sets the port to rcon.'},
		{'key': 'server-ip', 'type': 'string', 'default': '',
			'desc': 'Set this if you want the server to bind to a particular IP. It is strongly recommended that you leave server-ip blank!'},
		{'key': 'server-port', 'type': 'string', 'default': 25565,
			'desc': 'Changes the port the server is hosting on. This port must be forwarded if the server is going through a router.'},
		{'key': 'spawn-animals', 'type': 'bool', 'default': True,
			'desc': 'Determines if Animals will be able to spawn.'},
		{'key': 'spawn-monsters', 'type': 'bool', 'default': True,
			'desc': 'Determines if monsters will be spawned.'},
		{'key': 'spawn-npcs', 'type': 'bool', 'default': True,
			'desc': 'Determines if non-player characters (NPCs) will be spawned.'},
		{'key': 'view-distance', 'type': 'string', 'default': 10, 'maxlength': 2,
			'desc': 'Sets the amount of world data the server sends the client, measured in chunks in each direction of the player. (3-15)'},
		{'key': 'white-list', 'type': 'bool', 'default': False,
			'desc': 'With a white list enabled, users not on the white list will be unable to connect. Ops are automatically white listed, and there is no need to add them to the whitelist.'},
	]
	sproperties = []
	for item in properties_tpl:
		item['value'] = item['default']
		sproperties.append(item)

	if request.method == 'POST':
		nproperties = []
		for item in properties_tpl:
			val = ('true' if request.form.get(item['key']) == 'on' else 'false') if item['type'] == 'bool' else request.form.get(item['key'])
			item['value'] = val
			if item['type'] != 'string' or val != '':
				nproperties.append("%(key)s=%(value)s" % item)
		nproperties_str = "#Minecraft server properties\n#%s\n#Generated by MCWeb\n" % time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
		nproperties_str += "\n".join(nproperties)
		return "<pre>\n%s\n</pre>" % nproperties_str
	return render_template('properties.html', navigation=get_navi(fname()), properties=sproperties)

@app.route('/lists/')
@app.route('/lists/<name>')
def hello(name=None):
	if 'username' not in session: return goto_login(fname(), parms())
	return render_template('base.html', navigation=get_navi(fname()))

# Login / Logout
@app.route('/login', methods=['GET', 'POST'])
def login():
	"Login"
	if request.method == 'POST':
		funcname = session.pop('fname', 'status')
		args = session.pop('args', {})
		session['username'] = 'tux'
		return redirect(url_for(funcname, **args))
	return render_template('login.html', navigation=get_navi(fname()))

@app.route('/logout')
def logout():
	"Logout"
	session.pop('username', None)
	return redirect(url_for('status'))

if __name__ == '__main__':
	app.debug = True
	app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
	app.run()
