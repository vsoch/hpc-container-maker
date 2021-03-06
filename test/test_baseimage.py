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

"""Test cases for the baseimage module"""

from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import
import unittest

from hpccm.common import container_type
from hpccm.baseimage import baseimage

class Test_baseimage(unittest.TestCase):
    def setUp(self):
        """Disable logging output messages"""
        logging.disable(logging.ERROR)

    def test_empty(self):
        """Default base image"""
        b = baseimage()
        self.assertNotEqual(b.toString(container_type.DOCKER), '')
        self.assertNotEqual(b.toString(container_type.SINGULARITY), '')

    def test_invalid_ctype(self):
        """Invalid container type specified"""
        b = baseimage()
        self.assertEqual(b.toString(None), '')

    def test_value(self):
        """Image name is specified"""
        b = baseimage(image='foo')
        self.assertEqual(b.toString(container_type.DOCKER), 'FROM foo')
        self.assertEqual(b.toString(container_type.SINGULARITY),
                         'BootStrap: docker\nFrom: foo')

    def test_as_deprecated(self):
        """Docker specified image naming"""
        b = baseimage(image='foo', AS='dev')
        self.assertEqual(b.toString(container_type.DOCKER), 'FROM foo AS dev')
        self.assertEqual(b.toString(container_type.SINGULARITY),
                         'BootStrap: docker\nFrom: foo')

    def test_as(self):
        """Docker specified image naming"""
        b = baseimage(image='foo', _as='dev')
        self.assertEqual(b.toString(container_type.DOCKER), 'FROM foo AS dev')
        self.assertEqual(b.toString(container_type.SINGULARITY),
                         'BootStrap: docker\nFrom: foo')
