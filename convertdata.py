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

from dependencies import Dependencies
from macro import Macro
from flags import Flags
from projectvariables import ProjectVariables
from projectfiles import ProjectFiles
from message import send


class ConvertData:
    """
    ConvertData: will convert data to CMakeLists.txt.
    """

    def __init__(self, data=None):
        self.data = data

    def create_data(self):
        # Write variables
        variables = ProjectVariables(self.data)
        variables.define_variable()
        files = ProjectFiles(self.data)
        files.write_variables()
        variables.define_project()
        variables.define_target()

        # Write Macro
        macros = Macro()
        macros.write_macro(self.data)

        # Write Output Variables
        variables.write_output()

        # Write Include Directories
        depends = Dependencies(self.data)
        if self.data['includes']:
            depends.write_include_dir()
        else:
            send('Include Directories is not set.', '')

        # Write Dependencies
        depends.write_dependencies()

        # Add additional code or not
        if self.data['additional_code'] is not None:
            files.add_additional_code(self.data['additional_code'])

        # Write Flags
        all_flags = Flags(self.data)
        all_flags.write_flags()

        # Write and add Files
        files.write_files()
        files.add_artefact()

        # Link with other dependencies
        depends.link_dependencies()

        # Close CMake file
        self.data['cmake'].close()
