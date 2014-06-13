import os
import urllib
import shutil
import zipfile
import webbrowser
import subprocess

class ConsoleHelper(object):
	@staticmethod
	def clear_console():
		os.system(['clear','cls'][os.name == 'nt'])

class WebBrowserHelper(object):
	@staticmethod
	def open_url(url):
		# Redirect stdout to devnull in order to avoid output from browser
		savout = os.dup(1)
		os.close(1)
		os.open(os.devnull, os.O_RDWR)

		try:
			webbrowser.open(url)
		finally:
		   os.dup2(savout, 1)

class ProcessHelper(object):
	@staticmethod
	def execute(args, wait=True, block=True, cwd=None):
		print(cwd)

		if block:
			process = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, cwd=cwd)
		else:
			process = subprocess.Popen(args, shell=True, cwd=cwd)

		if wait:
			process.wait()

		return process.returncode

class FileHelper(object):
	@staticmethod
	def unzip_url(source_url, target_dir):
		"""
		Download an unzip and url in a target directory. Returns None if successful.
		"""
		if not os.path.exists(target_dir):
			os.makedirs(target_dir)

		name = os.path.join(target_dir, 'stage.tmp')
		
		try:
			name, hdrs = urllib.urlretrieve(source_url, name)
		except IOError, e:
			return 'invalid_url'

		try:
			with zipfile.ZipFile(name) as handle:
				handle.extractall(target_dir)

			os.unlink(name)
		except zipfile.error, e:
			return 'invalid_zip'

		return None

	@staticmethod
	def search_replace_file(file_path, pattern, replace_with):
		fh, abs_path = tempfile.mkstemp()

		with open(abs_path,'w') as new_file:
			with open(file_path) as old_file:
				for line in old_file:
					if pattern in line:
						line=line.replace(pattern, replace_with)
					new_file.write(line)

		os.close(fh)
		os.remove(file_path)
		shutil.move(abs_path, file_path)