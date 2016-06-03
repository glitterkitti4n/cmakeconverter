# -*- coding: utf-8 -*-

import projectvariables as pv
import message as msg
import macro, dependencies, flags

class ConvertData:
    """
    ConvertData: will convert data to CMakeLists.txt.
    """

    def __init__(self, data=None):
        self.data = data

    def create_data(self):
        # Write variables
        variables = pv.ProjectVariables(self.data)
        variables.define_variable()

        # Write Macro
        macro_project = macro.Macro()
        macro_project.write_macro(self.data)

        # Write Output Variables
        variables.write_output()

        # Write Include Directories
        depends = dependencies.Dependencies(self.data)
        if self.data['includes']:
            depends.write_include_dir()
        else:
            msg.send('Include Directories is not set.', '')

        # Write Dependencies
        depends.write_dependencies()

        # Write Flags
        all_flags = flags.Flags(self.data)
        all_flags.write_flags()

    def get_arguments(self):
        return self.data

    def get_cmake(self):
        return self.data['cmake']
