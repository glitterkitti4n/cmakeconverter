#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017:
#   Matthieu Estrada, ttamalfor@gmail.com
#
# This file is part of (CMakeConverter).
#
# (CMakeConverter) is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# (CMakeConverter) is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with (CMakeConverter).  If not, see <http://www.gnu.org/licenses/>.

import unittest2

from cmake_converter.flags import Flags
from cmake_converter.data_files import get_vcxproj_data, get_cmake_lists


class TestDependencies(unittest2.TestCase):
    """
        This file test methods of ActionManager class.
    """

    vcxproj_data_test = get_vcxproj_data('test/project_test.vcxproj')
    cmake_lists_test = get_cmake_lists('./')

    data_test = {
        'cmake': cmake_lists_test,
        'cmake_output': None,
        'vcxproj': vcxproj_data_test,
        'dependencies': None,
        'includes': None,
        'additional_code': None,
    }

    def test_init_dependencies(self):
        """Initialize Flags"""

        under_test = Flags(self.data_test)

        self.assertIsNotNone(under_test.tree)
        self.assertIsNotNone(under_test.ns)

        self.assertIsNotNone(under_test.propertygroup)
        self.assertTrue('debug' in under_test.propertygroup)
        self.assertTrue('release' in under_test.propertygroup)

        self.assertIsNotNone(under_test.definitiongroups)
        self.assertTrue('debug' in under_test.definitiongroups)
        self.assertTrue('release' in under_test.definitiongroups)

        self.assertFalse(under_test.win_deb_flags)
        self.assertFalse(under_test.win_rel_flags)

    def test_write_flags(self):
        """Write Flags"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Flags(self.data_test)
        self.assertFalse(under_test.win_deb_flags)
        self.assertFalse(under_test.win_rel_flags)

        under_test.write_flags()

        self.assertTrue(under_test.win_deb_flags)
        self.assertEqual(' /W4 /MD /Od /Zi /EHsc', under_test.win_deb_flags)
        self.assertTrue(under_test.win_rel_flags)
        self.assertEqual(' /W4 /GL /Od /Oi /Zi /EHsc', under_test.win_rel_flags)

        self.data_test['cmake'].close()

        cmakelists_test = open('CMakeLists.txt', 'r')
        content_test = cmakelists_test.read()

        self.assertTrue(' /W4 /MD /Od /Zi /EHsc' in content_test)
        self.assertTrue(' /W4 /GL /Od /Oi /Zi /EHsc' in content_test)

        cmakelists_test.close()

    def test_define_linux_flags(self):
        """Define Linux Flags"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Flags(self.data_test)

        under_test.define_linux_flags()
        self.data_test['cmake'].close()

        self.assertFalse(under_test.win_deb_flags)
        self.assertFalse(under_test.win_rel_flags)

        cmakelists_test = open('CMakeLists.txt', 'r')
        content_test = cmakelists_test.read()

        self.assertTrue('-std=c++11 -fPIC' in content_test)

    def test_define_windows_flags(self):
        """Define Windows Flags"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Flags(self.data_test)

        under_test.define_microsoft_groups()
        under_test.define_windows_flags()
        self.data_test['cmake'].close()

        self.assertTrue(under_test.win_deb_flags)
        self.assertTrue(under_test.win_rel_flags)

        cmakelists_test = open('CMakeLists.txt', 'r')
        content_test = cmakelists_test.read()

        self.assertFalse('-std=c++11 -fPIC' in content_test)
        self.assertTrue(' /W4 /MD /Od /Zi /EHsc' in content_test)
        self.assertTrue(' /W4 /GL /Od /Oi /Zi /EHsc' in content_test)

    def test_set_warning_level(self):
        """Set Warning Level"""

        self.data_test['cmake'] = get_cmake_lists('./')
        under_test = Flags(self.data_test)

        under_test.set_warning_level()

        self.assertTrue('/W4' in under_test.win_deb_flags)
        self.assertTrue('/W4' in under_test.win_rel_flags)

    def test_set_whole_program_optimization(self):
        """Set Whole Program Optimization"""

        self.data_test['cmake'] = get_cmake_lists()
        self.data_test['vcxproj'] = get_vcxproj_data('test/project_test.vcxproj')
        under_test = Flags(self.data_test)

        under_test.define_microsoft_groups()
        under_test.set_whole_program_optimization()

        self.assertFalse('/GL' in under_test.win_deb_flags)
        self.assertTrue('/GL' in under_test.win_rel_flags)
