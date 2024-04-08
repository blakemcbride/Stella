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

import sys
import sysconfig
import os
import os.path
import subprocess
from   distutils.errors import DistutilsSetupError
import cffi


# NOTES, TO DO:
# - by starting the module name with 'stellapi.' similar to what we do for libstella_ it gets into the proper location
# - we use special $ORIGIN run time library tag so we can run without LD_LIBRARY_PATH;
#   a different solution using static libs fails when connecting to other STELLA systems
# - we do have a bootstrap issue wrt to the generation of _libstella_wrappers.cc.body which requires a functioning stellapi,
#   which in turn requires properly compiled and linked STELLA libs; for now we try to generate that during setup, but
#   if that fails we fall back onto a (hopefully) pre-generated version of that file (outside of setup)
# - possibly strip the resulting library files to make them smaller or use appropriate compilation flags

# Shared library woes:
# - shared libraries that are linked to need to be findable at build time as well as run time without requiring the
#   setup of a special path such as LD_LIBRARY_PATH or similar prior to running python
# - this affects STELLA libraries such as libstella.so and libgc.so as well as extension modules such as libstella_.so
# - the runtime linking issue could be solved by using the $ORIGIN idiom for ELF executables (at least for now, we might
#   still discover issues on Windows)
# - at build time (e.g., with setup and pip), libraries are being compiled into temporary, architecture-specific directories
#   that cannot portably be determined, and thus are not specifiable in the `library_dirs' spec below, for example,
#   .../build/lib.linux-x86_64-3.8/stellapi/
# - for STELLA libraries, we can solve the build-time issue by pointing to a static STELLA lib directory such as native/cpp/lib
# - for extension libraries that link to other extension libs (e.g., libstella_wrappers_.so as built by this script), we have
#   a more difficult problem, since we don't know where libstella_.so gets written during build time)
# - one way to work around that is to build the requisite library libstella_.so in a static location such as the stellapi module dir
#   (which is what we did previously with the call at the very end), that way we can point to it similar to other STELLA libs
# - unfortunately, since Py3 we have to deal with ABI tag qualifiers such as .cpython-38-x86_64-linux-gnu.so or .abi3.so; these tags
#   can be looked up via sysconfig.get_config_var('SOABI'), but due to an additional wrinkle, it looks like that again we cannot
#   rely on which final tag the extension libraries will have
# - wrinkle: setuptools/command/build_ext.py:get_ext_filename overrides the suffix the regular build_ext.py:get_ext_filename produces
#   with .abi3 when it deems that to be appropriate (that advised functionality took us a long time to track down); abi3 is the tag
#   for the stable application binary interface (see https://docs.python.org/3/c-api/stable.html)
# - this means the libstella_.so library built in the static module directory might have a different tag than the one in the install
#   location, meaning that again we will fail to link properly at run time
# - we can force the use of the qualifier defined via SOABI if we set py_limited_api = False, in which case we do get the SOABI and not
#   the more restricted stable ABI tag
# - but: the BEST SOLUTION seem so be to avoid having libstella_wrappers_ to be linked against libstella_ in the first place and instead
#   link it to the underlying STELLA libraries directly, thus avoiding the dependency between extension libraries all together;
#   the reason for this dependency came from initial attempts with static linking to avoid the whole shared library mess
# - this also removes the requirement for building libstella_.so in the static module location
# - final wrinkle: we'd like to have consistent ABI tags for all our STELLA extension libraries, call wrappers, dynamic call wrappers,...
#   it looks like setting 'py_limited_api = False' will force setuptools to use the SOABI extension, while setting the same to True will
#   not force cffi to use the 'abi3' extension (this is messy and potentially a bug); for this reason, we now set this flag to False
#   to give us a consistent SOABI extension to work with (Py2 just gives us a warning about this unsupported setting)
# - Lessons learned
#   - this is very hairy and a real mess and good info on how to handle these library dependencies best seems hard to come by
#   - there is various hairy interacting "advice" going on, setuptools modifies distutils and cffi modifies setuptools
#   - all this and pip is hard to debug since we can't just use pdb; instead we had to resort to print statements plastered
#     all over copies of distutils and setuptools in our test environment


module_dir  = os.path.realpath(os.path.dirname(__file__))
stella_home = os.path.realpath(os.path.join(module_dir, os.pardir, os.pardir))
stella_cpp_dir = os.path.join(stella_home, 'native', 'cpp')
stella_lib_dir = os.path.join(stella_cpp_dir, 'lib')
gc_include_dir = os.path.join(stella_cpp_dir, 'stella', 'cpp-lib', 'gc', 'include')

libstella_wrappers_name = '_libstella_wrappers'
libstella_wrappers_module_name = 'stellapi.' + libstella_wrappers_name
libstella_wrappers_file = os.path.join(stella_home, 'python', 'stellapi', libstella_wrappers_name + '.cc.body')

#abi_qualifier = sysconfig.get_config_var('SOABI') and '.' + sysconfig.get_config_var('SOABI') or ''
#abi_qualifier = sysconfig.get_config_var('SOABI') and '.abi3' or ''

# if possible we want to regenerate the wrappers file here which requires a running version of spi;
# but not all is lost if this fails as long as we distributed an appropriate pre-generated file;
# disabled for now, since this should be pretty stable and causes extra fragility:
# try:
#     sys.path.append(os.path.join(stella_home, 'python'))
#     import stellapi as spi
#     builder, code = spi.generateAllStellaFuncallWrappers(file=libstella_wrappers_file)
# except:
#     pass

if not os.path.exists(libstella_wrappers_file):
    raise DistutilsSetupError('Failed to find or generate STELLA call wrappers file: ' + libstella_wrappers_file)

with open(os.path.join(stella_home, 'python', 'stellapi', libstella_wrappers_name + '.cc.body'), 'r') as inp:
    libstella_wrappers = inp.read()

ffibuilder = cffi.FFI()

ffibuilder.set_source(libstella_wrappers_module_name,
                      source=libstella_wrappers,
                      source_extension='.cc',
                      language='c++',
                      include_dirs=[stella_cpp_dir, gc_include_dir],
                      # old scheme: we link against libstella_ which might require an appropriate ABI qualifier tag
                      # plus a known library location during build time (see deliberations above); this requires
                      # module names to end in `_' instead of beginning with one, but we now abandoned that:
                      #library_dirs=[module_dir],
                      #libraries = ['stella_' + abi_qualifier],
                      # new scheme: we link the wrapper lib to STELLA libs directly to avoid the wretched dependency:
                      library_dirs=[stella_lib_dir],
                      libraries = ['stella', 'gc'],
                      # special ELF platform value that refers to the install dir of the library, this also means
                      # we have to later load it from that location and not some other dir as we did previously:
                      runtime_library_dirs=['$ORIGIN', '$ORIGIN/.libs'],
                      # force a consistent SOABI extension in Py3:
                      py_limited_api = False,
)

# since we are not going through the normal build machinery, we have to explicitly define the signatures we need:
for line in libstella_wrappers.splitlines():
    if line.startswith('extern "C"'):
        ffibuilder.cdef(line.replace('extern "C" ', '').replace('{', ';'))

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
else:
    # in the new scheme, we don't have to build libstella_ in the module directory anymore:
    #subprocess.call(['python', os.path.join('stellapi', 'build_libstella.py')], shell=False, cwd=os.path.join(stella_home, 'python'))
    pass
