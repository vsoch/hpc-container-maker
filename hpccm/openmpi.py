# Copyright (c) 2018, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Documentation TBD"""

from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import
import os
import re

from .apt_get import apt_get
from .comment import comment
from .ConfigureMake import ConfigureMake
from .copy import copy
from .environment import environment
from .shell import shell
from .tar import tar
from .toolchain import toolchain
from .wget import wget

class openmpi(ConfigureMake, tar, wget):
    """Documentation TBD"""

    def __init__(self, **kwargs):
        """Documentation TBD"""

        # Trouble getting MRO with kwargs working correctly, so just call
        # the parent class constructors manually for now.
        #super(openmpi, self).__init__(**kwargs)
        ConfigureMake.__init__(self, **kwargs)
        tar.__init__(self, **kwargs)
        wget.__init__(self, **kwargs)

        self.baseurl = kwargs.get('baseurl',
                                  'https://www.open-mpi.org/software/ompi')
        self.__check = kwargs.get('check', False)
        self.configure_opts = kwargs.get('configure_opts',
                                         ['--disable-getpwuid',
                                          '--enable-orterun-prefix-by-default'])
        self.cuda = kwargs.get('cuda', True)
        self.directory = kwargs.get('directory', '')
        self.infiniband = kwargs.get('infiniband', True)
        self.ospackages = kwargs.get('ospackages',
                                     ['file', 'hwloc', 'openssh-client',
                                      'wget'])
        self.prefix = kwargs.get('prefix', '/usr/local/openmpi')
        # TODO: distinguish between the build toolchain (input) and the
        # resulting OMPI toolchain (output), e.g., CC=mpicc
        self.toolchain = kwargs.get('toolchain', toolchain())
        self.version = kwargs.get('version', '3.0.0')

        self.__commands = [] # Filled in by __setup()
        self.__environment_variables = {
            'PATH': '{}:$PATH'.format(os.path.join(self.prefix, 'bin')),
            'LD_LIBRARY_PATH':
            '{}:$LD_LIBRARY_PATH'.format(os.path.join(self.prefix, 'lib'))}
        self.__wd = '/tmp' # working directory

    def cleanup_step(self, items=None):
        """Documentation TBD"""

        if not items:
            logging.warning('items are not defined')
            return ''

        return 'rm -rf {}'.format(' '.join(items))

    def __setup(self):
        """Documentation TBD"""

        # The download URL has the format contains vMAJOR.MINOR in the
        # path and the tarball contains MAJOR.MINOR.REVISION, so pull
        # apart the full version to get the MAJOR and MINOR components.
        match = re.match(r'(?P<major>\d+)\.(?P<minor>\d+)', self.version)
        major_minor = 'v{0}.{1}'.format(match.groupdict()['major'],
                                        match.groupdict()['minor'])
        tarball = 'openmpi-{}.tar.bz2'.format(self.version)
        url = '{0}/{1}/downloads/{2}'.format(self.baseurl, major_minor,
                                             tarball)

        # CUDA
        if self.cuda:
            if self.toolchain.CUDA_HOME:
                self.configure_opts.append(
                    '--with-cuda={}'.format(self.toolchain.CUDA_HOME))
            else:
                self.configure_opts.append('--with-cuda')
        else:
            self.configure_opts.append('--without-cuda')

        # InfiniBand
        if self.infiniband:
            self.configure_opts.append('--with-verbs')
        else:
            self.configure_opts.append('--without-verbs')

        if self.directory:
            # Use source from local build context
            self.__commands.append(self.configure_step(
                directory=os.path.join(self.__wd, self.directory),
                toolchain=self.toolchain))
        else:
            # Download source from web
            self.__commands.append(self.download_step(url=url,
                                                      directory=self.__wd))
            self.__commands.append(self.untar_step(
                tarball=os.path.join(self.__wd, tarball), directory=self.__wd))
            self.__commands.append(self.configure_step(
                directory=os.path.join(self.__wd,
                                       'openmpi-{}'.format(self.version)),
                toolchain=self.toolchain))

        self.__commands.append(self.build_step())

        if self.__check:
            self.__commands.append(self.check_step())

        self.__commands.append(self.install_step())

        if self.directory:
            # Using source from local build context, cleanup directory
            self.__commands.append(self.cleanup_step(
                items=[os.path.join(self.__wd, self.directory)]))
        else:
            # Using downloaded source, cleanup tarball and directory
            self.__commands.append(self.cleanup_step(
                items=[os.path.join(self.__wd, tarball),
                       os.path.join(self.__wd,
                                    'openmpi-{}'.format(self.version))]))

    def runtime(self, _from='0'):
        """Documentation TBD"""
        instructions = []
        instructions.append(comment('OpenMPI'))
        # TODO: move the definition of runtime ospackages
        instructions.append(apt_get(ospackages=['hwloc', 'openssh-client']))
        instructions.append(copy(_from=_from, src=self.prefix,
                                 dest=self.prefix))
        instructions.append(environment(
            variables=self.__environment_variables))
        return instructions

    def toString(self, ctype):
        """Documentation TBD"""

        self.__setup()

        instructions = []
        if self.directory:
            instructions.append(comment('OpenMPI').toString(ctype))
        else:
            instructions.append(comment(
                'OpenMPI version {}'.format(self.version)).toString(ctype))
        instructions.append(apt_get(
            ospackages=self.ospackages).toString(ctype))
        if self.directory:
            # Use source from local build context
            instructions.append(
                copy(src=self.directory,
                     dest=os.path.join(self.__wd,
                                       self.directory)).toString(ctype))
        instructions.append(shell(commands=self.__commands).toString(ctype))
        instructions.append(environment(
            variables=self.__environment_variables).toString(ctype))

        return '\n'.join(instructions)
