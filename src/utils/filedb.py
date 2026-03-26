'''
**********************************************************************
* Filename	: filedb.py
* Description : A simple file based database.
* Author	  : Cavon
* Brand	   : SunFounder
* E-mail	  : service@sunfounder.com
* Website	 : www.sunfounder.com
* Update	  : Cavon	2016-09-13	New release
**********************************************************************
'''

from pathlib import Path

current_dir_path = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = Path(f"{current_dir_path}/config")

class fileDB(object):
	"""A file based database.

	A file based database, read and write arguements in the specific file.
	"""
	def __init__(self, db=None):
		'''Init the db_file is a file to save the datas.'''

		# Check if db_file is defined
		if db != None:
			self.db = db
			
			if Path(db).is_file():
			    print(f"The db path provided:   {db}   exists and is a file.")
			else:
			    print(f"The db path provided:   {db}   doesn't exists and/or is not a file.")
			    print(f"Using:   {DEFAULT_CONFIG_PATH}   instead")
			    self.db = DEFAULT_CONFIG_PATH
		else:
			self.db = DEFAULT_CONFIG_PATH

	def get(self, name, default_value=None):
		"""Get value by data's name. Default value is for the arguemants do not exist"""
		try:
			conf = open(self.db,'r')
			lines=conf.readlines()
			conf.close()
			file_len=len(lines)-1
			flag = False
			# Find the arguement and set the value
			for i in range(file_len):
				if lines[i][0] != '#':
					if lines[i].split('=')[0].strip() == name:
						value = lines[i].split('=')[1].replace(' ', '').strip()
						flag = True
			if flag:
				return value
			else:
				print("Value not found in filedb")
				return default_value
		except Exception as e:
			print(f"Got error: {e}")		
			return default_value
	
	def set(self, name, value):
		"""Set value by data's name. Or create one if the arguement does not exist"""

		# Read the file
		conf = open(self.db,'r')
		lines=conf.readlines()
		conf.close()
		file_len=len(lines)-1
		flag = False
		# Find the arguement and set the value
		for i in range(file_len):
			if lines[i][0] != '#':
				if lines[i].split('=')[0].strip() == name:
					lines[i] = '%s = %s\n' % (name, value)
					flag = True
		# If arguement does not exist, create one
		if not flag:
			lines.append('%s = %s\n\n' % (name, value))

		# Save the file
		conf = open(self.db,'w')
		conf.writelines(lines)
		conf.close()
