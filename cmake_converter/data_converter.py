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
    DataConverter
    =============
     Manage conversion of **.vcxproj** data
"""

from cmake_converter.data_files import get_cmake_lists
from cmake_converter.flags import Flags
from cmake_converter.utils import write_comment, message
from cmake_converter.context import Context
import os


class DataConverter(object):
    """
        Base class for converters
    """

    @staticmethod
    def collect_data(context):
        """
        Collect data for converter.

        """
        context.variables.find_outputs_variables(context)

        context.files.collects_source_files(context)
        context.files.find_cmake_project_languages(context)

        if not context.has_only_headers:
            context.flags.define_flags(context)
            context.dependencies.find_include_dir(context)
            context.dependencies.find_target_references(context)
            context.dependencies.find_target_additional_dependencies(context)
            context.dependencies.find_target_additional_library_directories(context)
            context.dependencies.find_target_property_sheets(context)
            context.dependencies.find_target_pre_build_events(context)
            context.dependencies.find_target_pre_link_events(context)
            context.dependencies.find_target_post_build_events(context)
            context.dependencies.find_custom_build_step(context)
            context.dependencies.find_target_dependency_packages(context)

    def write_data(self, context, cmake_file):
        """
        Write data defined in converter.

        :param context: converter context
        :type context: Context
        :param cmake_file: CMakeLists IO wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        if not context.is_converting_solution:
            self.add_cmake_version_required(cmake_file)

        context.files.write_cmake_project(context, cmake_file)
        # context.variables.add_default_target() # TODO: add conversion option to cmd line

        # Add additional code or not
        if context.additional_code is not None:
            context.files.add_additional_code(context.additional_code, cmake_file)

        context.files.write_header_files(context, cmake_file)

        if not context.has_only_headers:
            context.flags.write_precompiled_headers_macro(context, cmake_file)
            context.files.write_source_files(context, cmake_file)
            context.flags.write_use_pch_macro(context, cmake_file)
            write_comment(cmake_file, 'Target')
            context.flags.write_target_artifact(context, cmake_file)
            self.write_supported_architectures_check(context, cmake_file)
            context.dependencies.write_target_property_sheets(context, cmake_file)
            context.variables.write_target_outputs(context, cmake_file)
            context.dependencies.write_include_directories(context, cmake_file)
            context.flags.write_defines(context, cmake_file)
            context.flags.write_flags(context, cmake_file)
            context.dependencies.write_target_pre_build_events(context, cmake_file)
            context.dependencies.write_target_pre_link_events(context, cmake_file)
            context.dependencies.write_target_post_build_events(context, cmake_file)
            context.dependencies.write_custom_build_events_of_files(context, cmake_file)
            if (context.target_references or
                    context.add_lib_deps or
                    context.add_lib_dirs or
                    context.sln_deps or
                    context.packages):
                write_comment(cmake_file, 'Dependencies')
            context.dependencies.write_target_references(context, cmake_file)
            context.dependencies.write_link_dependencies(context, cmake_file)
            context.dependencies.write_target_dependency_packages(context, cmake_file)
        else:
            Flags.write_target_headers_only_artifact(cmake_file)

    def convert(self, context):
        """
        Method template for data collecting and writing

        """

        message('Collecting data for project {0}'.format(context.vcxproj_path), '')
        self.collect_data(context)
        if context.dry:
            return
        if os.path.exists(context.cmake + '/CMakeLists.txt'):
            cmake_file = get_cmake_lists(context.cmake, 'a')
            cmake_file.write('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
        else:
            cmake_file = get_cmake_lists(context.cmake)
        message('Writing data for project {0}'.format(context.vcxproj_path), '')
        self.write_data(context, cmake_file)
        cmake_file.close()

    @staticmethod
    def add_cmake_version_required(cmake_file):
        """
        Write CMake minimum required

        :param cmake_file: IO cmake file wrapper
        :type cmake_file: _io.TextIOWrapper
        """

        cmake_file.write('cmake_minimum_required(VERSION 3.0.0 FATAL_ERROR)\n\n')

    @staticmethod
    def write_supported_architectures_check(context, cmake_file):
        arch_list = list(context.supported_architectures)
        arch_list.sort()
        cmake_file.write('if(NOT (')
        first = True
        for arch in arch_list:
            if first:
                cmake_file.write('\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{0}\"'
                                 .format(arch))
                first = False
            else:
                cmake_file.write('\n     OR \"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{0}\"'
                                 .format(arch))
        cmake_file.write('))\n')
        cmake_file.write(
            '    message(WARNING "${CMAKE_VS_PLATFORM_NAME} arch is not supported!")\n')
        cmake_file.write('endif()\n\n')
