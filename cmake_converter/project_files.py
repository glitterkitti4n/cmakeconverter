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
    ProjectFiles
    =============
     Manages the recovery of project files
"""

import os

from cmake_converter.message import send


class ProjectFiles(object):
    """
        Class who collect and store project files
    """

    def __init__(self, data):
        self.tree = data['vcxproj']['tree']
        self.ns = data['vcxproj']['ns']
        self.cmake = data['cmake']
        self.cppfiles = self.tree.xpath('//ns:ClCompile', namespaces=self.ns)
        self.headerfiles = self.tree.xpath('//ns:ClInclude', namespaces=self.ns)
        self.language = []
        self.sources = {}
        self.headers = {}

    def get_real_file_name(self, filelist, path, name):
        """
        """
        real_name = ''
        for item in filelist:
            if item.lower() == name.lower():
                real_name = item
                break;

        filelist.remove(real_name)
        
        if real_name == '':
            raise ValueError('Filename {0} not found at filesystem.'.format(name))
        else:
            return real_name

    def collects_source_files(self):
        """
        Write the project variables in CMakeLists.txt file

        """

        filelists = {}
        cmake_dir = os.path.dirname(self.cmake.name)

        # Cpp Dir
        for cpp in self.cppfiles:
            if cpp.get('Include') is not None:
                cxx = str(cpp.get('Include'))
                cxx = '/'.join(cxx.split('\\'))
                if not cxx.rpartition('.')[-1] in self.language:
                    self.language.append(cxx.rpartition('.')[-1])
                cpp_path, cxx_file = os.path.split(cxx)
                if cpp_path not in filelists:
                    filelists[cpp_path] = os.listdir(os.path.join(cmake_dir, cpp_path))
                if cpp_path not in self.sources:
                    self.sources = {cpp_path: []}
                if cxx_file not in self.sources[cpp_path]:
                    self.sources[cpp_path].append(self.get_real_file_name(filelists[cpp_path],
                                                                          cpp_path, cxx_file))

        # Headers Dir
        for header in self.headerfiles:
            h = str(header.get('Include'))
            h = '/'.join(h.split('\\'))
            header_path, header_file = os.path.split(h)
            if header_path not in filelists:
                filelists[header_path] = os.listdir(os.path.join(cmake_dir, header_path))
            if header_path not in self.headers:
                self.headers = {header_path: []}
            if header_file not in self.headers[header_path]:
                self.headers[header_path].append(self.get_real_file_name(filelists[header_path],
                                                                        header_path, header_file))

        send("C++ Extensions found: %s" % self.language, 'INFO')

    def write_header_files(self):
        """
        Write header files variables to file() cmake function
        """
        self.cmake.write('\n############ Header Files #############\n')
        self.cmake.write('set(HEADERS_FILES\n')

        for hdrs_dir in self.headers:
            for header_file in self.headers[hdrs_dir]:
                self.cmake.write('    %s\n' % os.path.join(hdrs_dir, header_file))

        self.cmake.write(')\n')
        self.cmake.write('source_group("Headers" FILES ${HEADERS_FILES})\n\n')

    def write_source_files(self):
        """
        Write source files variables to file() cmake function
        """
        self.cmake.write('\n############ Source Files #############\n')
        self.cmake.write('set(SRC_FILES\n')

        for src_dir in self.sources:
            for src_file in self.sources[src_dir]:
                self.cmake.write('    %s\n' % os.path.join(src_dir, src_file))

        self.cmake.write(')\n')

        self.cmake.write('source_group("Sources" FILES ${SRC_FILES})\n\n')

    def add_additional_code(self, file_to_add):
        """
        Add additional file with CMake code inside

        :param file_to_add: the file who contains CMake code
        :type file_to_add: str
        """

        if file_to_add != '':
            try:
                fc = open(file_to_add)
                self.cmake.write('############# Additional Code #############\n')
                self.cmake.write('# Provides from external file.            #\n')
                self.cmake.write('###########################################\n\n')
                for line in fc:
                    self.cmake.write(line)
                fc.close()
                self.cmake.write('\n')
                send('File of Code is added = ' + file_to_add, 'warn')
            except OSError as e:
                send(str(e), 'error')
                send(
                    'Wrong data file ! Code was not added, please verify file name or path !',
                    'error'
                )
