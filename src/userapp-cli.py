#!/usr/bin/env python

import shutil
import json
import sys, os, stat
import readline
import ConfigParser
import userapp
import getpass
import webbrowser

class ConsoleHelper(object):
	@staticmethod
	def clear_console():
		os.system(['clear','cls'][os.name == 'nt'])

class ServiceLocator(object):
	_instance=None

	def __init__(self):
		self.registry={}

	def register(self, name, object):
		self.registry[name]=object

	def resolve(self, name):
		return self.registry[name] if name in self.registry else None

	@staticmethod
	def get_instance():
		if ServiceLocator._instance is None:
			ServiceLocator._instance=ServiceLocator()

		return ServiceLocator._instance

class Configuration(object):
	def __init__(self, selected_profile_name=None, profiles=None, file_path=None):
		self.__file_path=file_path
		self.selected_profile_name=selected_profile_name
		self.profiles={} if profiles is None else profiles

	@staticmethod
	def parseBooleanString(value):
		if isinstance(value, bool):
			return value

		if isinstance(value, basestring):
			return value.lower() in ['true', '1', 'yes', 'on']

		if isinstance(value, int):
			return value == 1

		return False

	def load(self):
		try:
			with open(self.__file_path, 'r') as handle:
				self.profiles = json.load(handle)['profiles']
		except:
			self.profiles={}

	def save(self):
		config_dir_path=os.path.dirname(self.__file_path)

		if not os.path.exists(config_dir_path):
			os.makedirs(config_dir_path)

		with open(self.__file_path, 'w') as handle:
			handle.write(str(self))

	def has_profile(self, name):
		return name in self.profiles

	def get_profile(self, name):
		if name in self.profiles:
			return self.profiles[name]

		new_profile=self.get_default_profile()
		self.profiles[name]=new_profile

		return new_profile

	def set_selected_profile(self, name):
		if self.has_profile(name):
			self.selected_profile_name=name

	def get_default_profile(self):
		return {
			'primary':True,
			'user':{
				'app_id':None,
				'token':None,
				'login':None,
				'password':None
			},
			'server':{
				'base_address':'api.userapp.io',
				'secure':True,
				'debug':False
			}
		}

	def get_primary_profile(self):
		for (name, profile) in self.profiles.items():
			if profile['primary']:
				return profile

		return self.get_default_profile()

	def get_selected_profile(self):
		if self.selected_profile_name is None:
			return self.get_primary_profile()

		if self.selected_profile_name in self.profiles:
			return self.profiles[self.selected_profile_name]

		return self.get_default_profile()

	def __str__(self):
		return json.dumps({'profiles':self.profiles}, sort_keys=True, indent=4)

	def __repr__(self):
		return str(self)

class CliCommandFactory(object):
	def __init__(self):
		self.cli_context=ServiceLocator.get_instance().resolve('cli_context')

	def create(self, arguments):
		command=InvalidCommand(arguments+[])

		if len(arguments) > 0:
			command_type=arguments.pop(0)

			if command_type == 'clear' or (len(arguments) > 0 and arguments[len(arguments)-1] == 'clear'):
				command=ClearConsoleCommand()
			elif command_type == 'config':
				command=ConfigCommand(arguments)
			elif command_type == 'profile':
				command=ProfileCommand(arguments)
			elif command_type == 'login':
				command=UserAppLoginCommand(arguments)
			elif command_type == 'register':
				command=UserAppRegisterCommand(arguments)
			elif command_type == 'call':
				if self.cli_context.is_interactive() and len(arguments) == 0 and not self.cli_context.in_scope(command_type):
					command=EnterScopeCommand([command_type])
				else:
					command=UserAppApiCallCommand(arguments)
			elif command_type == 'dashboard':
				command=UserAppDashboardLaunchCommand()
			elif command_type == 'install':
				command=InstallCommand()
			elif command_type == 'help':
				command=HelpCommand()

		return command

class UserAppApiCallCommand(object):
	def __init__(self, arguments):
		self.config=ServiceLocator.get_instance().resolve('config')

		self.service=None
		self.method=None
		self.parameters=None

		if len(arguments) > 0:
			call=arguments.pop(0)

			call_segments=call.split('.')
			self.method=call_segments.pop()
			self.service='.'.join(call_segments)

			if len(arguments) > 0:
				parameters={}

				for argument in arguments:
					param_segments=argument.split('=', 1)
					if len(param_segments) == 2:
						parameters[param_segments[0]]=param_segments[1]

				self.parameters=parameters

	def execute(self):
		profile=self.config.get_selected_profile()

		if profile['user']['token'] is None:
			print("(info) Not authenticated. Please login as user " + profile['user']['login'] + '.')
			UserAppLoginCommand([profile['user']['login']]).execute()

		client=userapp.Client(
			app_id=profile['user']['app_id'],
			token=profile['user']['token'],
			secure=profile['server']['secure'],
			base_address=profile['server']['base_address'],
			debug=profile['server']['debug']
		)

		try:
			result=client.call(1, self.service, self.method, self.parameters)
			print("(result) " + json.dumps(result, cls=userapp.IterableObjectEncoder, sort_keys=True, indent=4))
		except Exception, e:
			print("(error) " + str(e.message))

class ConfigCommand(object):
	def __init__(self, arguments):
		service_locator=ServiceLocator.get_instance()
		self.config=service_locator.resolve('config')
		self.cli_context=service_locator.resolve('cli_context')
		self.arguments=arguments

	def execute(self):
		arguments=self.arguments

		profile=self.config.get_selected_profile()

		def config_get_section(key):
			if key in ['app_id', 'token', 'login', 'password']:
				return 'user'

			if key in ['base_address', 'debug', 'secure']:
				return 'server'

			return None

		def config_exists(key):
			section=config_get_section(key)

			if section is None:
				return False

			return key in profile[section]

		def config_set(key, value):
			section=config_get_section(key)

			if section is None:
				return None

			profile[section][key]=value

		def config_get(key):
			section=config_get_section(key)

			if section is None:
				return None

			return profile[section][key]

		if len(arguments) > 0:
			command=arguments.pop(0)

			if command == 'list':
				result={}

				profile=self.config.get_selected_profile()

				for (key, value) in profile['user'].items():
					result[key]='' if value is None else value

				for (key, value) in profile['server'].items():
					result[key]='' if value is None else value

				print("(result) " + json.dumps(result, sort_keys=True, indent=4))
			elif command == 'get':
				if len(arguments) == 0:
					print("(error) Please specify a variable to get (debug, base_address, secure, app_id, token).")
				elif not config_exists(arguments[0]):
					print("(error) Invalid config variable '" + (arguments[0]) + "'.")
				else:
					current_value=config_get(arguments[0])

					if isinstance(current_value, bool):
						current_value='true' if current_value else 'false'

					if current_value is None:
						current_value = ''

					print("(result) " + current_value)
			elif command == 'set':
				if len(arguments) == 0:
					print("(error) Please specify a variable to set (debug, base_address, secure, app_id, token).")
				if len(arguments) != 2:
					print("(error) Please specify a value to set.")
				elif not config_exists(arguments[0]):
					print("(error) Invalid config variable '" + (arguments[0]) + "'.")
				else:
					new_value=arguments[1]
					current_value=config_get(arguments[0])
					
					if arguments[0] in ['debug', 'secure']:
						new_value=Configuration.parseBooleanString(new_value)

					config_set(arguments[0], new_value)

					print("(result) Changed config '"+arguments[0]+"' from '"+str(current_value)+"' to '"+str(new_value)+"'.")

					if not self.cli_context.is_interactive():
						self.config.save()
			elif command == 'save':
				self.config.save()
				print("(result) Configuration saved")
			else:
				print("(error) Please specify a command (list, get, set or save).")
		else:
			print("(error) Please specify a command (list, get, set or save).")

class InstallCommand(object):
	def __init__(self):
		pass

	def execute(self):
		try:
			source_file_path=os.path.abspath(sys.modules['__main__'].__file__)
			target_file_path='/usr/local/bin/userapp-cli'

			if source_file_path == target_file_path:
				print("(error) Already installed. Cannot install same file.")
			else:
				shutil.copy2(source_file_path, target_file_path)
				print("(result) Successfully installed. Now you can access the CLI using # userapp-cli")
		except Exception, e:
			print("(error) Error installing CLI. Please verify that you are sudo/have permissions to /usr/local/bin.")

class ProfileCommand(object):
	def __init__(self, arguments):
		service_locator=ServiceLocator.get_instance()
		self.config=service_locator.resolve('config')
		self.cli_context=service_locator.resolve('cli_context')
		self.arguments=arguments

	def execute(self):
		arguments=self.arguments

		profile=self.config.get_selected_profile()

		if len(arguments) > 0:
			command=arguments.pop(0)

			if command == 'list':
				print("(result) " + json.dumps(config.profiles.keys(), sort_keys=True, indent=4))
			elif command == 'current':
				profile_login=profile['user']['login']
				print("(result) " + ("No profile. Use 'login' or 'register' if you want to create a new profile." if profile_login is None else profile_login))
			elif command == 'switch':
				if len(arguments) == 0:
					print("(error) Please specify a profile to switch to. For valid profiles, try 'profile list'.")
				elif not self.config.has_profile(arguments[0]):
					print("(error) Invalid profile name '" + (arguments[0]) + "'.")
				else:
					name=arguments[0]

					if raw_input('Set as primary? ').lower() in ['yes', 'y']:
						profile['primary']=False
						profile=self.config.get_profile(name)
						profile['primary']=True
						self.config.save()

					self.config.set_selected_profile(name)
			else:
				print("(error) Please specify a command (list, current or switch).")
		else:
			print("(error) Please specify a command (list, current or switch).")

class HelpCommand(object):
	def __init__(self):
		pass

	def execute(self):
		print("Usage: userapp-cli [COMMAND] [OPTIONS] [OPTIONS...]")
		print("       userapp-cli signup john@doe.com mysecretpsw999")
		print("       userapp-cli login john@doe.com mysecretpsw999")
		print("       userapp-cli config list")
		print("       userapp-cli config get app_id")
		print("       userapp-cli config set app_id 123")
		print("       userapp-cli call")
		print("       userapp-cli call user.get")
		print("       userapp-cli call user.get user_id=abc")
		print("")
		print("COMMANDS")
		print("")
		print("  signup [email] [password]")
		print("    Sign up for a new UserApp account.")
		print("")
		print("  login [email] [password]")
		print("    Authenticate with UserApp and load your app id and token.")
		print("")
		print("  config list")
		print("    List all config variables.")
		print("")
		print("  config get <variable>")
		print("    Get a config variable. Available: app_id, token, base_address, secure, debug.")
		print("")
		print("  profile list")
		print("    List all profiles.")
		print("")
		print("  profile current")
		print("    Get the name of the current profile.")
		print("")
		print("  profile switch <name>")
		print("    Switch to another profile.")
		print("")
		print("  config set <variable> <value>")
		print("    Set a config variable.")
		print("")
		print("  call")
		print("    Enter the callable scope.")
		print("")
		print("  call <service>.<method>")
		print("    Call a UserApp API method. E.g. 'call user.login'.")
		print("")
		print("  call <service>.<method> variable=value other_var=other_val")
		print("    Call a UserApp API method with arguments. E.g. 'call user.login login=joe83 password=secretpsw999'.")
		print("")

class EnterScopeCommand(object):
	def __init__(self, arguments):
		self.arguments=arguments
		self.cli_context=ServiceLocator.get_instance().resolve('cli_context')

	def execute(self):
		for argument in self.arguments:
			self.cli_context.enter(argument)

class UserAppDashboardLaunchCommand(object):
	def __init__(self):
		self.config=ServiceLocator.get_instance().resolve('config')

	def execute(self):
		profile=self.config.get_selected_profile()
		
		if profile['user']['token'] is None:
			print("(info) Not authenticated. Please login as user " + profile['user']['login'] + '.')
			UserAppLoginCommand([profile['user']['login']]).execute()

		api=userapp.API(
			app_id=USERAPP_MASTER_APP_ID,
			secure=profile['server']['secure'],
			base_address=profile['server']['base_address'],
			debug=profile['server']['debug']
		)

		try:
			login_result=api.user.login(
				login=profile['user']['login'],
				password=profile['user']['password']
			)

			print("(result) Launching dashboard...")

			# Redirect stdout to devnull in order to avoid output from browser
			savout = os.dup(1)
			os.close(1)
			os.open(os.devnull, os.O_RDWR)

			try:
				webbrowser.open('https://app.userapp.io/#/?ua_token='+str(login_result.token))
			finally:
			   os.dup2(savout, 1)
		except Exception, e:
			print("(error) " + str(e.message))

class UserAppLoginCommand(object):
	def __init__(self, arguments=None):
		self.config=ServiceLocator.get_instance().resolve('config')

		self.email=None
		self.password=None

		if arguments is None:
			arguments=[]

		if len(arguments) > 0:
			self.email=arguments[0]

		if len(arguments) > 1:
			self.password=arguments[1]

	def execute(self):
		if self.email is None and self.password is None:
			print("Enter your UserApp credentials.")

		if self.email is None:
			self.email=raw_input('email: ')

		if self.password is None:
			self.password=getpass.getpass('password: ')

		profile=self.config.get_selected_profile()

		api=userapp.API(
			app_id=USERAPP_MASTER_APP_ID,
			secure=profile['server']['secure'],
			base_address=profile['server']['base_address'],
			debug=profile['server']['debug']
		)

		try:
			token=None
			token_identifier='UserApp CLI'

			login_result=api.user.login(login=self.email, password=self.password)

			app=api.app.get()
			tokens=api.token.search(fields='*')

			for item in tokens.items:
				if item.name == token_identifier:
					token=item.value

			if token is None:
				new_token=api.token.save(name=token_identifier, enabled=True)
				token=new_token.value

			profile=self.config.get_profile(self.email)

			profile['user']['primary']=False
			profile['user']['app_id']=app.app_id
			profile['user']['login']=self.email
			self.config.save()

			profile['user']['token']=token
			profile['user']['password']=self.password

			print("(result) Logged in as user " + login_result.user_id)

			if raw_input('Save credentials? ').lower() in ['yes', 'y', '']:
				self.config.save()

		except Exception, e:
			print(e.__dict__)
			print(e)
			print("(error) " + str(e.message))

class UserAppRegisterCommand(object):
	def __init__(self, arguments=None):
		self.config=ServiceLocator.get_instance().resolve('config')

		self.email=None
		self.password=None

		if arguments is None:
			arguments=[]

		if len(arguments) > 0:
			self.email=arguments[0]

		if len(arguments) > 1:
			self.password=arguments[1]

	def execute(self):
		if self.email is None and self.password is None:
			print("Create a new UserApp account.")

		if self.email is None:
			self.email=raw_input('email: ')

		if self.password is None:
			self.password=getpass.getpass('password: ')

			if self.password != getpass.getpass('retype same password: '):
				print("(error) Password did not match.")
				return

		profile=self.config.get_selected_profile()

		api=userapp.API(
			app_id=USERAPP_MASTER_APP_ID,
			secure=profile['server']['secure'],
			base_address=profile['server']['base_address'],
			debug=profile['server']['debug']
		)

		try:
			token=None
			token_identifier='UserApp CLI'

			signup_login=api.user.save(login=self.email, email=self.email, password=self.password)
			UserAppLoginCommand([self.email, self.password]).execute()

		except Exception, e:
			print("(error) " + str(e.message))

class ClearConsoleCommand(object):
	def __init__(self):
		pass

	def execute(self):
		ConsoleHelper.clear_console()

class InvalidCommand(object):
	def __init__(self, arguments):
		self.arguments=arguments

	def execute(self):
		print("(error) Invalid command '" + (' '.join(self.arguments)) + "'")

class NopCommand(object):
	def __init__(self):
		pass

	def execute(self):
		pass

class CliCommandParser(object):
	def __init__(self):
		pass

	def parse(self, raw):
		result = raw.split(' ')

		if len(result) == 1 and len(result[0]) == 0:
			result = []

		return result

class CliContext(object):
	def __init__(self):
		self.interactive=False
		self.scopes=[]

	def enter(self, scope):
		self.scopes.append(scope)

	def exit(self):
		return self.scopes.pop() if len(self.scopes) > 0 else None

	def get_scopes(self):
		return self.scopes

	def in_scope(self, scope):
		return self.scopes[len(self.scopes)-1] == scope if len(self.scopes) > 0 else False

	def set_interactive(self, mode):
		self.interactive=mode

	def is_interactive(self):
		return self.interactive

if not os.geteuid() == 0:
    sys.exit('(error) This script requires root.')

USERAPP_MASTER_APP_ID='51ded0be98035'

cli_context=CliContext()

config=Configuration(file_path='/etc/userapp/config.json')
config.load()

service_locator=ServiceLocator.get_instance()
service_locator.register('config', config)
service_locator.register('cli_context', cli_context)

command_factory=CliCommandFactory()

if len(sys.argv) == 1:
	ConsoleHelper.clear_console()

	cli_context.set_interactive(True)

	parser=CliCommandParser()

	while True:
		try:
			cli_scopes=cli_context.get_scopes()

			line=raw_input("userapp" + (' ' + (':'.join(cli_scopes)) if len(cli_scopes) > 0 else '') + "> ")

			arguments=parser.parse(line)

			command=command_factory.create(cli_scopes + arguments)
			command.execute()
		except KeyboardInterrupt:
			print(" ")
			if cli_context.exit() is None:
				break
else:
	try:
		arguments=sys.argv
		arguments.pop(0)

		command=command_factory.create(arguments)
		command.execute()
	except KeyboardInterrupt:
		print(" ")