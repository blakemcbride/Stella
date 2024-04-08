#!/usr/bin/env python

############################ BEGIN LICENSE BLOCK #############################
#                                                                            #
# Version: MPL 1.1/GPL 2.0/LGPL 2.1                                          #
#                                                                            #
# The contents of this file are subject to the Mozilla Public License        #
# Version 1.1 (the "License"); you may not use this file except in           #
# compliance with the License. You may obtain a copy of the License at       #
# http://www.mozilla.org/MPL/                                                #
#                                                                            #
# Software distributed under the License is distributed on an "AS IS" basis, #
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License   #
# for the specific language governing rights and limitations under the       #
# License.                                                                   #
#                                                                            #
# The Original Code is the STELLA Programming Language.                      #
#                                                                            #
# The Initial Developer of the Original Code is                              #
# UNIVERSITY OF SOUTHERN CALIFORNIA, INFORMATION SCIENCES INSTITUTE          #
# 4676 Admiralty Way, Marina Del Rey, California 90292, U.S.A.               #
#                                                                            #
# Portions created by the Initial Developer are Copyright (C) 1996-2020      #
# the Initial Developer. All Rights Reserved.                                #
#                                                                            #
# Contributor(s):                                                            #
#                                                                            #
# Alternatively, the contents of this file may be used under the terms of    #
# either the GNU General Public License Version 2 or later (the "GPL"), or   #
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),   #
# in which case the provisions of the GPL or the LGPL are applicable instead #
# of those above. If you wish to allow use of your version of this file only #
# under the terms of either the GPL or the LGPL, and not to allow others to  #
# use your version of this file under the terms of the MPL, indicate your    #
# decision by deleting the provisions above and replace them with the notice #
# and other provisions required by the GPL or the LGPL. If you do not delete #
# the provisions above, a recipient may use your version of this file under  #
# the terms of any one of the MPL, the GPL or the LGPL.                      #
#                                                                            #
############################# END LICENSE BLOCK ##############################

# CFFI extension builder that compiles STELLA libraries into an extension module
# that can be imported and accessed using the standard Python import machinery.
# This basically replaces the bootstrap machinery used in api.py.
# See https://cffi.readthedocs.io/en/latest/cdef.html

import sys
import os
import os.path
import subprocess
import glob
import shutil
import cffi


# NOTES, TO DO:
# - we moved stellapi.py into its own package that now also hosts libs and include files
# - we use special $ORIGIN run time library tag so we can run without LD_LIBRARY_PATH;
#   a different solution using static libs fails when connecting to other STELLA systems
# - we now pregenerate a full wrappers file to avoid having to modify it dynamically
#   in an install location
# - add more error and sanity checking to `build-stella-libs' to make sure we don't continue
#   if translation or compilation fails
# - possibly strip the resulting library files to make them smaller or use appropriate
#   compilation flags
# - possibly also refactor api.py which is getting too large, but is also very interconnected

# Shared library woes:
# - see build_libstella_wrappers.py


module_dir  = os.path.realpath(os.path.dirname(__file__))
module_libs_dir = os.path.join(module_dir, '.libs')
module_include_dir = os.path.join(module_dir, 'include')
module_sources_dir = os.path.join(module_dir, 'sources')
stella_home = os.path.realpath(os.path.join(module_dir, os.pardir, os.pardir))
stella_cpp_dir = os.path.join(stella_home, 'native', 'cpp')
stella_lib_dir = os.path.join(stella_cpp_dir, 'lib')
stella_src_dir = os.path.join(stella_home, 'sources')

libstella_module_name = 'stellapi._libstella'

# we don't need any actual code here, we simply declare all functions we need for boostrap:
libstella_wrapper = """
extern "C" void  stella_startup(int verboseP);
extern "C" void  stella_startupStellaSystem();
extern "C" void* stella_lookupFunctionCodeByName(const char* qualName);
extern "C" void* stella_lookupCCallableWrapperCodeByName(const char* qualName);
extern "C" const char* stella_lookupFunctionCppSignatureByName(const char* qualName);
extern "C" const char* stella_lookupFunctionCSignatureByName(const char* qualName);
extern "C" void* stella_lookupMethodCodeByName(const char* qualName);
extern "C" const char* stella_lookupMethodCppSignatureByName(const char* qualName);
extern "C" const char* stella_lookupMethodCSignatureByName(const char* qualName);
extern "C" const char* stella_lookupStorageSlotCppSignatureByName(const char* qualName);
extern "C" const char* stella_lookupStorageSlotCSignatureByName(const char* qualName);
extern "C" const char* stella_lookupClassCppTypeByName(const char* qualName);
extern "C" const char* stella_lookupGlobalVariableCppSignatureByName(const char* qualName);
extern "C" const char* stella_lookupGlobalVariableCSignatureByName(const char* qualName);
extern "C" void* stella_gcProtectObject(void* object);
extern "C" void* stella_gcReleaseObject(void* handle);
extern "C" void* stella_objectPrimaryClass(void* self);
extern "C" const char* stella_stringCopy(const char* string);
extern "C" const char* stella_generalizedSymbolAbsoluteName(void* self, int readableP);

extern "C" void GC_register_finalizer(void* obj, void* fn, void* cd, void** ofn, void** ocd);
extern "C" void GC_register_finalizer_ignore_self(void* obj, void* fn, void* cd, void** ofn, void** ocd);
extern "C" void GC_register_finalizer_no_order(void* obj, void* fn, void* cd, void** ofn, void** ocd);
extern "C" void GC_register_finalizer_unreachable(void* obj, void* fn, void* cd, void** ofn, void** ocd);
extern "C" void GC_gcollect(void);
extern "C" void GC_disable(void);
extern "C" void GC_enable(void);
"""

ffibuilder = cffi.FFI()

ffibuilder.set_source(libstella_module_name,
                      libstella_wrapper,
                      language='c++',
                      source_extension='.cc',
                      include_dirs=[stella_cpp_dir],
                      library_dirs=[stella_lib_dir],
                      # $ORIGIN tag is supported on ELF platforms, we might have to adjust for others:
                      runtime_library_dirs=['$ORIGIN', '$ORIGIN/.libs'],
                      libraries = ['stella', 'gc'],
                      # force a consistent SOABI extension in Py3:
                      py_limited_api = False,
)

# now make the above functions available through their respective CFFI Python wrappers
# (we need to remove the `extern "C" ' declarations first):
ffibuilder.cdef(libstella_wrapper.replace('extern "C" ', ''))


def build_stella_libs():
    """Build the requisite STELLA libraries to link against to produce _libstella.so.
    We couldn't find another way to satisfy this requirement within setup so we are doing it here.
    """
    # TO DO: this needs more error and sanity checking to make sure we don't continue if translation or compilation fails
    stella_dir =  os.path.join(stella_cpp_dir, 'stella')
    cpp_lib_dir = os.path.join(stella_dir, 'cpp-lib')
    if not os.path.exists(cpp_lib_dir):
        os.makedirs(cpp_lib_dir)

    # generate an updated STELLA translation using the STELLA system currently installed:
    # TO DO: this is a bootstrap issue which we need to handle more flexibly for target platforms such as Windows
    trans_cmd = '(translate-system "stella" :cpp :force-translation? false :recursive? true :production-settings? true)'
    subprocess.call([os.path.join(stella_home, 'stella'), '-e', trans_cmd], shell=False, cwd=stella_home)

    # C++ compile STELLA and copy relevant libs to module_directory/.libs where the setup package_data directive will find it:
    subprocess.call(['make', 'LIB-DIR=' + stella_lib_dir], shell=False, cwd=stella_dir)
    if not os.path.exists(module_libs_dir):
        os.makedirs(module_libs_dir)
    for file in (glob.glob(os.path.join(stella_lib_dir, 'libstella.*')) +
                 glob.glob(os.path.join(stella_lib_dir, 'libgc.*'))
                ):
        shutil.copy(file, module_libs_dir)

    # copy relevant include files to module directory/include/ where the package_data directive will pick it up:
    if not os.path.exists(module_include_dir):
        os.makedirs(module_include_dir)
    for file in (glob.glob(os.path.join(stella_dir, '*.h*')) +
                 glob.glob(os.path.join(cpp_lib_dir, '*.h*'))
                ):
        target = os.path.join(module_include_dir, os.path.relpath(file, stella_cpp_dir))
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        shutil.copy(file, target)
    # we copy GC-relevant include files to the top-level include dir to avoid excessive nesting:
    for file in glob.glob(os.path.join(cpp_lib_dir, 'gc', 'include', 'gc*.h')):
        target = os.path.join(module_include_dir, 'gc', os.path.basename(file))
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        shutil.copy(file, target)
    # copy relevant source files we need to translate other systems:
    for file in (glob.glob(os.path.join(stella_src_dir, 'systems', 'stella-system.ste')) +
                 glob.glob(os.path.join(stella_src_dir, 'stella', '*-default.in'))):
        target = os.path.join(module_sources_dir, os.path.relpath(file, stella_src_dir))
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        shutil.copy(file, target)


build_stella_libs()


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
