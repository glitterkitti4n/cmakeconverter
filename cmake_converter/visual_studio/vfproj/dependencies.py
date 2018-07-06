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

import os

from cmake_converter.dependencies import Dependencies
from cmake_converter.utils import message, prepare_build_event_cmd_line_for_cmake


class VFDependencies(Dependencies):

    @staticmethod
    def find_include_dir(context):
        for setting in context.settings:
            ad_inc = context.settings[setting]['VFFortranCompilerTool'].get(
                'AdditionalIncludeDirectories'
            )
            if ad_inc:
                Dependencies.get_additional_include_directories(ad_inc, setting, context)
            if 'inc_dirs' in context.settings[setting]:
                context.settings[setting]['inc_dirs'] += ';${CMAKE_CURRENT_SOURCE_DIR}/'
            else:
                context.settings[setting]['inc_dirs'] = '${CMAKE_CURRENT_SOURCE_DIR}/'

    @staticmethod
    def find_target_references(context):
        if context.sln_deps:
            context.target_references = context.target_references + context.sln_deps
            message('References : {}'.format(context.target_references), '')

    @staticmethod
    def find_target_additional_dependencies(context):
        for setting in context.settings:
            ad_libs = None
            if 'VFLibrarianTool' in context.settings[setting]:
                ad_libs = context.settings[setting]['VFLibrarianTool'].get('AdditionalDependencies')
            if 'VFLinkerTool' in context.settings[setting]:
                ad_libs = context.settings[setting]['VFLinkerTool'].get('AdditionalDependencies')
            if ad_libs:
                add_libs = []
                for d in ad_libs.split(';'):
                    if d != '%(AdditionalDependencies)':
                        if os.path.splitext(d)[1] == '.lib':
                            add_libs.append(d.replace('.lib', ''))
                context.add_lib_deps = True
                message('Additional Dependencies for {0} = {1}'.format(setting, add_libs),
                        '')
                context.settings[setting]['add_lib_deps'] = '$<SEMICOLON>'.join(add_libs)

    @staticmethod
    def find_target_additional_library_directories(context):
        """
        Find and set additional library directories in context

        """

        for setting in context.settings:
            context.add_lib_dirs = []
            additional_library_directories = None
            if 'VFLibrarianTool' in context.settings[setting]:
                additional_library_directories = context.settings[setting]['VFLibrarianTool'] \
                    .get('AdditionalLibraryDirectories')
            if 'VFLinkerTool' in context.settings[setting]:
                additional_library_directories = context.settings[setting]['VFLinkerTool'] \
                    .get('AdditionalLibraryDirectories')

            if additional_library_directories:
                list_depends = additional_library_directories.replace(
                    '%(AdditionalLibraryDirectories)', ''
                )
                if list_depends != '':
                    message('Additional Library Directories = {0}'.format(list_depends), '')
                    add_lib_dirs = []
                    for d in list_depends.split(';'):
                        d = d.strip()
                        if d != '':
                            add_lib_dirs.append(d)
                    context.add_lib_dirs = add_lib_dirs
            else:  # pragma: no cover
                message('No additional library dependencies.', '')

    @staticmethod
    def find_custom_build_events_of_files(context):
        for file in context.file_spec_raw_options:
            file_settings = context.file_spec_raw_options[file]
            for setting in file_settings:
                if 'VFCustomBuildTool' in file_settings[setting]:
                    custom_build = file_settings[setting]['VFCustomBuildTool']
                    if 'file_custom_build_events' not in context.settings[setting]:
                        context.settings[setting]['file_custom_build_events'] = {}
                    custom_event_data = {
                        'command_line': prepare_build_event_cmd_line_for_cmake(
                            custom_build['CommandLine']
                        ),
                        'description': custom_build['Description'],
                        'outputs': custom_build['Outputs'],
                    }
                    context.settings[setting]['file_custom_build_events'][file] = custom_event_data
                    message('Custom build for {0} file {1} is {2}'
                            .format(setting, file, custom_build), '')
