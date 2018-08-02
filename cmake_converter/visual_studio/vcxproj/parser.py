#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2018:
#   Pavel Liavonau, liavonlida@gmail.com
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

import re

from cmake_converter.parser import Parser, StopParseException
from cmake_converter.context import ContextInitializer
from cmake_converter.data_files import get_propertygroup, get_definitiongroup
from cmake_converter.utils import replace_vs_vars_with_cmake_vars
from cmake_converter.data_files import get_xml_data


class VCXParser(Parser):

    def __init__(self, context):
        Parser.__init__(self)
        self.node_handlers = {
            'ItemGroup': self.__parse_item_group,
            'ProjectConfiguration': self.do_nothing_node_stub,
            'ConfigurationType': self.__parse_configuration_type,
            'CharacterSet': context.flags.set_character_set,
            'PlatformToolset': self.do_nothing_node_stub,
            'PropertyGroup': self.__parse_property_group,
            'ItemDefinitionGroup': self.__parse_item_definition_group,
            'ClInclude': self.__parse_cl_include,
            'ClCompile': self.__parse_cl_compile,
            'AdditionalIncludeDirectories': context.dependencies.set_include_dirs,
            'AdditionalDependencies': context.dependencies.set_target_additional_dependencies,
            'AdditionalLibraryDirectories':
                context.dependencies.set_target_additional_library_directories,
            'PreprocessorDefinitions': context.flags.set_defines,
            'PrecompiledHeader': context.flags.set_flag,
            'Link': self._parse_nodes,
            'Lib': self._parse_nodes,
            'OutputFile': context.variables.set_output_file,
            'ImportLibrary': context.variables.set_import_library,
            'OutDir': context.variables.set_output_dir,
            'TargetName': self.__parse_target_name_node,
            'UseDebugLibraries': context.flags.set_flag,
            'WholeProgramOptimization': context.flags.set_flag,
            'GenerateDebugInformation': context.flags.set_flag,
            'LinkIncremental': context.flags.set_flag,
            'Optimization': context.flags.set_flag,
            'InlineFunctionExpansion': context.flags.set_flag,
            'IntrinsicFunctions': context.flags.set_flag,
            'StringPooling': context.flags.set_flag,
            'BasicRuntimeChecks': context.flags.set_flag,
            'RuntimeLibrary': context.flags.set_flag,
            'FunctionLevelLinking': context.flags.set_flag,
            'WarningLevel': context.flags.set_flag,
            'TreatWarningAsError': context.flags.set_flag,
            'DebugInformationFormat': context.flags.set_flag,
            'CompileAs': context.flags.set_flag,
            'FloatingPointModel': context.flags.set_flag,
            'RuntimeTypeInfo': context.flags.set_flag,
            'DisableSpecificWarnings': context.flags.set_flag,
            'AdditionalOptions': self.__parse_additional_options,
            'ExceptionHandling': context.flags.set_flag,
            'BufferSecurityCheck': context.flags.set_flag,
            'DiagnosticsFormat': context.flags.set_flag,
            'DisableLanguageExtensions': context.flags.set_flag,
            'TreatWChar_tAsBuiltInType': context.flags.set_flag,
            'ForceConformanceInForLoopScope': context.flags.set_flag,
            'RemoveUnreferencedCodeData': context.flags.set_flag,
            'OpenMPSupport': context.flags.set_flag,
        }
        self.attributes_handlers = {
            'ItemGroup_Label': self.do_nothing_attr_stub,
            'ProjectConfiguration_Include': self.__parse_project_configuration_include,
            'ClCompile_Include': self.do_nothing_attr_stub,  # TODO?
            'ClInclude_Include': self.do_nothing_attr_stub,  # TODO?
            'Condition': self.__parse_condition,
            'ProjectReference_Include': context.dependencies.add_target_reference,
        }
        self.filters = None

    def parse(self, context):
        self.filters = get_xml_data(context, context.vcxproj_path + '.filters')
        tree = context.vcxproj['tree']
        root = tree.getroot()
        self._parse_nodes(context, root)
        context.flags.apply_flags_to_context(context)
        context.files.apply_files_to_context(context)
        context.flags.define_pch_cpp_file(context)

    def __parse_item_group(self, context, node):
        self._parse_nodes(context, node)

    @staticmethod
    def __parse_project_configuration_include(context, attr_name, setting,
                                              project_configuration_node):
        if setting not in context.configurations_to_parse:
            return
        ContextInitializer.init_context_setting(context, setting)
        context.settings[setting]['PrecompiledHeader'] = ''

        # TODO: remove next
        context.property_groups[setting] = get_propertygroup(
            setting, ' and @Label="Configuration"'
        )
        context.definition_groups[setting] = get_definitiongroup(
            setting
        )

        context.current_setting = setting
        context.variables.apply_default_values(context)
        context.flags.prepare_context_for_flags(context)
        context.current_setting = None

    @staticmethod
    def __parse_configuration_type(context, node):
        context.settings[context.current_setting]['target_type'] = node.text

    def __parse_item_definition_group(self, context, node):
        self._parse_nodes(context, node)

    def __parse_property_group(self, context, node):
        self._parse_nodes(context, node)

    def __get_source_group_from_filters(self, node, filter_node_name):
        if self.filters:
            file_path = node.attrib['Include']
            filter_node = self.filters['tree'].xpath(
                '//ns:{}[@Include="{}"]/*'.format(filter_node_name, file_path),
                namespaces=self.filters['ns']
            )
            if filter_node:
                return filter_node[0].text.replace('\\', '\\\\')
            else:
                return ''

    def __parse_cl_include(self, context, node):
        if 'Include' in node.attrib:
            source_group = 'Headers'

            if self.filters:
                source_group = self.__get_source_group_from_filters(node, 'ClInclude')

            context.files.add_file_from_node(
                context,
                context.headers, node, 'Include', source_group)
            return  # TODO: handle settings of files
        self._parse_nodes(context, node)

    def __parse_cl_compile(self, context, node):
        if 'Include' in node.attrib:
            source_group = 'Sources'

            if self.filters:
                source_group = self.__get_source_group_from_filters(node, 'ClCompile')

            context.files.add_file_from_node(
                context,
                context.sources, node, 'Include', source_group)
            return  # TODO: handle settings of files
        self._parse_nodes(context, node)

    @staticmethod
    def __parse_additional_options(context, node):
        parent = node.getparent()
        parent_tag = Parser.strip_namespace(parent.tag)
        if 'ClCompile' == parent_tag:
            node.tag = 'CompileAdditionalOptions'
            context.flags.set_flag(context, node)
        if 'Link' == parent_tag:
            node.tag = 'LinkAdditionalOptions'
            context.flags.set_flag(context, node)

    @staticmethod
    def __parse_target_name_node(context, node):
        context.settings[context.current_setting]['target_name'] = replace_vs_vars_with_cmake_vars(
            context,
            node.text
        )

    def __parse_condition(self, context, attr_name, condition_value, node):
        setting = None
        found = re.search(r".*=='(.*)'", condition_value)
        if found:
            setting = found.group(1)
        if setting in context.settings:
            context.current_setting = setting
            self.reset_current_setting_after_parsing_node(node)
        else:
            context.current_setting = None
            raise StopParseException()
