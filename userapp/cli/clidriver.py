import os
import sys
import atexit
import readline
import rlcompleter

from core import Configuration
from core import ServiceLocator
from helper import ConsoleHelper
from command import CliCommandParser
from command import CliCommandFactory

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

def main():
	cli_context=CliContext()

	historyPath = os.path.expanduser("~/.uahistory")

	def save_history(historyPath=historyPath):
	    import readline
	    readline.write_history_file(historyPath)

	if os.path.exists(historyPath):
	    readline.read_history_file(historyPath)

	atexit.register(save_history)

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

	return 0