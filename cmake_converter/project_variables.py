#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018:
#   Matthieu Estrada, ttamalfor@gmail.com
#   Pavel Liavonau, liavonlida@gmail.com
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

"""
    ProjectVariables
    ================
     Manage creation of CMake variables that will be used during compilation
"""

from cmake_converter.utils import write_property_of_settings
from cmake_converter.utils import write_comment


class ProjectVariables(object):
    """
        Class who manage project variables
    """

    @staticmethod
    def add_default_target(cmake_file):
        """
        Add default target release if not define

        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        cmake_file.write(
            '# Define Release by default.\n'
            'if(NOT CMAKE_BUILD_TYPE)\n'
            '  set(CMAKE_BUILD_TYPE "Release")\n'
            '  message(STATUS "Build type not specified: Use Release by default.")\n'
            'endif(NOT CMAKE_BUILD_TYPE)\n\n'
        )

    @staticmethod
    def write_target_outputs(context, cmake_file):
        """
        Add outputs for each artefacts CMake target

        :param context: related full context
        :type context: Context
        :param cmake_file: CMakeLists.txt IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if len(context.settings) == 0:
            return

        write_comment(cmake_file, 'Target name')
        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
            'string(CONCAT TARGET_NAME', ')', 'target_name', '',
            '${PROJECT_NAME}'
        )
        cmake_file.write(
            'set_target_properties(${PROJECT_NAME} PROPERTIES OUTPUT_NAME ${TARGET_NAME})\n'
            'set_target_properties(${PROJECT_NAME} PROPERTIES PREFIX "")\n\n'
        )

        write_comment(cmake_file, 'Output directory')

        write_property_of_settings(
            cmake_file, context.settings,
            context.sln_configurations_map,
            'string(CONCAT OUT_DIR', ')', 'out_dir', '',
            '${CMAKE_SOURCE_DIR}/${CMAKE_VS_PLATFORM_NAME}/$<CONFIG>'
        )

        for setting in context.settings:
            break

        configuration_type = context.settings[setting]['target_type']

        if configuration_type == 'DynamicLibrary':
            cmake_file.write('set(ARCHIVE_OUT_DIR ${OUT_DIR})\n')
            write_property_of_settings(
                cmake_file, context.settings,
                context.sln_configurations_map,
                'string(CONCAT ARCHIVE_OUT_DIR', ')', 'import_library_path', ''
            )
            cmake_file.write('set(ARCHIVE_OUT_NAME ${PROJECT_NAME})\n')
            write_property_of_settings(
                cmake_file, context.settings,
                context.sln_configurations_map,
                'string(CONCAT ARCHIVE_OUT_NAME', ')', 'import_library_name', ''
            )

        if configuration_type:
            left_string = 'set_target_properties(${PROJECT_NAME} PROPERTIES '
            right_string = '_OUTPUT_DIRECTORY ${OUT_DIR})\n'
            if configuration_type == 'DynamicLibrary' or configuration_type == 'StaticLibrary':
                if configuration_type == 'DynamicLibrary':
                    cmake_file.write(
                        left_string + 'ARCHIVE' + '_OUTPUT_NAME ${ARCHIVE_OUT_NAME})\n')
                    cmake_file.write(
                        left_string + 'ARCHIVE' + '_OUTPUT_DIRECTORY ${ARCHIVE_OUT_DIR})\n')
                    cmake_file.write(left_string + 'RUNTIME' + right_string)
                else:
                    cmake_file.write(
                        left_string + 'ARCHIVE' + right_string)
                # TODO: do we really need LIBRARY_OUTPUT_DIRECTORY here?
                cmake_file.write(left_string + 'LIBRARY' + right_string)
                cmake_file.write('\n')
            else:
                cmake_file.write(
                    left_string + 'RUNTIME' + right_string + '\n')

