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

from cmake_converter.parser import Parser
from cmake_converter.context import ContextInitializer
from cmake_converter.data_files import get_propertygroup, get_definitiongroup
from cmake_converter.utils import replace_vs_vars_with_cmake_vars


class VCXParser(Parser):

    def __init__(self, context):
        Parser.__init__(self)
        self.node_handlers = {
            'ItemGroup': self.__parse_item_group,
            'ProjectConfiguration': self.__parse_project_configuration,
            'ConfigurationType': self.__parse_configuration_type,
            'PlatformToolset': self.do_nothing_node_stub,
            'PropertyGroup': self.__parse_property_group,
            'ItemDefinitionGroup': self.__parse_item_definition_group,
            'Link': self.__parse_link_node,
            'OutputFile': context.variables.set_output_file,
            'ImportLibrary': context.variables.set_import_library,
            'OutDir': self.__parse_out_dir_node,
            'TargetName': self.__parse_target_name_node,
        }

    def parse(self, context):
        tree = context.vcxproj['tree']
        root = tree.getroot()
        self._parse_nodes(context, root)

    def __parse_item_group(self, context, item_group_node):
        self._parse_nodes(context, item_group_node)

    @staticmethod
    def __parse_project_configuration(context, project_configuration_node):
        if 'Include' in project_configuration_node.attrib:
            setting = project_configuration_node.attrib['Include']
            if setting not in context.configurations_to_parse:
                return
            ContextInitializer.init_context_setting(context, setting)
            context.current_setting = setting
            context.variables.apply_default_values(context)
            context.current_setting = None
            # TODO: remove next
            context.property_groups[setting] = get_propertygroup(
                setting, ' and @Label="Configuration"'
            )
            context.definition_groups[setting] = get_definitiongroup(
                setting
            )

    def __parse_property_group(self, context, node):
        setting = self.__get_setting_from_node(node)

        if setting is None:
            self._parse_nodes(context, node)

        if setting not in context.settings:
            return

        context.current_setting = setting
        self._parse_nodes(context, node)
        context.current_setting = None

    @staticmethod
    def __parse_configuration_type(context, node):
        context.settings[context.current_setting]['target_type'] = node.text

    def __parse_item_definition_group(self, context, node):
        setting = self.__get_setting_from_node(node)

        if setting is None:
            self._parse_nodes(context, node)

        if setting not in context.settings:
            return

        context.current_setting = setting
        self._parse_nodes(context, node)
        context.current_setting = None

    def __parse_target_name_node(self, context, node):
        setting = context.current_setting
        if setting is None:
            setting = self.__get_setting_from_node(node)

        if setting is not None:
            context.settings[setting]['target_name'] = replace_vs_vars_with_cmake_vars(
                context,
                node.text
            )

    def __parse_out_dir_node(self, context, node):
        setting = context.current_setting
        if setting is None:
            setting = self.__get_setting_from_node(node)

        if setting is not None:
            context.current_setting = setting
            context.variables.set_output_dir(context, node)
            context.current_setting = None

    def __parse_link_node(self, context, node):
        self._parse_nodes(context, node)

    @staticmethod
    def __get_setting_from_node(node):
        if 'Condition' in node.attrib:
            condition = re.search(r".*=='(.*)'", node.attrib['Condition']).group(1)
            return condition
        return None
