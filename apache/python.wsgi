#!/usr/bin/python
import os
import sys

def main(project, path_to_parent, settings="settings"):
	settings_module = '.'.join([project, settings])
	os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
	import django.core.handlers.wsgi
	
	sys.path.append(path_to_parent)
	sys.path.append(os.path.join(path_to_parent, project))
	return django.core.handlers.wsgi.WSGIHandler()


parent         = lambda f: os.path.dirname(f)
appname        = os.path.basename(parent(parent(__file__)))
path_to_parent = parent(parent(parent(__file__)))
application    = main(appname, path_to_parent)