import os
import json

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