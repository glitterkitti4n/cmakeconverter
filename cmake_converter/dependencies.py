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

"""
    Dependencies
    ============
     Manage directories and libraries of project dependencies
"""

import ntpath
import os
import re

from cmake_converter.message import send
from cmake_converter.data_files import get_vcxproj_data, get_xml_data
from cmake_converter.utils import write_property_of_settings, \
    get_global_project_name_from_vcxproj_file, cleaning_output, normalize_path


class Dependencies(object):
    """
        Class who find and write dependencies of project, additionnal directories...
    """

    def __init__(self, context):
        self.cmake = context['cmake']
        self.tree = context['vcxproj']['tree']
        self.ns = context['vcxproj']['ns']
        self.dependencies = context['dependencies']
        self.settings = context['settings']
        self.definition_groups = context['definition_groups']
        self.includes = context['includes']
        self.vcxproj_path = context['vcxproj_path']

    def write_include_dir(self):
        """
        Write on "CMakeLists.txt" include directories required for compilation.

        """
        if not self.includes:
            send('Include Directories is not set.', '')
            return

        working_path = os.path.dirname(self.vcxproj_path)

        for setting in self.settings:
            incl_dir = self.tree.find(
                '{0}/ns:ClCompile/ns:AdditionalIncludeDirectories'.format(self.definition_groups[setting]),
                namespaces=self.ns
            )

            if incl_dir is not None:
                inc_dir = incl_dir.text.replace('$(ProjectDir)', './')
                inc_dir = inc_dir.replace(';%(AdditionalIncludeDirectories)', '')
                dirs = []
                for i in inc_dir.split(';'):
                    i = normalize_path(working_path, i)
                    i = re.sub(r'\$\((.+?)\)', r'$ENV{\1}', i)
                    dirs.append(i)
                inc_dirs = ';'.join(dirs)
                self.settings[setting]['inc_dirs'] = inc_dirs
                send('Include Directories found : %s' % inc_dirs, 'warn')
            else:  # pragma: no cover
                send('Include Directories not found for this project.', 'warn')

        write_property_of_settings(self.cmake, self.settings, 'target_include_directories(${PROJECT_NAME} PRIVATE ',
                                   ')', 'inc_dirs')
        self.cmake.write('\n')

    @staticmethod
    def get_dependency_target_name(vs_project):
        """
        Return dependency of target

        :param vs_project: vcxproj
        :return:
        """
        # VS Project (.vcxproj)
        vcxproj = get_vcxproj_data(vs_project)
        project_name = get_global_project_name_from_vcxproj_file(vcxproj)
        if project_name:
            return project_name
        else:
            return os.path.splitext(ntpath.basename(vs_project))[0]

    def write_target_dependencies(self, references):
        """
        Add dependencies to project

        """

        references_found = []
        if references:
            for ref in references:
                if ref is None:
                    continue

                ref_inc = ref.get('Include')
                if ref_inc is None:
                    continue

                if ref_inc not in references_found:
                    references_found.append(ref_inc)

            if references_found:
                self.cmake.write('add_dependencies(${PROJECT_NAME}')
                for ref_found in references_found:
                    project_name = self.get_dependency_target_name(os.path.join(os.path.dirname(self.vcxproj_path),
                                                                                ref_found))
                    self.cmake.write(' {0}'
                                     .format(project_name))

                self.cmake.write(')\n\n')

    def write_dependencies(self):
        """
        Write on "CMakeLists.txt" subdirectories or link directories for external libraries.

        """
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            self.cmake.write('################### Dependencies ##################\n'
                             '# Add Dependencies to project.                    #\n'
                             '###################################################\n\n')
            self.write_target_dependencies(references)
            return  # TODO: looks like wrong code
            self.cmake.write(
                'option(BUILD_DEPENDS \n' +
                '   "Build other CMake project." \n' +
                '   ON \n' +
                ')\n\n'
            )
            self.cmake.write(
                '# Dependencies : disable BUILD_DEPENDS to link with lib already build.\n'
            )
            if self.dependencies is None:
                self.cmake.write('if(BUILD_DEPENDS)\n')
                for ref in references:
                    reference = str(ref.get('Include'))
                    path_to_reference = os.path.splitext(ntpath.basename(reference))[0]
                    self.cmake.write(
                        '   add_subdirectory(platform/cmake/%s ${CMAKE_BINARY_DIR}/%s)\n' % (
                            path_to_reference, path_to_reference
                        )
                    )
            else:
                self.cmake.write('if(BUILD_DEPENDS)\n')
                d = 1
                for ref in self.dependencies:
                    self.cmake.write(
                        '   add_subdirectory(%s ${CMAKE_BINARY_DIR}/lib%s)\n' % (ref, str(d)))
                    send(
                        'Add manually dependencies : %s. Will be build in "lib%s/" !' % (
                            ref, str(d)),
                        'warn'
                    )
                    d += 1
            self.cmake.write('else()\n')
            for ref in references:
                reference = str(ref.get('Include'))
                path_to_reference = os.path.splitext(ntpath.basename(reference))[0]
                self.cmake.write(
                    '   link_directories(dependencies/%s/build/)\n' % path_to_reference
                )
            self.cmake.write('endif()\n\n')
        else:  # pragma: no cover
            send('No link needed.', '')

    def link_dependencies(self):
        """
        Write link dependencies of project.

        """

        # References to other targets in solution
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            self.cmake.write('# Link with other targets.\n')
            self.cmake.write('target_link_libraries(${PROJECT_NAME}')
            for ref in references:
                ref_inc = ref.get('Include')
                if ref_inc is None:
                    continue
                reference = str(ref_inc)
                path_to_reference = os.path.splitext(ntpath.basename(reference))[0]
                lib = self.get_dependency_target_name(os.path.join(os.path.dirname(self.vcxproj_path), reference))
                if lib == 'g3log':
                    lib += 'ger'  # To get "g3logger"
                self.cmake.write(' ' + lib)
                message = 'External library found : %s' % path_to_reference
                send(message, '')
            self.cmake.write(')\n')

        # Additional Dependencies
        dependencies = self.tree.xpath('//ns:AdditionalDependencies', namespaces=self.ns)
        if dependencies:
            list_depends = dependencies[0].text.replace('%(AdditionalDependencies)', '')
            if list_depends != '':
                send('Additional Dependencies = %s' % list_depends, 'ok')
                add_lib_dirs = []
                for d in list_depends.split(';'):
                    if d != '%(AdditionalDependencies)':
                        if os.path.splitext(d)[1] == '.lib':
                            add_lib_dirs.append(d.replace('.lib', ''))
                if add_lib_dirs:
                    self.cmake.write('# Link with other additional libraries.\n')
                    self.cmake.write('target_link_libraries(${PROJECT_NAME}')
                    for dep in add_lib_dirs:
                        self.cmake.write(' ' + dep)
                    self.cmake.write(')\n')
        else:  # pragma: no cover
            send('No dependencies.', '')

        # Additional Library Directories
        additional_library_directories = self.tree.xpath('//ns:AdditionalLibraryDirectories', namespaces=self.ns)
        if additional_library_directories:
            list_depends = additional_library_directories[0].text.replace('%(AdditionalLibraryDirectories)', '')
            if list_depends != '':
                send('Additional Library Directories = %s' % list_depends, 'ok')
                add_lib_dirs = []
                for d in list_depends.split(';'):
                    d = d.strip()
                    if d != '':
                        add_lib_dirs.append(d)
                if add_lib_dirs:
                    self.cmake.write('if(MSVC)\n')
                    self.cmake.write('   target_link_libraries(${PROJECT_NAME}')
                    for dep in add_lib_dirs:
                        self.cmake.write(' -LIBPATH:' + cleaning_output(dep))
                    self.cmake.write(')\n')
                    self.cmake.write('endif(MSVC)\n')
        else:  # pragma: no cover
            send('No dependencies.', '')

    def extensions_targets_dependencies(self):
        """
        Other dependencies of project. Like nuget for example.

        """
        packages_xml = get_xml_data( os.path.join(os.path.dirname(self.cmake.name), 'packages.config') )
        # External libraries
        if packages_xml:
            extension = packages_xml['tree'].xpath('/packages/package')
            for ref in extension:
                id = ref.get('id')
                version = ref.get('version')
                name = '{0}.{1}'.format(id, version)
                self.cmake.write('\nuse_package(${{PROJECT_NAME}} {0})'.format(name))
