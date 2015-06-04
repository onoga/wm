import config
import os
import sys


if __name__ == '__main__':
	python = os.path.join(config.python_bin, 'pythonw')

	params = (
		python,
		os.path.join(config.project_path, 'scripts', 'gnue-forms.py'),
		'-s',
		config.server_url + '/forms/login.gfd',
	)

	os.execv(python, params)

