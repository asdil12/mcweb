#!/usr/bin/python2

import time
import re

filename = 'mcs/server.properties'

tpl = [
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
	{'key': 'enable-command-block', 'type': 'bool', 'default': False,
		'desc': 'Enables Command-Blocks on the server.'},
	{'key': 'gamemode', 'type': 'enum', 'default': 0,
		'enum': [{'key': 0, 'value': 'Survival'}, {'key': 1, 'value': 'Creative'}, {'key': 2, 'value': 'Adventure'}],
		'desc': 'Defines the mode of gameplay.'},
	{'key': 'generate-structures', 'type': 'bool', 'default': True,
		'desc': 'Defines whether structures (such as NPC Villages) will be generated.'},
	{'key': 'generator-settings', 'type': 'string', 'default': '',
		'desc': 'The settings used to customize Superflat world generation.'},
	{'key': 'hardcore', 'type': 'bool', 'default': False,
		'desc': 'Permanently bann players if they die.'},
	{'key': 'level-name', 'type': 'string', 'default': 'world',
		'desc': 'The name of the world and it\'s folder.'},
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
	{'key': 'snooper-enabled', 'type': 'bool', 'default': True,
		'desc': 'Sends snoop data regularly to http://snoop.minecraft.net'},
	{'key': 'spawn-animals', 'type': 'bool', 'default': True,
		'desc': 'Determines if Animals will be able to spawn.'},
	{'key': 'spawn-monsters', 'type': 'bool', 'default': True,
		'desc': 'Determines if monsters will be spawned.'},
	{'key': 'spawn-npcs', 'type': 'bool', 'default': True,
		'desc': 'Determines if non-player characters (NPCs) will be spawned.'},
	{'key': 'spawn-protection', 'type': 'string', 'default': 16,
		'desc': 'Sets the radius of the spawn point protection.'},
	{'key': 'view-distance', 'type': 'string', 'default': 10, 'maxlength': 2,
		'desc': 'Sets the amount of world data the server sends the client, measured in chunks in each direction of the player. (3-15)'},
	{'key': 'white-list', 'type': 'bool', 'default': False,
		'desc': 'With a white list enabled, users not on the white list will be unable to connect. Ops are automatically white listed, and there is no need to add them to the whitelist.'},
]

regex_comment = re.compile(r"^#.*$", re.M)

def get_string(values):
	nproperties = []
	for item in tpl:
		if not values.has_key(item['key']): continue
		val = ('true' if values.get(item['key']) == 'on' else 'false') if item['type'] == 'bool' else values.get(item['key'])
		if item['type'] == 'string' and val == item['default'] == '': continue
		item['value'] = val
		nproperties.append("%(key)s=%(value)s" % item)
	nproperties_str = "#Minecraft server properties\n#%s\n#Generated by MCWeb\n" % time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
	nproperties_str += "\n".join(nproperties)
	return nproperties_str

def get_dict(cfgstr):
	cfgstr = regex_comment.sub('', cfgstr)
	cfgstr = cfgstr.strip("\n")
	cfgdict = {}
	for item in cfgstr.split("\n"):
		key, value = item.split("=")
		cfgdict[key] = value
	for item in tpl:
		if cfgdict.has_key(item['key']):
			if item['type'] == 'bool':
				cfgdict[item['key']] = (cfgdict[item['key']] == 'true')
	return cfgdict

def load():
	try:
		cfgs = open(filename).read()
		return get_dict(cfgs)
	except:
		return {}

def save(cfg):
	cfgs = get_string(cfg)
	open(filename, 'w').write(cfgs)
