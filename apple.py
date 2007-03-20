#!/usr/bin/env python
# 
# apple - Build distribution daemon
# Copyright (C) 2005 Jason Chu <jason@archlinux.org>
# 
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# 

import sys
#sys.path.append('/etc')
#import appleConfig
import os, os.path, datetime
# next two imports are for OptionParser
from copy import copy
from optparse import Option, OptionValueError, OptionParser
from pacbuild.apple import connect, rpc, package, misc

defaultConfig = "/etc/appleConfig.py"
appleConfig = {}

UMASK = 0

WORKDIR = "/"

MAXFD = 1024

if (hasattr(os, "devnull")):
   REDIRECT_TO = os.devnull
else:
   REDIRECT_TO = "/dev/null"

def createDaemon():
	"""Detach a process from the controlling terminal and run it in the
	background as a daemon.
	"""

	try:
		pid = os.fork()
	except OSError, e:
		raise Exception, "%s [%d]" % (e.strerror, e.errno)

	if (pid == 0):	# The first child.
		os.setsid()

		try:
			pid = os.fork()	# Fork a second child.
		except OSError, e:
			raise Exception, "%s [%d]" % (e.strerror, e.errno)

		if (pid == 0):	# The second child.
			os.chdir(WORKDIR)
			os.umask(UMASK)
		else:
			os._exit(0)	# Exit parent (the first child) of the second child.
	else:
		os._exit(0)	# Exit parent of the first child.

	import resource		# Resource usage information.
	maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
	if (maxfd == resource.RLIM_INFINITY):
		maxfd = MAXFD
  
	# Iterate through and close all file descriptors.
	for fd in range(0, maxfd):
		try:
			os.close(fd)
		except OSError:	# ERROR, fd wasn't open to begin with (ignored)
			pass

	os.open(REDIRECT_TO, os.O_RDWR)	# standard input (0)

	os.dup2(0, 1)			# standard output (1)
	os.dup2(0, 2)			# standard error (2)

	return(0)

def check_filename(option, opt, value):
	if os.path.isfile(value):
	    return os.path.abspath(value)
	else:
		raise OptionValueError("option %s: invalid filename" % opt)

class ExtendOption(Option):
	TYPES = Option.TYPES + ("filename",)
	TYPE_CHECKER = copy(Option.TYPE_CHECKER)
	TYPE_CHECKER["filename"] = check_filename

def createOptParser():
	usage = "usage: %prog [options]"
	description = "<fill in description here>"
	parser = OptionParser(usage = usage, description = description,
	                      option_class = ExtendOption)

	parser.add_option("-c", "--config", action = "store", type = "filename",
	                  dest = "config", default = defaultConfig,
	                  help = "use a different config than default (%s)" % defaultConfig)
	parser.add_option("-d", "--daemon", action = "store_true",
	                  dest = "daemon", default = False,
	                  help = "run as a daemon")
	return parser


def _main(argv=None):
	if argv is None:
		argv = sys.argv

	# instantiate parser object and set it loose
	parser = createOptParser()
	(opts, args) = parser.parse_args()

	# use results of parse_args to set things up
	configPath = opts.config
	if opts.daemon:
		createDaemon()
		pid = open('/var/run/apple.pid', 'w')
		pid.write('%s\n' % os.getpid())
		pid.close()

	execfile(configPath, appleConfig, appleConfig)

	connect(appleConfig['database'])
	package.packagedir = appleConfig['Packagedir']

	rpc.init()

	try:
		builderTimeout = datetime.timedelta(hours=1, minutes=5)
		while True:
			for i in package.getBuilds():
				if i.isStale(appleConfig['stalePackageTimeout']):
					i.unbuild()
			for i in misc.Builder.select():
				if (datetime.datetime.now() - i.lastBeat >= builderTimeout):
					misc.Builder.delete(i.id)
			rpc.process()
	except KeyboardInterrupt:
		pass

	return 0

if __name__ == "__main__":
	sys.exit(_main())
