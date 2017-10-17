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
    VS Project manage the .vcxproj files and its XML data
"""

from lxml import etree

from cmake_converter.message import send


class VSProject(object):
    """
        Class who prepare data for parsing. Retrieve root xml and namespace.
    """

    def __init__(self):
        self.vcxproj = ''

    def create_data(self, vs_project):
        """
        Get xml data from vcxproj file

        :param vs_project: the vcxproj file
        :type vs_project: str
        """

        vcxproj = {}
        try:
            tree = etree.parse(vs_project)
            namespace = str(tree.getroot().nsmap)
            ns = {'ns': namespace.partition('\'')[-1].rpartition('\'')[0]}
            vcxproj['tree'] = tree
            vcxproj['ns'] = ns
            assert 'http://schemas.microsoft.com' in ns['ns']
        except AssertionError:
            send(
                '.vcxproj file cannot be import, because this file does not seem to comply with'
                ' Microsoft xml data !',
                'error'
            )
            exit(1)
        except (OSError, IOError):
            send(
                '.vcxproj file cannot be import. '
                'Please, verify you have rights to this directory or file exists !',
                'error'
            )
            exit(1)
        except etree.XMLSyntaxError:
            send('This file is not a ".vcxproj" file or XML is broken !', 'error')
            exit(1)

        return vcxproj

    @staticmethod
    def get_propertygroup(platform, target):
        """
        Return "propertygroup" value for wanted platform and target

        :param platform: wanted platform: x86 | x64
        :type platform: str
        :param target: wanted target: debug | release
        :type target: str
        :return: "propertygroup" value
        :rtype: str
        """

        prop_deb_x86 = \
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|Win32\'"]'
        prop_deb_x64 = \
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Debug|x64\'"]'
        prop_rel_x86 = \
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|Win32\'"]'
        prop_rel_x64 = \
            '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'Release|x64\'"]'

        propertygroups = {
            'debug': {
                'x86': prop_deb_x86,
                'x64': prop_deb_x64,
            },
            'release': {
                'x86': prop_rel_x86,
                'x64': prop_rel_x64
            }
        }

        return propertygroups[platform][target]

    @staticmethod
    def get_definitiongroup(platform, target):
        """

        :param platform:
        :param target:
        :return:
        """

        item_deb_x86 = \
            '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
            '$(Platform)\'==\'Debug|Win32\'"]'
        item_deb_x64 = \
            '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
            '$(Platform)\'==\'Debug|x64\'"]'
        item_rel_x86 = \
            '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
            '$(Platform)\'==\'Release|Win32\'"]'
        item_rel_x64 = \
            '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
            '$(Platform)\'==\'Release|x64\'"]'

        itemdefinitiongroups = {
            'debug': {
                'x86': item_deb_x86,
                'x64': item_deb_x64,
            },
            'release': {
                'x86': item_rel_x86,
                'x64': item_rel_x64
            }
        }

        return itemdefinitiongroups[platform][target]
