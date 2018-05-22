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
    Data Files
    ==========
     Manage the **VS Project** data and creation of **CMakeLists.txt** file
"""

from lxml import etree

from cmake_converter.message import send
import os


def get_vcxproj_data(vs_project):
    """
    Return xml data from "vcxproj" file

    :param vs_project: the vcxproj file
    :type vs_project: str
    :return: dict with VS Project data
    :rtype: dict
    """

    vcxproj = {}
    vs_project = '/'.join(vs_project.split('\\'))

    try:
        tree = etree.parse(vs_project)
        namespace = str(tree.getroot().nsmap)
        ns = {'ns': namespace.partition('\'')[-1].rpartition('\'')[0]}
        vcxproj['tree'] = tree
        vcxproj['ns'] = ns
        assert 'http://schemas.microsoft.com' in ns['ns']
    except AssertionError:  # pragma: no cover
        send(
            '.vcxproj file cannot be import, because this file does not seem to comply with'
            ' Microsoft xml data !',
            'error'
        )
        exit(1)
    except (OSError, IOError):  # pragma: no cover
        send(
            '%s file cannot be import. '
            'Please, verify you have rights to this directory or file exists !' % vs_project,
            'error'
        )
        exit(1)
    except etree.XMLSyntaxError:  # pragma: no cover
        send('This file is not a ".vcxproj" file or XML is broken !', 'error')
        exit(1)

    return vcxproj


def get_xml_data(xml_file):
    """
    Return xml data from "xml" file

    :param xml_file: the xml file
    :type xml_file: str
    :return: dict with VS Project data
    :rtype: dict
    """

    xml = {}
    xml_file = '/'.join(xml_file.split('\\'))

    if not os.path.exists(xml_file):
        send(
            '{0} file not exists. '.format(xml_file),
            'error'
        )
        return None

    try:
        tree = etree.parse(xml_file)
        namespace = str(tree.getroot().nsmap)
        ns = {'ns': namespace.partition('\'')[-1].rpartition('\'')[0]}
        xml['tree'] = tree
        xml['ns'] = ns
        #assert 'http://schemas.microsoft.com' in ns['ns']
    except AssertionError:  # pragma: no cover
        send(
            '.xml file cannot be import, because this file does not seem to comply with'
            ' Microsoft xml data !',
            'error'
        )
        exit(1)
    except (OSError, IOError):  # pragma: no cover
        send(
            '%s file cannot be import. '
            'Please, verify you have rights to this directory or file exists !' % xml_file,
            'error'
        )
        exit(1)
    except etree.XMLSyntaxError:  # pragma: no cover
        send('This file is not a ".xml" file or XML is broken !', 'error')
        exit(1)

    return xml


def get_propertygroup(target_platform, attributes=''):
    """
    Return "propertygroup" value for wanted platform and target

    :param target_platform: wanted target: debug | release
    :type target_platform: str
    :param attributes: attributes to add to namespace
    :type attributes: str
    :return: "propertygroup" value
    :rtype: str
    """

    prop = \
        '//ns:PropertyGroup[@Condition="\'$(Configuration)|$(Platform)\'==\'{0}\'"{1}]'.format(
            target_platform, attributes)

    return prop


def get_definitiongroup(target_platform):
    """
    Return ItemDefinitionGroup namespace depends on platform and target

    :param target_platform: wanted target: debug | release
    :type target_platform: str
    :return: wanted ItemDefinitionGroup namespace
    :rtype: str
    """

    item = \
        '//ns:ItemDefinitionGroup[@Condition="\'$(Configuration)|' \
        '$(Platform)\'==\'{0}\'"]'.format(target_platform)

    return item


def get_cmake_lists(cmake_path=None, open_type='w'):
    """
    Create CMakeLists.txt file in wanted "cmake_path"

    :param cmake_path: path where CMakeLists.txt should be open
    :type cmake_path: str
    :param open_type: type that CMakeLists.txt should be opened
    :type open_type: str
    :return: cmake file wrapper opened
    :rtype: _io.TextIOWrapper
    """

    cmake = ''
    if not cmake_path:
        if open_type == 'w':
            send('CMakeLists will be written at current directory.', '')
        cmake = os.path.join(os.getcwd(), 'CMakeLists.txt')
    else:
        if open_type == 'w':
            send('CmakeLists.txt will be written at : ' + str(cmake_path), 'warn')
        if cmake_path[-1:] == '/' or cmake_path[-1:] == '\\':
            cmake = str(cmake_path) + 'CMakeLists.txt'
        else:
            cmake = str(cmake_path) + '/CMakeLists.txt'

    if not os.path.exists(cmake) and open_type == 'r':
        return None

    return open(cmake, open_type)
