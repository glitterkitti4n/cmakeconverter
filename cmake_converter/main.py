#!/usr/bin/env python3
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

"""
    Main
    ====
     Manage script arguments and launch
"""

import argparse
import os

from cmake_converter.context import Context
from cmake_converter.visual_studio.solution import convert_solution, convert_project,\
    clean_cmake_lists_file, copy_cmake_utils
from cmake_converter.utils import message


def main():  # pragma: no cover
    """
    Define arguments and message to DataConverter()

    """

    usage = "cmake-converter -p <vcxproj> " \
            "[-c | -a | -D | -O | -i | -v | -std | -dry | -verbose | -j]"
    # Init parser
    parser = argparse.ArgumentParser(
        usage=usage,
        description='Convert Visual Studio projects (.vcxproj) to CMakeLists.txt'
    )
    parser.add_argument(
        '-s', '--solution',
        help='valid solution file. i.e.: ../../my.sln',
        dest='solution'
    )
    parser.add_argument(
        '-p', '--project',
        help='[required] valid vcxproj file. i.e.: ../../mylib.vcxproj',
        dest='project'
    )
    parser.add_argument(
        '-c', '--cmake',
        help='define output of CMakeLists.txt file',
        dest='cmake'
    )
    parser.add_argument(
        '-a', '--additional',
        help='import cmake code from file.cmake to your final CMakeLists.txt',
        dest='additional'
    )
    parser.add_argument(
        '-D', '--dependencies',
        help='replace dependencies found in .vcxproj, separated by colons. '
             'i.e.: external/zlib/cmake/:../../external/g3log/cmake/',
        dest='dependencies'
    )
    parser.add_argument(
        '-O', '--cmakeoutput',
        help='define output of artefact produces by CMake.',
        dest='cmakeoutput'
    )
    parser.add_argument(
        '-dry', '--dry-run',
        help='run converter without writing files.',
        dest='dry',
        action='store_true'
    )
    parser.add_argument(
        '-v', '--verbose-mode',
        help='run converter without info messages in log.',
        dest='verbose',
        action='store_true'
    )
    parser.add_argument(
        '-w', '--warning-level',
        help='run converter with given verbocity of warnings([1..4]default=3).',
        dest='warn',
    )
    parser.add_argument(
        '-j', '--jobs',
        help='run converter using given number of processes.',
        dest='jobs',
    )
    parser.add_argument(
        '-std', '--std',
        help='choose your C++ std version. Default : c++11',
        dest='std'
    )

    # Get args
    args = parser.parse_args()

    if not args.project and not args.solution:
        parser.print_help()
        exit(0)

    initial_context = Context()

    # Prepare context
    initial_context.additional_code = args.additional
    if args.dependencies:
        initial_context.dependencies = args.dependencies.split(':')
    initial_context.cmake_output = args.cmakeoutput

    if args.std:
        initial_context.std = args.std

    if args.dry:
        initial_context.dry = True
        message(initial_context, 'Converter runs in dry mode', 'done')

    if args.verbose:
        initial_context.verbose = True
        message(initial_context, 'Converter runs in verbose mode', 'done')

    if args.jobs:
        initial_context.jobs = int(args.jobs)
    message(initial_context, 'processes count = {}'. format(initial_context.jobs), 'done')

    if args.warn:
        initial_context.warn_level = int(args.warn)
    message(initial_context, 'warnings level = {}'. format(initial_context.warn_level), 'done')

    if not args.solution:
        cmake_lists_path = os.path.dirname(os.path.abspath(args.project))
        if args.cmake:
            cmake_lists_path = args.cmake
        clean_cmake_lists_file(initial_context, cmake_lists_path, set())
        project_abs_path = os.path.abspath(args.project)
        convert_project(initial_context, project_abs_path, cmake_lists_path)
        copy_cmake_utils(os.path.dirname(project_abs_path))
    else:
        convert_solution(initial_context, os.path.abspath(args.solution))


if __name__ == "__main__":  # pragma: no cover
    main()
