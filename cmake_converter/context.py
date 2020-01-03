#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2019:
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
    Context object descriptor
    =========================

"""

import os
import time
from multiprocessing import cpu_count
from collections import OrderedDict
import copy

from cmake_converter.utils import message


class Context:
    """
        Converter context
    """
    def __init__(self):
        self.time0 = time.time()
        self.jobs = cpu_count()
        self.vcxproj = {}
        self.vcxproj_path = ''
        self.solution_path = ''
        self.project_number = None
        self.has_headers = False
        self.has_only_headers = False
        self.solution_languages = set()
        self.project_languages = []
        self.sln_deps = []
        self.target_references = []
        self.add_lib_deps = False
        self.packages_config_path = ''
        self.import_projects = []
        self.packages = []

        self.projects_regexp = '.*'
        self.additional_code = None
        self.dry = False
        self.verbose = False
        self.warn_level = 2
        self.private_include_directories = False
        self.indent = '    '

        self.sln_configurations_map = dict()
        self.solution_folder = ''
        self.configurations_to_parse = set()
        self.cmake = ''
        self.project_name = ''
        self.root_namespace = ''
        self.target_windows_version = ''
        self.sources = {}
        self.headers = {}
        self.other_project_files = {}
        self.source_groups = {}
        self.excluded_from_build = False
        self.file_contexts = OrderedDict()
        self.supported_architectures = set()
        self.settings = OrderedDict()
        self.current_setting = (None, None)  # (conf, arch)
        self.current_node = None
        self.warnings_count = 0
        # helpers
        self.parser = None
        self.variables = None
        self.files = None
        self.flags = None
        self.dependencies = None
        self.utils = None

    def clone(self):
        """
        Deep clone of Context

        :return:
        """
        return copy.deepcopy(self)

    @staticmethod
    def get_project_initialization_dict():
        """ Get initializer functors mapped to path keys """
        return {}

    def init(self, source_project_path, cmake_lists_destination_dir):
        """
           Initialize instance of Context with Initializer

           :param source_project_path:
           :param cmake_lists_destination_dir:
           :return:
           """

        message(
            self,
            'Initialization data for conversion of project {}'.format(self.vcxproj_path),
            ''
        )

        for sln_config in self.sln_configurations_map:
            self.configurations_to_parse.add(self.sln_configurations_map[sln_config])

        context_initializer_map = self.get_project_initialization_dict()

        for key in context_initializer_map:
            if key in source_project_path:
                context_initializer_map[key]()
                self.project_name = os.path.basename(os.path.splitext(source_project_path)[0])
                self.vcxproj_path = source_project_path
                self.set_cmake_lists_path(cmake_lists_destination_dir)
                self.utils.init_context_current_setting(self)  # None - global settings
                self.flags.prepare_context_for_flags(self)
                return True
        return False

    def set_cmake_lists_path(self, cmake_lists):
        """
        Set CMakeLists.txt path in context, for given project

        :param cmake_lists: path of CMakeLists related to project name
        :type cmake_lists: str
        """

        self.cmake = None

        if cmake_lists:
            if os.path.exists(cmake_lists):
                self.cmake = cmake_lists

        if self.cmake is None:
            message(
                self,
                'Path "{}" for CMakeLists.txt is wrong. '
                'It will be created in working directory.'.format(cmake_lists),
                'warn'
            )
            self.cmake = 'CMakeLists.txt'

        return self.cmake
