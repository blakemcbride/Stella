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

"""
Core low-level library functionality to bootstrap the API.
"""

from __future__ import print_function, division, absolute_import

import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str
    long = int

import os
import os.path
import tempfile
from shutil import copyfile
import imp

import stellapi.common as com
from   stellapi.common import FFI as _ffi
from   stellapi.utils import to_bytes, ffi_to_string, ApiException
from   stellapi.namespaces import boot, stella


### Bootstrap some basic functionality:

_reloadCounter = 0

def getSharedLibSuffix():
    """Return the shared library file extension used on this platform."""
    import sysconfig as cfg
    return cfg.get_config_var('SHLIB_SUFFIX') or cfg.get_config_var('SO')

def getExtensionLibSuffix():
    """Return the Python extension library file extension used on this platform,
    which might be qualified by the particular ABI version used.
    """
    import sysconfig as cfg
    return cfg.get_config_var('EXT_SUFFIX') or cfg.get_config_var('SO')

def getAbiQualifier():
    """Return ABI (application binary interface) qualifier if any."""
    # See also: https://www.python.org/dev/peps/pep-3149/
    #           https://docs.python.org/3/c-api/stable.html
    import sysconfig as cfg
    # See build_libstella_wrappers.py on how we are trying to force a consistent ABI tag
    # for Py3, however, it looks like this will run us into issues again at some point:
    #return cfg.get_config_var('SOABI') and '.abi3' or ''
    return cfg.get_config_var('SOABI') and '.' + cfg.get_config_var('SOABI') or ''

def loadLibrary(spec, name=None, kind='module', reload=False):
    """Load an extension module/library from `spec' which either has to be a fully
    qualified module name, a pathname to a module with full name `name', or the
    name of a dynamic library visible in the current dynamic load library path.
    `kind' can be `module' or `dynlib' and determines how to load the library.
    Stores the loaded library under `name' (defaults to `spec') in `com.LOADED_STELLA_LIBS'.
    If `reload' and the extension is a module, try to reload it.
    """
    global _reloadCounter
    name = name or str(spec)
    if kind == 'module':
        if os.path.exists(spec):
            try:
                if reload:
                    # by ensuring we load from a new file, we effectively reload the library and get new stuff
                    # (in addition to the temp file we use a counter to make sure we don't get the same file twice):
                    _reloadCounter += 1
                    # TO DO: we could try to allocate the temp file in the same directory as `spec' to
                    # avoid dynamic load library path issues, but we might not be allowed to write there:
                    tmplib = tempfile.mkstemp(suffix='_%d_%s' % (_reloadCounter, os.path.basename(spec)))[1]
                    copyfile(spec, tmplib)
                    spec = tmplib
                newlib = [name, imp.load_dynamic(name, spec)]
            finally:
                if reload:
                    os.remove(tmplib)
        else:
            import importlib
            newlib = [name, importlib.import_module(spec)]
            if reload:
                imp.reload(newlib[1])
    elif kind == 'dynlib':
        newlib = [name, _ffi.dlopen(spec)]
    else:
        raise ApiException('Unknown library type: ' + str(kind))
    com.LOADED_STELLA_LIBS = [newlib] + com.LOADED_STELLA_LIBS
    return newlib

def findLibrary(name):
    for tuple in com.LOADED_STELLA_LIBS:
        if name == tuple[0]:
            return tuple
    return None

def lookupLibraryFunction(name):
    """Try to lookup a function with `name' defined in one of the loaded STELLA libraries.
    Return None if no such function can be found in any of the currently loaded libraries.
    """
    for libname, lib in com.LOADED_STELLA_LIBS:
        if hasattr(lib, 'lib'):
            lib = getattr(lib, 'lib')
        if hasattr(lib, name):
            return getattr(lib, name)
    return None

loadLibrary('stellapi._libstella', name='libstella')
_stellalib = findLibrary('libstella')[1].lib
try:
    loadLibrary('stellapi._libstella_wrappers', name='libstella_wrappers')
except:
    pass


stella.cdef.NULL = _ffi.NULL

# define early needed functions in boot namespace - these now mirror what is specified
# in stellapi/libstella_builder.py (which see):
boot.startup = _stellalib.stella_startup
boot.startupStellaSystem = _stellalib.stella_startupStellaSystem
boot.lookupFunctionCodeByName = _stellalib.stella_lookupFunctionCodeByName
boot.lookupCCallableWrapperCodeByName = _stellalib.stella_lookupCCallableWrapperCodeByName
boot.lookupFunctionCppSignatureByName = _stellalib.stella_lookupFunctionCppSignatureByName
boot.lookupFunctionCSignatureByName = _stellalib.stella_lookupFunctionCSignatureByName
boot.lookupMethodCodeByName = _stellalib.stella_lookupMethodCodeByName
boot.lookupMethodCppSignatureByName = _stellalib.stella_lookupMethodCppSignatureByName
boot.lookupMethodCSignatureByName = _stellalib.stella_lookupMethodCSignatureByName
boot.lookupStorageSlotCppSignatureByName = _stellalib.stella_lookupStorageSlotCppSignatureByName
boot.lookupStorageSlotCSignatureByName = _stellalib.stella_lookupStorageSlotCSignatureByName
boot.lookupClassCppTypeByName = _stellalib.stella_lookupClassCppTypeByName
boot.lookupGlobalVariableCppSignatureByName = _stellalib.stella_lookupGlobalVariableCppSignatureByName
boot.lookupGlobalVariableCSignatureByName = _stellalib.stella_lookupGlobalVariableCSignatureByName
boot.gcProtectObject = _stellalib.stella_gcProtectObject
boot.gcReleaseObject = _stellalib.stella_gcReleaseObject
boot.primaryClass = _stellalib.stella_objectPrimaryClass
boot.stringCopy = _stellalib.stella_stringCopy
boot.symbolAbsoluteName = _stellalib.stella_generalizedSymbolAbsoluteName

# GC control (note: with GC_DEBUG set these need to be replaced with their debug variants):
boot.gcRegisterFinalizer = _stellalib.GC_register_finalizer
# this is the one needed with C++ (see gc_cpp.h):
boot.gcRegisterFinalizerIgnoreSelf = _stellalib.GC_register_finalizer_ignore_self
boot.gcRegisterFinalizerNoOrder = _stellalib.GC_register_finalizer_no_order
boot.gcRegisterFinalizerUnreachable = _stellalib.GC_register_finalizer_unreachable
boot.gcDisable = _stellalib.GC_disable
boot.gcEnable  = _stellalib.GC_enable
boot.gcCollect = _stellalib.GC_gcollect


# Initialize STELLA:
boot.startup(com.VERBOSE_STARTUP)
boot.startupStellaSystem()

# Now we can dynamically load in various functionality we need, but these functions
# cannot raise exceptions or return objects that might be GC'ed on the STELLA side:
boot.readSExpressionFromString = _ffi.cast("void* (*) (const char* string)", boot.lookupFunctionCodeByName(b'stella/read-s-expression-from-string'))
boot.typeToClass = _ffi.cast("void* (*) (void* type)", boot.lookupFunctionCodeByName(b'stella/type-to-class'))
boot.definedTypeP = _ffi.cast("bool (*) (void* type)", boot.lookupFunctionCodeByName(b'stella/defined-type?'))
boot.canonicalType = _ffi.cast("void* (*) (void* type)", boot.lookupFunctionCodeByName(b'stella/canonical-type'))
boot.classSurrogate = _ffi.cast("void* (*) (void* class)", boot.lookupFunctionCodeByName(b'stella/class-surrogate'))
boot.lookupSlot = _ffi.cast("void* (*) (void* class, void* slotName)", boot.lookupFunctionCodeByName(b'stella/lookup-slot'))
boot.getGenericSlotAccessor = _ffi.cast("void* (*) (void* slot, void* class, bool warn)", boot.lookupFunctionCodeByName(b'stella/get-generic-slot-accessor'))
boot.getGlobalVariableNativeObject = _ffi.cast("void* (*) (void* variable)", boot.lookupFunctionCodeByName(b'stella/get-global-variable-native-object'))
boot.getGlobalExceptionHandler = _ffi.cast("void* (*) ()", boot.lookupFunctionCodeByName(b'stella/get-global-exception-handler'))
boot.setGlobalExceptionHandler = _ffi.cast("void (*) (void*)", boot.lookupFunctionCodeByName(b'stella/set-global-exception-handler'))
boot.coerceToString = _ffi.cast("const char* (*) (void*)", boot.lookupFunctionCodeByName(b'stella/coerce-to-string'))
boot.eqlP = _ffi.cast("bool (*) (void* x, void* y)", boot.lookupFunctionCodeByName(b'stella/eql?'))
boot.definedListP = _ffi.cast("bool (*) (void* x)", boot.lookupFunctionCodeByName(b'stella/defined-list?'))

boot.wrapLongInteger = _ffi.cast("void* (*) (long long int)", boot.lookupFunctionCodeByName(b'stella/wrap-long-integer'))
boot.unwrapInteger = _ffi.cast("int (*) (void*)", boot.lookupFunctionCodeByName(b'stella/unwrap-integer'))
boot.unwrapLongInteger = _ffi.cast("long long int (*) (void*)", boot.lookupFunctionCodeByName(b'stella/unwrap-long-integer'))
boot.unwrapFloat = _ffi.cast("double (*) (void*)", boot.lookupFunctionCodeByName(b'stella/unwrap-float'))
boot.unwrapBoolean = _ffi.cast("bool (*) (void*)", boot.lookupFunctionCodeByName(b'stella/unwrap-boolean'))
boot.unwrapString = _ffi.cast("const char* (*) (void*)", boot.lookupFunctionCodeByName(b'stella/unwrap-string'))
boot.unwrapMutableString = _ffi.cast("char* (*) (void*)", boot.lookupFunctionCodeByName(b'stella/unwrap-mutable-string'))
boot.unwrapCharacter = _ffi.cast("char (*) (void*)", boot.lookupFunctionCodeByName(b'stella/unwrap-character'))

"""
ffi_to_string(boot.lookupFunctionCppSignatureByName(b'stella/read-character')).split('\t')
stella_Object = boot.typeToClass(boot.readSExpressionFromString(b'stella/@object'))
"""
