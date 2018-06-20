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
import re

from cmake_converter.dependencies import Dependencies
from cmake_converter.data_files import get_xml_data, get_propertygroup
from cmake_converter.utils import normalize_path, message, replace_vs_vars_with_cmake_vars, \
    make_os_specific_shell_path


class VCXDependencies(Dependencies):

    def find_include_dir(self, context):
        """
        Write on "CMakeLists.txt" include directories required for compilation.

        """

        for setting in context.settings:
            incl_dir = context.vcxproj['tree'].find(
                '{0}/ns:ClCompile/ns:AdditionalIncludeDirectories'.format(
                    context.definition_groups[setting]
                ),
                namespaces=context.vcxproj['ns']
            )

            if incl_dir is not None:
                inc_dirs = self.get_additional_include_directories(
                    incl_dir.text, setting, context
                )
                message('Include Directories found : {0}'.format(inc_dirs), '')
            else:  # pragma: no cover
                message('Include Directories not found for this project.', '')

    def find_target_references(self, context):
        """
        Find and set references of project to current context

        """

        references_found = []
        references = context.vcxproj['tree'].xpath('//ns:ProjectReference',
                                                   namespaces=context.vcxproj['ns'])
        if references:
            for ref in references:
                if ref is None:
                    continue

                ref_inc = ref.get('Include')
                if ref_inc is None:
                    continue

                if ref_inc not in references_found:
                    ref = self.get_dependency_target_name(
                        os.path.join(os.path.dirname(context.vcxproj_path), ref_inc)
                    )
                    references_found.append(ref)

        context.target_references = references_found

    @staticmethod
    def find_target_additional_dependencies(context):
        """
        Find and set additional dependencies of current project in context

        """

        dependencies = context.vcxproj['tree'].xpath('//ns:AdditionalDependencies',
                                                     namespaces=context.vcxproj['ns'])
        context.add_lib_deps = []
        if dependencies:
            list_depends = dependencies[0].text.replace('%(AdditionalDependencies)', '')
            if list_depends != '':
                message('Additional Dependencies = %s' % list_depends, '')
                add_lib_dirs = []
                for d in list_depends.split(';'):
                    if d != '%(AdditionalDependencies)':
                        if os.path.splitext(d)[1] == '.lib':
                            add_lib_dirs.append(d.replace('.lib', ''))
                context.add_lib_deps = add_lib_dirs
        else:  # pragma: no cover
            message('No additional dependencies.', '')

    @staticmethod
    def find_target_additional_library_directories(context):
        """
        Find and set additional library directories in context

        """

        additional_library_directories = context.vcxproj['tree'].xpath(
            '//ns:AdditionalLibraryDirectories', namespaces=context.vcxproj['ns']
        )

        context.add_lib_dirs = []
        if additional_library_directories:
            list_depends = additional_library_directories[0].text.replace(
                '%(AdditionalLibraryDirectories)', ''
            )
            if list_depends != '':
                message('Additional Library Directories = %s' % list_depends, '')
                add_lib_dirs = []
                for d in list_depends.split(';'):
                    d = d.strip()
                    if d != '':
                        add_lib_dirs.append(d)
                context.add_lib_dirs = add_lib_dirs
        else:  # pragma: no cover
            message('No additional library dependencies.', '')

    @staticmethod
    def find_target_property_sheets(context):
        """
        Find and set in current context property sheets

        """

        property_nodes = context.vcxproj['tree'].xpath(
            '//ns:ImportGroup[@Label="PropertySheets"]/ns:Import', namespaces=context.vcxproj['ns']
        )
        props_set = set()
        for node in property_nodes:
            label = node.get('Label')
            if not label:
                filename = node.get('Project')
                if 'Microsoft.CPP.UpgradeFromVC60' in filename:
                    continue
                # props_path = os.path.join(os.path.dirname(context.vcxproj_path), filename)
                working_path = os.path.dirname(context.vcxproj_path)
                props_set.add(normalize_path(working_path, filename).replace('.props', '.cmake'))
                # properties_xml = get_xml_data(props_path)
                # if properties_xml:
                #     properties_xml.close()  # TODO collect data from props
        props_list = list(props_set)
        props_list.sort()
        context.property_sheets = props_list

    @staticmethod
    def find_target_dependency_packages(context):
        """
        Find and set other dependencies of project to current context. Like nuget for example.

        """

        context.packages = []

        packages_nodes = context.vcxproj['tree'].xpath(
            '//ns:ItemGroup/ns:None[@Include="packages.config"]', namespaces=context.vcxproj['ns']
        )
        if packages_nodes:
            # TODO with '|' in xpath and unify label name(remove hardcode)
            ext_targets = context.vcxproj['tree'].xpath(
                '//ns:ImportGroup[@Label="ExtensionTargets"]/ns:Import'
                , namespaces=context.vcxproj['ns'])
            if not ext_targets:
                ext_targets = context.vcxproj['tree'].xpath(
                    '//ns:ImportGroup[@Label="Shared"]/ns:Import',
                    namespaces=context.vcxproj['ns'])
            if not ext_targets:
                ext_targets = context.vcxproj['tree'].xpath(
                    '//ns:ImportGroup[@Label="ExtensionSettings"]/ns:Import',
                    namespaces=context.vcxproj['ns'])

            filename = packages_nodes[0].get('Include')
            packages_xml = get_xml_data(os.path.join(os.path.dirname(context.vcxproj_path),
                                                     filename))
            if packages_xml:
                extension = packages_xml['tree'].xpath('/packages/package')
                for ref in extension:
                    package_id = ref.get('id')
                    package_version = ref.get('version')
                    id_version = '{0}.{1}'.format(package_id, package_version)
                    targets_file_path = ''
                    for import_project_node in ext_targets:
                        project_path = import_project_node.get('Project')
                        if id_version in project_path:
                            targets_file_path = project_path
                            break

                    ext_properties = []
                    if targets_file_path:
                        targets_file = get_xml_data(targets_file_path)
                        if targets_file is None:
                            continue

                        property_page_schema_nodes = targets_file['tree']\
                            .xpath('//ns:ItemGroup/ns:PropertyPageSchema',
                                   namespaces=targets_file['ns'])

                        if property_page_schema_nodes:
                            for property_page_schema_node in property_page_schema_nodes:
                                xml_schema_path = property_page_schema_node.get('Include')
                                xml_schema_path = xml_schema_path.replace(
                                    '$(MSBuildThisFileDirectory)',
                                    os.path.dirname(targets_file_path) + '/'
                                )
                                xml_schema_file = get_xml_data(xml_schema_path)
                                if xml_schema_file:
                                    ext_property_nodes = xml_schema_file['tree'] \
                                        .xpath('//ns:EnumProperty',
                                               namespaces=xml_schema_file['ns'])
                                    for ext_property_node in ext_property_nodes:
                                        ext_properties.append(ext_property_node.get('Name'))
                        # TODO: remove next if due specific hack
                        if not ext_properties:
                            ext_property_nodes = targets_file['tree']\
                                .xpath('//ns:PropertyGroup'
                                       '[@Label="Default initializers for properties"]/*',
                                       namespaces=targets_file['ns'])
                            for ext_property_node in ext_property_nodes:
                                ext_properties.append(re.sub(r'{.*\}', '', ext_property_node.tag))
                    else:
                        message('Path of file {0}.targets not found at vs project xml.'
                                .format(id_version), 'warn')

                    context.packages.append([package_id, package_version, ext_properties])
                    message('Used package {0} {1}.'.format(package_id, package_version), '')

                    for ext_property in ext_properties:
                        for setting in context.settings:
                            if 'packages' not in context.settings[setting]:
                                context.settings[setting]['packages'] = {}
                            ext_property_node = context.vcxproj['tree'].xpath(
                                '{0}/ns:{1}'.format(get_propertygroup(setting), ext_property),
                                namespaces=context.vcxproj['ns'])
                            if ext_property_node:
                                if id_version not in context.settings[setting]['packages']:
                                    context.settings[setting]['packages'][id_version] = {}
                                context.settings[setting]['packages'][id_version][ext_property] = \
                                    ext_property_node[0].text
                                message('{0} property of {1} {2} for {3} is {4}'
                                        .format(ext_property,
                                                package_id,
                                                package_version,
                                                setting,
                                                ext_property_node[0].text), '')

    @staticmethod
    def __find_target_build_events(context, tree_xpath, value_name, event_type):
        for setting in context.settings:
            build_events = context.vcxproj['tree'].xpath(
                tree_xpath.format(context.definition_groups[setting]),
                namespaces=context.vcxproj['ns']
            )
            context.settings[setting][value_name] = []
            for build_event_node in build_events:
                for build_event in build_event_node.text.split('\n'):
                    build_event = build_event.strip()
                    if build_event:
                        cmake_build_event = make_os_specific_shell_path(build_event)
                        cmake_build_event = replace_vs_vars_with_cmake_vars(cmake_build_event)
                        cmake_build_event = cmake_build_event.replace('\\', '\\\\')
                        context.settings[setting][value_name] \
                            .append(cmake_build_event)
                        message('{0} event for {1}: {2}'
                                .format(event_type, setting, cmake_build_event), 'info')

    def find_target_pre_build_events(self, context):
        self.__find_target_build_events(
            context,
            '{0}/ns:PreBuildEvent/ns:Command',
            'pre_build_events',
            'Pre build'
        )

    def find_target_pre_link_events(self, context):
        self.__find_target_build_events(
            context,
            '{0}/ns:PreLinkEvent/ns:Command',
            'pre_link_events',
            'Pre link'
        )

    def find_target_post_build_events(self, context):
        self.__find_target_build_events(
            context,
            '{0}/ns:PostBuildEvent/ns:Command',
            'post_build_events',
            'Post build'
        )
