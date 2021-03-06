import config
import os
import sys


if __name__ == '__main__':
	python = os.path.join(config.python_bin, 'python')

	params = (
		python,
		os.path.join(config.project_path, 'scripts', 'gnue-forms.py'),
		'-s --debug-level=sql',
		config.server_url + '/forms/login.gfd',
	)

	os.system("%s %s" % (python, ' '.join(params[1:])))
