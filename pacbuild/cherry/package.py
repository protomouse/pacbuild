# 
# pacbuild.cherry.package - Package specific code
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
# 

from sqlobject import *

class Package(SQLObject):
	name = StringCol(alternateID=True)
	repo = ForeignKey('Repo')
	packageArchs = MultipleJoin('PackageArch')

class PackageArch(SQLObject):
	applies = IntCol()
	arch = ForeignKey('Arch')
	package = ForeignKey('Package')
	packageInstances = MultipleJoin('PackageInstance')

class PackageInstance(SQLObject):
	packageArch = ForeignKey('PackageArch')
	pkgver = StringCol()
	pkgrel = StringCol()
	status = EnumCol(enumValues=('new', 'queued', 'building', 'build-error', 'dep-wait', 'freshend', 'verifying', 'accepted', 'invalid'))
	timestamp = DateTimeCol()
	log = StringCol()
	binary = StringCol()

	def _set_binary(self, value):
		self._SO_set_binary(value.encode('base64').replace('\n',''))
	def _get_binary(self):
		return self._SO_get_binary().decode('base64')

	source = StringCol()

	def _set_source(self, value):
		self._SO_set_source(value.encode('base64').replace('\n',''))
	def _get_source(self):
		return self._SO_get_source().decode('base64')

