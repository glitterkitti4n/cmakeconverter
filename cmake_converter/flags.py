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
    Flags
    =====
     Manage compilation flags of project
"""

import os

from os import path

from cmake_converter.message import send
from cmake_converter.utils import take_name_from_list_case_ignore, get_configuration_type\
    , write_property_of_settings, set_unix_slash, normalize_path

cl_flags = 'cl_flags'
ln_flags = 'ln_flags'
defines = 'defines'
default_value = 'default_value'


class Flags(object):
    """

    """

    def __init__(self, context):
        self.context = context
        self.tree = context['vcxproj']['tree']
        self.ns = context['vcxproj']['ns']
        self.cmake = context['cmake']
        self.settings = context['settings']

    def write_defines_and_flags(self, compiler_check):
        """
        Get and write Preprocessor Macros definitions

        """
        cmake = self.cmake

        # normalize
        for setting in self.settings:
            self.settings[setting]['defines_str'] = ';'.join(self.settings[setting][defines])
            self.settings[setting]['cl_str'] = ';'.join(self.settings[setting][cl_flags])

        write_property_of_settings(cmake, self.settings, 'target_compile_definitions(${PROJECT_NAME} PRIVATE', ')',
                                   'defines_str')
        cmake.write('\n')
        cmake.write('if({0})\n'.format(compiler_check))
        write_property_of_settings(cmake, self.settings, 'target_compile_options(${PROJECT_NAME} PRIVATE', ')',
                                   'cl_str', indent='    ')

        settings_of_arch = {}
        for setting in self.settings:
            arch = self.settings[setting]['arch']
            if arch not in settings_of_arch:
                settings_of_arch[arch] = {}
            settings_of_arch[arch][setting] = self.settings[setting]

        first_arch = True
        for arch in settings_of_arch:
            if first_arch:
                cmake.write('    if(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{0}\")\n'.format(arch))
            else:
                cmake.write('    elseif(\"${{CMAKE_VS_PLATFORM_NAME}}\" STREQUAL \"{0}\")\n'.format(arch))
            first_arch = False
            for setting in settings_of_arch[arch]:
                conf = self.settings[setting]['conf']
                if self.settings[setting][ln_flags]:
                    configuration_type = get_configuration_type(setting, self.context)
                    if configuration_type:
                        if 'StaticLibrary' in configuration_type:
                            cmake.write(
                                '        set_target_properties(${{PROJECT_NAME}}'
                                ' PROPERTIES STATIC_LIBRARY_FLAGS_{0} "{1}")\n'
                                .format(conf.upper(), ' '.join(self.settings[setting][ln_flags]))
                            )
                        else:
                            cmake.write(
                                '        set_target_properties(${{PROJECT_NAME}} PROPERTIES LINK_FLAGS_{0} "{1}")\n'
                                .format(conf.upper(), ' '.join(self.settings[setting][ln_flags]))
                            )
        cmake.write('    else()\n')
        cmake.write(
            '         message(WARNING "${CMAKE_VS_PLATFORM_NAME} arch is not supported!")\n')
        cmake.write('    endif()\n')
        cmake.write('endif()\n\n')


class CPPFlags(Flags):
    """
        Class who check and create compilation flags
    """

    available_std = ['c++11', 'c++14', 'c++17']

    def __init__(self, context):
        Flags.__init__(self, context)
        self.propertygroup = context['property_groups']
        self.definitiongroups = context['definition_groups']
        self.std = context['std']

    def get_setting_name(self, setting):
        return self.settings[setting]['conf']

    def get_cmake_configuration_types(self):
        configuration_types = []
        for setting in self.settings:
            configuration_types.append(self.get_setting_name(setting))
        return configuration_types

    def define_flags(self):
        """
        Parse all flags properties and write them inside "CMakeLists.txt" file

        """
        self.define_windows_flags()
        self.define_defines()
        # self.define_linux_flags() # TODO: redo with generator expression for each setting(configuration)

    def define_linux_flags(self):
        """
        Define the Flags for Linux platforms

        """

        if self.std:
            if self.std in self.available_std:
                send('Cmake will use C++ std %s.' % self.std, 'info')
                linux_flags = '-std=%s' % self.std
            else:
                send(
                    'C++ std %s version does not exist. CMake will use "c++11" instead' % self.std,
                    'warn'
                )
                linux_flags = '-std=c++11'
        else:
            send('No C++ std version specified. CMake will use "c++11" by default.', 'info')
            linux_flags = '-std=c++11'
        references = self.tree.xpath('//ns:ProjectReference', namespaces=self.ns)
        if references:
            for ref in references:
                reference = str(ref.get('Include'))
                if '\\' in reference:
                    reference = set_unix_slash(reference)
                lib = os.path.splitext(path.basename(reference))[0]

                if (lib == 'lemon' or lib == 'zlib') and '-fPIC' not in linux_flags:
                    linux_flags += ' -fPIC'

        self.cmake.write('if(NOT MSVC)\n')
        self.cmake.write('   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} %s")\n' % linux_flags)
        self.cmake.write('   if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")\n')
        self.cmake.write('       set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")\n')
        self.cmake.write('   endif()\n')
        self.cmake.write('endif(NOT MSVC)\n\n')

    def define_defines(self):
        """
        DEFINES
        """
        # PreprocessorDefinitions
        for setting in self.settings:
            define = self.tree.find(
                '{0}/ns:ClCompile/ns:PreprocessorDefinitions'.format(self.definitiongroups[setting]),
                namespaces=self.ns
            )
            if define is not None:
                for preproc in define.text.split(";"):
                    if preproc != '%(PreprocessorDefinitions)' and preproc != 'WIN32':
                        self.settings[setting][defines].append(preproc)
                # Unicode
                character_set = self.tree.xpath(
                    '{0}/ns:CharacterSet'.format(self.propertygroup[setting]),
                    namespaces=self.ns)
                if character_set is not None:
                    if 'Unicode' in character_set[0].text:
                        self.settings[setting][defines].append('UNICODE')
                        self.settings[setting][defines].append('_UNICODE')
                    if 'MultiByte' in character_set[0].text:
                        self.settings[setting][defines].append('_MBCS')
                send('PreprocessorDefinitions for {0}'.format(setting), 'ok')

    def do_precompiled_headers(self, files):
        precompiled_header_path = ''
        for setting in self.settings:
            precompiled_header_values = {'Use': {'PrecompiledHeader': 'Use'},
                                         'NotUsing': {'PrecompiledHeader': 'NotUsing'},
                                         'Create': {'PrecompiledHeader': 'Create'},
                                         default_value: {'PrecompiledHeader': 'NotUsing'}}
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:PrecompiledHeader'
                          .format(self.definitiongroups[setting]),
                          precompiled_header_values)

            precompiled_header_file_values = {default_value: {'PrecompiledHeaderFile': 'stdafx.h'}}
            flag_value = self.set_flag(setting,
                                       '{0}/ns:ClCompile/ns:PrecompiledHeaderFile'
                                       .format(self.definitiongroups[setting]), precompiled_header_file_values)
            if flag_value != '':
                self.settings[setting]['PrecompiledHeaderFile'] = [flag_value]

            if self.settings[setting]['PrecompiledHeader'][0] == 'Use':
                pch_flag_value = self.settings[setting]['PrecompiledHeaderFile'][0]
                found = False
                founded_pch_h_path = ''
                for headers_path in files.headers:
                    for header in files.headers[headers_path]:
                        if header.lower() == pch_flag_value.lower():
                            found = True
                            founded_pch_h_path = headers_path
                        if found:
                            break
                    if found:
                        break

                if precompiled_header_path == '':
                    pch_cpp = self.settings[setting]['PrecompiledHeaderFile'][0].replace('.h', '.cpp')
                    real_pch_cpp = take_name_from_list_case_ignore(files.sources[founded_pch_h_path], pch_cpp)
                    if founded_pch_h_path != '':
                        founded_pch_h_path += '/'
                    real_pch_cpp = founded_pch_h_path + real_pch_cpp
                    precompiled_header_path = real_pch_cpp.replace('.cpp', '.h')
                self.settings[setting]['PrecompiledHeaderFile'][0] = precompiled_header_path

    def define_windows_flags(self):
        """
        Define the Flags for Win32 platforms

        """

        # Define FLAGS for Windows

        # from propertygroup
        #   compilation
        self.set_use_debug_libraries()
        self.set_whole_program_optimization()
        #   linking
        self.set_generate_debug_information()
        self.set_link_incremental()

        # from definitiongroups
        #   compilation
        self.set_optimization()
        self.set_intrinsic_functions()
        self.set_string_pooling()
        self.set_basic_runtime_checks()
        self.set_runtime_library()
        self.set_function_level_linking()
        self.set_warning_level()
        self.set_warning_as_errors()
        self.set_debug_information_format()
        self.set_floating_point_model()
        self.set_runtime_type_info()
        self.set_disable_specific_warnings()
        self.set_additional_options()
        self.set_exception_handling()
        self.set_buffer_security_check()
        self.set_diagnostics_format()
        self.set_treatwchar_t_as_built_in_type()
        self.set_force_conformance_in_for_loop_scope()
        self.set_remove_unreferenced_code_data()

    def set_flag(self, setting, xpath, flag_values):
        """
        Set flag helper
        """
        flag_element = self.tree.xpath(xpath, namespaces=self.ns)

        values = None
        if default_value in flag_values:
            values = flag_values[default_value]

        flag_text = ''
        if flag_element:
            flag_text = flag_element[0].text
            if flag_text in flag_values:
                values = flag_values[flag_text]

        flags_message = ''
        if values is not None:
            for key in values:
                value = values[key]
                if key not in self.settings[setting]:
                    self.settings[setting][key] = []
                self.settings[setting][key].append(value)
                flags_message += value

        flag_name = xpath.split(':')[-1]
        send('{0} for {1} is {2} '.format(flag_name, setting, flags_message), '')
        return flag_text

    def set_whole_program_optimization(self):
        """
        Set Whole Program Optimization flag: /GL and /LTCG

        """

        flag_values = {'true': {ln_flags: '/LTCG', cl_flags: '/GL'}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:WholeProgramOptimization'.format(self.propertygroup[setting]),
                          flag_values)

    def set_link_incremental(self):
        """
        Set LinkIncremental flag: /INCREMENTAL

        """

        flag_values = {'true':  {ln_flags: '/INCREMENTAL'},
                       'false': {ln_flags: '/INCREMENTAL:NO'},
                       default_value: {}
                       }

        for setting in self.settings:
            conf_type = get_configuration_type(setting, self.context)
            if conf_type and 'StaticLibrary' in conf_type:
                continue
            value = self.set_flag(setting, '{0}/ns:LinkIncremental'
                                  .format(self.propertygroup[setting].replace(' and @Label="Configuration"', '')),
                                  flag_values)
            if not value:
                value = self.set_flag(setting,
                                      '//ns:LinkIncremental[@Condition="\'$(Configuration)|$(Platform)\'==\'{0}\'"]'
                                      .format(setting), flag_values)
            if not value:
                self.settings[setting][ln_flags].append('/INCREMENTAL')  # default

    def set_force_conformance_in_for_loop_scope(self):
        """
        Set flag: ForceConformanceInForLoopScope

        """

        flag_values = {'true':  {cl_flags: '/Zc:forScope'},
                       'false': {cl_flags: '/Zc:forScope-'},
                       default_value: {cl_flags: '/Zc:forScope'}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:ForceConformanceInForLoopScope'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_remove_unreferenced_code_data(self):
        """
        Set flag: RemoveUnreferencedCodeData

        """

        flag_values = {'true':  {cl_flags: '/Zc:inline'},
                       'false': {cl_flags: ''},
                       default_value: {cl_flags: '/Zc:inline'}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:RemoveUnreferencedCodeData'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_use_debug_libraries(self):
        """
        Set Use Debug Libraries flag: /MD

        """
        for setting in self.settings:
            md = self.tree.xpath('{0}/ns:UseDebugLibraries'.format(self.propertygroup[setting]), namespaces=self.ns)
            if md:
                if 'true' in md[0].text:
                    self.settings[setting]['use_debug_libs'] = True
                else:
                    self.settings[setting]['use_debug_libs'] = False
                send('UseDebugLibrairies for {0}'.format(setting), 'ok')
            else:
                send('No UseDebugLibrairies for {0}'.format(setting), '')

    def set_warning_level(self):
        """
        Set Warning level for Windows: /W

        """
        flag_values = {'Level1': {cl_flags: '/W1'},
                       'Level2': {cl_flags: '/W2'},
                       'Level3': {cl_flags: '/W3'},
                       'Level4': {cl_flags: '/W4'},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:WarningLevel'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_warning_as_errors(self):
        """
        Set TreatWarningAsError /WX

        """
        flag_values = {'true': {cl_flags: '/WX'},
                       'false': {},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:TreatWarningAsError'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_disable_specific_warnings(self):
        """
        Set DisableSpecificWarnings

        """
        for setting in self.settings:
            specific_warnings_node = self.tree.xpath('{0}/ns:ClCompile/ns:DisableSpecificWarnings'
                                                     .format(self.definitiongroups[setting]), namespaces=self.ns)
            if specific_warnings_node:
                for sw in specific_warnings_node[0].text.strip().split(";"):
                    sw = sw.strip()
                    if sw != '%(DisableSpecificWarnings)':
                        self.settings[setting][cl_flags].append('/wd{0}'.format(sw))
                send('DisableSpecificWarnings for {0} : {1}'.format(setting, specific_warnings_node[0].text.strip()),
                     'ok')
            else:
                send('No Additional Options for {0}'.format(setting), '')

    def set_additional_options(self):
        """
        Set Additional options

        """
        for setting in self.settings:
            add_opt = self.tree.xpath('{0}/ns:ClCompile/ns:AdditionalOptions'
                                      .format(self.definitiongroups[setting]), namespaces=self.ns)
            if add_opt:
                for opt in add_opt[0].text.strip().split(" "):
                    opt = opt.strip()
                    if opt != '' and opt != '%(AdditionalOptions)':
                        self.settings[setting][cl_flags].append(opt)
                    send('Additional Options for {0} : {1}'.format(setting, opt), 'ok')
            else:
                send('No Additional Options for {0}'.format(setting), '')

    def set_basic_runtime_checks(self):
        """
        """
        flag_values = {'StackFrameRuntimeCheck': {cl_flags: '/RTCs'},
                       'UninitializedLocalUsageCheck': {cl_flags: '/RTCu'},
                       'EnableFastChecks': {cl_flags: '/RTC1'},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:BasicRuntimeChecks'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_runtime_library(self):
        """
        Set RuntimeLibrary flag: /MDd

        """

        # RuntimeLibrary
        for setting in self.settings:
            mdd_value = self.tree.find('{0}/ns:ClCompile/ns:RuntimeLibrary'.format(self.definitiongroups[setting]),
                                       namespaces=self.ns)
            mdd = '/MDd'
            m_d = '/MD'
            mtd = '/MTd'
            m_t = '/MT'

            if 'use_debug_libs' in self.settings[setting]:
                if self.settings[setting]['use_debug_libs']:
                    m_d = '/MDd'
                    m_t = '/MTd'
                else:
                    mdd = '/MD'
                    mtd = '/MT'

            cl_flag_value = ''
            if mdd_value is not None:
                if 'MultiThreadedDebugDLL' == mdd_value.text:
                    cl_flag_value = mdd
                if 'MultiThreadedDLL' == mdd_value.text:
                    cl_flag_value = m_d
                if 'MultiThreaded' == mdd_value.text:
                    cl_flag_value = m_t
                if 'MultiThreadedDebug' == mdd_value.text:
                    cl_flag_value = mtd
                send('RuntimeLibrary {0} for {1}'.format(mdd_value.text, setting), 'ok')
            else:
                cl_flag_value = m_d  # default
                send('Default RuntimeLibrary {0} for {1}'.format(m_d, setting), '')

            if cl_flag_value:
                self.settings[setting][cl_flags].append(cl_flag_value)

    def set_string_pooling(self):
        """
        Set StringPooling flag: /GF

        """
        flag_values = {'true': {cl_flags: '/GF'},
                       'false': {cl_flags: '/GF-'},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:StringPooling'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_optimization(self):
        """
        Set Optimization flag: /Od

        """
        flag_values = {'Disabled': {cl_flags: '/Od'},
                       'MinSpace': {cl_flags: '/O1'},
                       'MaxSpeed': {cl_flags: '/O2'},
                       'Full': {cl_flags: '/Ox'},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:Optimization'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_intrinsic_functions(self):
        """
        Set Intrinsic Functions flag: /Oi

        """
        flag_values = {'true': {cl_flags: '/Oi'},
                       'false': {},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:IntrinsicFunctions'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_runtime_type_info(self):
        """
        Set RuntimeTypeInfo flag: /GR

        """
        flag_values = {'true': {cl_flags: '/GR'},
                       'false': {},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:RuntimeTypeInfo'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_function_level_linking(self):
        """
        Set FunctionLevelLinking flag: /Gy

        """
        flag_values = {'true': {cl_flags: '/Gy'},
                       'false': {},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:FunctionLevelLinking'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_debug_information_format(self):
        """
        Set GenerateDebugInformation flag: /Zi

        """
        flag_values = {'ProgramDatabase': {cl_flags: '/Zi'},
                       'EditAndContinue': {cl_flags: '/ZI'},
                       default_value: {}}

        for setting in self.settings:
            self.set_flag(setting,
                          '{0}/ns:ClCompile/ns:DebugInformationFormat'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_generate_debug_information(self):
        """
        Set GenerateDebugInformation flag: /DEBUG

        """

        for setting in self.settings:
            deb = self.tree.find(
                '{0}/ns:Link/ns:GenerateDebugInformation'.format(self.definitiongroups[setting]),
                namespaces=self.ns
            )
            if deb is not None:
                if 'true' in deb.text:
                    conf_type = get_configuration_type(setting, self.context)
                    if conf_type and 'StaticLibrary' in conf_type:
                        continue
                    self.settings[setting][ln_flags].append('/DEBUG')
                    send('GenerateDebugInformation for {0}'.format(setting), 'ok')
            else:
                send('No GenerateDebugInformation for {0}'.format(setting), '')

    def set_floating_point_model(self):
        """
        Set FloatingPointModel flag: /fp

        """
        flag_values = {'Precise': {cl_flags: '/fp:precise'},
                       'Strict': {cl_flags: '/fp:strict'},
                       'Fast': {cl_flags: '/fp:fast'},
                       default_value: {cl_flags: '/fp:precise'}}

        for setting in self.settings:
            self.set_flag(setting, '{0}/ns:ClCompile/ns:FloatingPointModel'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_exception_handling(self):
        """
        Set ExceptionHandling flag: /EHsc

        """
        flag_values = {'false': {},
                       'true': {cl_flags: '/EHsc'},
                       default_value: {cl_flags: '/EHsc'}}

        for setting in self.settings:
            self.set_flag(setting, '{0}/ns:ClCompile/ns:ExceptionHandling'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_buffer_security_check(self):
        """
        Set BufferSecurityCheck flag: /GS

        """
        flag_values = {'false': {},
                       'true': {cl_flags: '/GS'},
                       default_value: {cl_flags: '/GS'}}

        for setting in self.settings:
            self.set_flag(setting, '{0}/ns:ClCompile/ns:BufferSecurityCheck'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_diagnostics_format(self):
        """
        Set DiagnosticsFormat flag : /GS
        
        """
        flag_values = {'Classic': {cl_flags: '/diagnostics:classic'},
                       'Column': {cl_flags: '/diagnostics:column'},
                       'Caret': {cl_flags: '/diagnostics:caret'},
                       default_value: {cl_flags: '/diagnostics:classic'}}

        for setting in self.settings:
            self.set_flag(setting, '{0}/ns:ClCompile/ns:DiagnosticsFormat'
                          .format(self.definitiongroups[setting]),
                          flag_values)

    def set_treatwchar_t_as_built_in_type(self):
        """
        Set TreatWChar_tAsBuiltInType /Zc:wchar_t

        """
        flag_values = {'false': {cl_flags: '/Zc:wchar_t-'},
                       'true': {cl_flags: '/Zc:wchar_t'},
                       default_value: {cl_flags: '/Zc:wchar_t'}}

        for setting in self.settings:
            self.set_flag(setting, '{0}/ns:ClCompile/ns:TreatWChar_tAsBuiltInType'
                          .format(self.definitiongroups[setting]),
                          flag_values)
    
    def setting_has_pch(self, setting):
        """
        """
        has_pch = self.settings[setting]['PrecompiledHeader']
        return 'Use' in has_pch

    def write_precompiled_headers_macro(self):
        """
        """
        need_pch_macro = False
        for setting in self.settings:
            if self.setting_has_pch(setting):
                need_pch_macro = True
                break

        if need_pch_macro:
            cmake = self.cmake
            cmake.write(
                'MACRO(ADD_PRECOMPILED_HEADER PrecompiledHeader PrecompiledSource SourcesVar)\n'
                '    if(MSVC)\n'
                '        set(PrecompiledBinary "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.pch")\n'
                '        SET_SOURCE_FILES_PROPERTIES(${PrecompiledSource}\n'
                '                                    PROPERTIES COMPILE_FLAGS "/Yc\\"${PrecompiledHeader}\\"'
                ' /Fp\\"${PrecompiledBinary}\\""\n'
                '                                               OBJECT_OUTPUTS "${PrecompiledBinary}")\n'
                '        SET_SOURCE_FILES_PROPERTIES(${${SourcesVar}}\n'
                '                                    PROPERTIES COMPILE_FLAGS "/Yu\\"${PrecompiledHeader}\\"'
                ' /FI\\"${PrecompiledHeader}\\" /Fp\\"${PrecompiledBinary}\\""\n'
                '                                               OBJECT_DEPENDS "${PrecompiledBinary}")\n'
                '    endif()\n'
                '    LIST(INSERT ${SourcesVar} 0 ${PrecompiledSource})\n'
                'ENDMACRO(ADD_PRECOMPILED_HEADER)\n\n'
            )

    def write_precompiled_headers(self, setting):
        """
        """
        if not self.setting_has_pch(setting):
            return

        pch = self.settings[setting]['PrecompiledHeaderFile'][0]
        self.cmake.write('ADD_PRECOMPILED_HEADER("{0}" "{1}" SRC_FILES)\n\n'.format(os.path.basename(pch),
                                                                                    pch.replace('.h', '.cpp')))

    def write_target_artifact(self):
        """
        Add Library or Executable target

        """
        setting = ''
        for s in self.settings:
            setting = s
 
        self.cmake.write('# Warning: pch and target are the same for every configuration\n')
        self.write_precompiled_headers(setting)

        configuration_type = None
        for s in self.settings:
            configuration_type = get_configuration_type(s, self.context)
            if configuration_type:
                break
        if configuration_type:
            if configuration_type == 'DynamicLibrary':
                self.cmake.write('add_library(${PROJECT_NAME} SHARED')
                send('CMake will build a SHARED Library.', '')
            elif configuration_type == 'StaticLibrary':  # pragma: no cover
                self.cmake.write('add_library(${PROJECT_NAME} STATIC')
                send('CMake will build a STATIC Library.', '')
            else:  # pragma: no cover
                self.cmake.write('add_executable(${PROJECT_NAME} ')
                send('CMake will build an EXECUTABLE.', '')
            self.cmake.write(' ${SRC_FILES}')
            self.cmake.write(')\n\n')


class FortranFlags(Flags):
    """

    """
    def __init__(self, context):
        Flags.__init__(self, context)
        self.vcxproj_path = context['vcxproj_path']

    def define_flags(self):
        """
        Parse all flags properties and write them inside "CMakeLists.txt" file

        """
        self.set_source_file_format()
        self.set_local_variable_storage()
        self.set_real_kind()
        self.set_additional_options()

    def set_source_file_format(self):
        for setting in self.settings:
            opt = self.settings[setting]['VFFortranCompilerTool'].get('SourceFileFormat')
            if opt == 'fileFormatFree':
                self.settings[setting][cl_flags].append('/free')

    def set_local_variable_storage(self):
        for setting in self.settings:
            opt = self.settings[setting]['VFFortranCompilerTool'].get('LocalVariableStorage')
            if opt == 'localStorageAutomatic':
                self.settings[setting][cl_flags].append('/Qauto')

    def set_real_kind(self):
        for setting in self.settings:
            opt = self.settings[setting]['VFFortranCompilerTool'].get('RealKIND')
            if opt == 'realKIND8':
                self.settings[setting][cl_flags].append('/real_size:64')
            if opt == 'realKIND16':
                self.settings[setting][cl_flags].append('/real_size:128')

    def set_additional_options(self):
        """
        Set Additional options

        """
        for setting in self.settings:
            add_opts = self.settings[setting]['VFFortranCompilerTool'].get('AdditionalOptions')
            if add_opts:
                add_opts = set_unix_slash(add_opts).split(' ')
                ready_add_opts = []
                for add_opt in add_opts:
                    add_opt = add_opt.strip()
                    if '/Qprof-dir' in add_opt:
                        name_value = add_opt.split(':')
                        add_opt = name_value[0] + ':' + normalize_path(os.path.dirname(self.vcxproj_path),
                                                                       name_value[1])
                    ready_add_opts.append(add_opt)
                self.settings[setting][cl_flags].append(';'.join(ready_add_opts))
                send('Additional Options for {0} : {1}'.format(setting, str(add_opt)), 'ok')
            else:
                send('No Additional Options for {0}'.format(setting), '')

    def write_target_artifact(self):
        """
        Add Library or Executable target

        """

        send('CMake will build a STATIC Library.', '')
        self.cmake.write('add_library(${PROJECT_NAME} STATIC')
        self.cmake.write(' ${SRC_FILES}')
        self.cmake.write(')\n\n')
