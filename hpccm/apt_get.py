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

"""Documentation TBD"""

from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import

from .shell import shell

class apt_get(object):
    """Documentation TBD"""

    def __init__(self, **kwargs):
        """Documentation TBD"""

        #super(apt_get, self).__init__()

        self.__commands = []
        self.ospackages = kwargs.get('ospackages', [])

    def __setup(self):
        """Documentation TBD"""

        self.__commands.append('apt-get update -y')
        if self.ospackages:
            install = 'apt-get install -y --no-install-recommends \\\n'
            packages = []
            for pkg in self.ospackages:
                packages.append('        {}'.format(pkg))
            install = install + ' \\\n'.join(packages)
            self.__commands.append(install)
        self.__commands.append('rm -rf /var/lib/apt/lists/*')

    def toString(self, ctype):
        """Documentation TBD"""

        self.__setup()
        s = shell(commands=self.__commands)
        return s.toString(ctype)
