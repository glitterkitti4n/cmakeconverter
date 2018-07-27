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

from cmake_converter.utils import message


class StopParseException(Exception):
    pass


class Parser(object):

    def __init__(self):
        self.node_handlers = {
        }
        self.attributes_handlers = {
        }
        self.reset_setting_after_nodes = set()

    @staticmethod
    def parse(context):
        message(context, 'Parser is not implemented yet!', 'error')

    @staticmethod
    def do_nothing_node_stub(context, node):
        pass

    @staticmethod
    def do_nothing_attr_stub(context, param, node):
        pass

    def reset_current_setting_after_parsing_node(self, node):
        self.reset_setting_after_nodes.add(node)

    @staticmethod
    def strip_namespace(tag):
        return re.sub(r'{.*\}', '', tag)

    def _parse_nodes(self, context, parent):
        for child_node in parent:
            if type(child_node.tag) is not str:
                continue
            child_node_tag = Parser.strip_namespace(child_node.tag)

            try:
                self._parse_attributes(context, child_node)
            except StopParseException:
                continue

            if child_node_tag in self.node_handlers:
                self.node_handlers[child_node_tag](context, child_node)
            else:
                message(context, 'No handler for <{}> node.'.format(child_node_tag), 'warn')

            if child_node in self.reset_setting_after_nodes:
                context.current_setting = None
                self.reset_setting_after_nodes.remove(child_node)

    def _parse_attributes(self, context, node):
        for attr in node.attrib:
            node_tag = re.sub(r'{.*\}', '', node.tag)  # strip namespace
            key = '{}_{}'.format(node_tag, attr)
            if key in self.attributes_handlers:
                self.attributes_handlers[key](context, node.get(attr), node)
            else:
                message(
                    context,
                    'No handler for "{}" attribute of <{}> node.'.format(attr, node_tag),
                    'warn'
                )

    @staticmethod
    def remove_unused_settings(context):
        mapped_configurations = set()
        for sln_config in context.sln_configurations_map:
            mapped_configurations.add(context.sln_configurations_map[sln_config])
        settings_to_remove = []
        for setting in context.settings:
            if setting not in mapped_configurations:
                settings_to_remove.append(setting)
        for setting in settings_to_remove:
            context.settings.pop(setting, None)
