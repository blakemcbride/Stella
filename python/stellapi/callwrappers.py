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
Generating C++ function call wrappers to call STELLA code.
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
if PY3:
    from io import StringIO
else:
    from StringIO import StringIO
import re
import cffi

import stellapi.common as com
from   stellapi.common import FFI as _ffi
from   stellapi.utils import to_bytes, ffi_to_string, ApiException
from   stellapi.namespaces import boot, stella, getStellaModuleCDefNamespace
import stellapi.bootstrap as libs
import stellapi.signatures as sigs
from   stellapi.filelock import FileLock


### Creating STELLA code funcall wrappers

# The primary purpose of these is to provide proper catching of C++ exceptions and
# handling of multiple return values.  This allows us to create similar functionality
# as the wrappers created by the STELLA :c-callable? annotation but be more frugal
# and dynamic and not require constant pollution and retranslation of STELLA code.

_cIdentRegex = re.compile('^[_a-zA-Z0-9]+$')

def encodeCTypeForCallWrapperName(typ):
    ntype = typ
    ntype = ntype.replace('*', 'P') # 'P'ointer
    ntype = ntype.replace('&', 'R') # 'R'eference
    ntype = ntype.replace(' ', '')  # e.g., for long long int
    if _cIdentRegex.match(ntype) is None:
        raise ApiException('Cannot encode type for wrapper name: ' + typ)
    return ntype
    
def stellaFunCSigToCallWrapperName(csig):
    # Ex: callStellaFun_RcharP_IcharP_Iint_RcharP_RvoidP
    name = StringIO()
    name.write('callStellaFun_R')
    name.write(encodeCTypeForCallWrapperName(sigs.stellaSigNativeCppReturnType(csig)))
    for i in range(sigs.stellaSigArity(csig)):
        pname = sigs.stellaSigParaNativeName(csig, i)
        ptype = sigs.stellaSigParaNativeCppType(csig, i)
        pkind = 'I'     # 'I'nput
        if sigs.stellaSigIsReturnPara(csig, i):
            ptype = ptype[0:-1]
            pkind = 'R' # 'R'eturn
        name.write('_')
        name.write(pkind)
        name.write(encodeCTypeForCallWrapperName(ptype))
    return name.getvalue()

def stellaMethCSigToCallWrapperName(csig):
    # We treat methods identical to functions and only change the prefix.
    funWrapperName = stellaFunCSigToCallWrapperName(csig)
    return funWrapperName.replace('callStellaFun_', 'callStellaMeth_')

def stellaFunCSigToCallWrapperParaNames(csig, toCpp=False):
    params = ['code']
    argi = 1
    reti = 2
    for i in range(sigs.stellaSigArity(csig)):
        pname = sigs.stellaSigParaNativeName(csig, i)
        ptype = sigs.stellaSigParaNativeType(csig, i)
        cpptype = sigs.stellaSigParaNativeCppType(csig, i)
        if pname.startswith('_Return') and ptype.endswith('&'):
            pname = 'ret' + str(reti)
            if toCpp and cpptype.startswith('bool'):
                # cast C-style int* boolean return arguments to bool*:
                pname = '(' + sigs.pointerizeReturnParameterType(cpptype) + ')' + pname
            params.append(pname)
            reti += 1
        else:
            params.append('arg' + str(argi))
            argi += 1
    return params

def stellaMethCSigToCallWrapperParaNames(csig, toCpp=False):
    # Identical to function case.
    return stellaFunCSigToCallWrapperParaNames(csig, toCpp)

def stellaFunCSigToCallWrapperParaTypes(csig, toCpp=False):
    types = ['void*']
    for i in range(sigs.stellaSigArity(csig)):
        pname = sigs.stellaSigParaNativeName(csig, i)
        # for C++ map C-style `int' types that correspond to booleans to `bool' instead:
        ptype = toCpp and sigs.stellaSigParaNativeCppType(csig, i) or sigs.stellaSigParaNativeType(csig, i)
        if pname.startswith('_Return') and ptype.endswith('&'):
            types.append(ptype[0:-1] + '*')
        else:
            types.append(ptype)
    return types

def stellaMethCSigToCallWrapperParaTypes(csig, toCpp=False):
    # Identical to function case.
    return stellaFunCSigToCallWrapperParaTypes(csig, toCpp)

def stellaFunCSigToCallWrapperSig(csig):
    # Ex: char* callStellaFun_RcharP_IcharP_Iint_RcharP_RvoidP(void* code, char* arg1, int arg2, char** ret2, void** ret3)
    sig = StringIO()
    sig.write(sigs.stellaSigNativeReturnType(csig))
    sig.write(' ')
    sig.write(stellaFunCSigToCallWrapperName(csig))
    sig.write('(')
    for ptype, pname in zip(stellaFunCSigToCallWrapperParaTypes(csig), stellaFunCSigToCallWrapperParaNames(csig)):
        if pname != 'code':
            sig.write(', ')
        sig.write(ptype)
        sig.write(' ')
        sig.write(pname)
    sig.write(')')
    return sig.getvalue()

def stellaMethCSigToCallWrapperSig(csig):
    funsig = stellaFunCSigToCallWrapperSig(csig)
    return funsig.replace(' callStellaFun_', ' callStellaMeth_')

def stellaFunCSigToCallWrapperFuncall(csig):
    # Ex: return ((char* (*) (char*, int, char**, void**))code)(arg1, arg2, ret2, ret3);
    rtype = sigs.stellaSigNativeCppReturnType(csig)
    fcall = StringIO()
    if rtype != 'void':
        fcall.write('return ')
    fcall.write('((')
    fcall.write(rtype)
    fcall.write(' (*) (')
    fcall.write(', '.join(stellaFunCSigToCallWrapperParaTypes(csig, toCpp=True)[1:]))
    fcall.write('))code)(')
    fcall.write(', '.join(stellaFunCSigToCallWrapperParaNames(csig, toCpp=True)[1:]))
    fcall.write(');')
    return fcall.getvalue()

def stellaMethCSigIsOverloadedFunction(csig):
    # Return true if the STELLA method with `csig' is implemented via an overloaded function.
    # The more reliable test would be to check the type of the code wrapper, but we don't
    # have access to the qualified name here, so we key in on the first argument type.
    ptype = sigs.stellaSigParaNativeType(csig, 0)
    # this is too simplistic but will do for now:
    return ptype != 'void*'

def stellaMethCSigToCallWrapperFuncall(csig):
    # Ex: return (((stella::Object*)arg1)->*(void* (stella::Object::*)())(((stella::MethodCodeWrapper*)code)->wrapperValue))();
    # (the C++ syntax of calling method pointers is utterly hair raising)
    if stellaMethCSigIsOverloadedFunction(csig):
        # we have a FunctionCodeWrapper which needs regular funcall syntax:
        fcall = stellaFunCSigToCallWrapperFuncall(csig)
        fcall = fcall.replace('code', '(((stella::FunctionCodeWrapper*)code)->wrapperValue)')
        return fcall
    rtype = sigs.stellaSigNativeCppReturnType(csig)
    fcall = StringIO()
    if rtype != 'void':
        fcall.write('return ')
    fcall.write('(((stella::Object*)arg1)->*(')
    fcall.write(rtype)
    fcall.write(' (stella::Object::*)(')
    fcall.write(', '.join(stellaMethCSigToCallWrapperParaTypes(csig, toCpp=True)[2:]))
    fcall.write('))(((stella::MethodCodeWrapper*)code)->wrapperValue))(')
    fcall.write(', '.join(stellaMethCSigToCallWrapperParaNames(csig, toCpp=True)[2:]))
    fcall.write(');')
    return fcall.getvalue()

_typeToNullValue = {
    'int': 'stella::NULL_INTEGER',
    'bool': 'false',
    'double': 'stella::NULL_FLOAT',
    'char': 'stella::NULL_CHARACTER',
    'long long int': 'stella::NULL_LONG_INTEGER',
    }

def stellaNativeTypeToNullValue(rtype):
    return _typeToNullValue.get(rtype, 'NULL')

def stellaFunCSigToCallWrapperCode(csig):
    """Given the C-signature 'csig' of some STELLA function, create the C++ code for
    the wrapper function that will be used to call functions with this exact signature.
    Functions with the same signature can be called with the same wrapper function
    which means we will need much fewer wrappers than we have functions to call."""
    rtype = sigs.stellaSigNativeCppReturnType(csig)
    code = StringIO()
    code.write('extern "C" ')
    code.write(stellaFunCSigToCallWrapperSig(csig))
    code.write(' {\n')
    code.write('  try {\n')
    code.write('    ')
    code.write(stellaFunCSigToCallWrapperFuncall(csig))
    code.write('\n')
    code.write('  }\n')
    code.write('  catch (std::exception& e) {\n')
    code.write('    stella::callGlobalExceptionHandler(&e);\n')
    if rtype != 'void':
        code.write('    return ')
        code.write(stellaNativeTypeToNullValue(rtype))
        code.write(';\n')
    code.write('  }\n')
    code.write('}\n')
    return code.getvalue()

def stellaMethCSigToCallWrapperCode(csig):
    """Given the C-signature 'csig' of some STELLA method, create the C++ code for
    the wrapper function that will be used to call methods with this exact signature.
    Methods with the same signature can be called with the same wrapper function
    which means we will need much fewer wrappers than we have methods to call."""
    rtype = sigs.stellaSigNativeCppReturnType(csig)
    code = StringIO()
    code.write('extern "C" ')
    code.write(stellaMethCSigToCallWrapperSig(csig))
    code.write(' {\n')
    code.write('  try {\n')
    code.write('    ')
    code.write(stellaMethCSigToCallWrapperFuncall(csig))
    code.write('\n')
    code.write('  }\n')
    code.write('  catch (std::exception& e) {\n')
    code.write('    stella::callGlobalExceptionHandler(&e);\n')
    if rtype != 'void':
        code.write('    return ')
        code.write(stellaNativeTypeToNullValue(rtype))
        code.write(';\n')
    code.write('  }\n')
    code.write('}\n')
    return code.getvalue()

"""
>>> print(stellaFunCSigToCallWrapperCode(sigs.getStellaFunctionCSignature('stella/parse-stella-name')))
extern "C" char* callStellaFun_RcharP_IcharP_Ibool_RcharP_RvoidP(void* code, char* arg1, int arg2, char** ret2, void** ret3) {
  try {
    return ((char* (*) (char*, bool, char**, void**))code)(arg1, arg2, ret2, ret3);
  }
  catch (std::exception& e) {
    stella::callGlobalExceptionHandler(&e);
    return NULL;
  }
}
"""

_stellaFuncallRegistry = set()

def registerStellaFuncallWrapper(qualName):
    """Register that we need a call wrapper for the STELLA function 'qualName'."""
    _stellaFuncallRegistry.add(qualName)

def hasRegisteredStellaFuncallWrapper(qualName):
    """Return True if a call wrapper for the STELLA function 'qualName' has been registered."""
    return qualName in _stellaFuncallRegistry

def lookupRegisteredStellaFunctionNameFromCode(fncode):
    """Given the C-code of a registered STELLA function, return its qualified name."""
    for sfun in _stellaFuncallRegistry:
        if isStellaMethodName(sfun):
            if sigs.getStellaMethodCode(sfun) == fncode:
                return sfun
        elif sigs.getStellaFunctionCode(sfun) == fncode:
            return sfun
    return None

def isStellaMethodName(qualName):
    """Return True if 'qualName' names an existing STELLA method."""
    # Note that this will say true for native methods where we don't have code.
    return qualName.find('.') > 0 and boot.lookupMethodCppSignatureByName(to_bytes(qualName)) != _ffi.NULL

def getStellaFuncallWrapperFileInfo():
    wrapperDir = os.path.dirname(com.CALL_WRAPPER_FILE)
    if wrapperDir == '':
        # compute wrapper file default directory in user site-package location:
        import site
        wrapperDir = os.path.join(site.getusersitepackages(), com.stellapiModule.__name__)
        if not os.path.exists(wrapperDir):
            # this should give us a reproducable per-user lockfile based on user's site-package location:
            lockfile = os.path.join(tempfile.gettempdir(), 'stellapi-%d.lock' % (abs(hash(wrapperDir)) % 2**32))
            with FileLock(lockfile, mode='w'):
                os.path.exists(wrapperDir) or os.makedirs(wrapperDir)
        com.CALL_WRAPPER_FILE = os.path.join(wrapperDir, com.CALL_WRAPPER_FILE)
    wrapperSource = os.path.realpath(com.CALL_WRAPPER_FILE)
    wrapperDir = os.path.dirname(wrapperSource)
    wrapperName, ext = os.path.basename(wrapperSource).split('.')
    wrapperFullName = com.stellapiModule.__name__ + '.' + wrapperName
    wrapperLib = os.path.join(wrapperDir, wrapperName + libs.getExtensionLibSuffix())
    wrapperLock = os.path.join(wrapperDir, wrapperName + '.lock')
    if not (wrapperName.startswith('_') or wrapperName.endswith('_')):
        # the wrapper name becomes a module name, so make sure it is internal and doesn't conflict:
        raise ApiException('Call wrapper file name needs to start or end with an underscore: ' + wrapperSource)
    return {'source': wrapperSource,
            'directory': wrapperDir,
            'name': wrapperName,
            'fullname': wrapperFullName,
            'extension': '.' + ext,
            'library': wrapperLib,
            'lock': wrapperLock,
            }

_stellaSectionHeader  = "/**********  STELLA-specific call wrapper section  **********/"
_stellaSectionTrailer = "/**********  end STELLA-specific call wrapper section  **********/"

def readStellaFuncallWrappers(wrappersFile):
    """Read a call `wrappersFile' generated by `compileStellaFuncallWrappers' and return
    a dictionary of wrapper C-sigs pointing to their corresponding definitions.
    """
    info = None
    defn = None
    with open(wrappersFile, 'r') as inp:
        for line in inp:
            if info is None:
                if line[0] == '/' and line.startswith(_stellaSectionHeader):
                    info = {}
            elif line[0] == '/' and line.startswith(_stellaSectionTrailer):
                break
            elif line.startswith('extern "C" '):
                defn = StringIO()
                defn.write(line)
                sig = line[11:].replace(' {', '').strip()
            elif line.startswith('}'):
                defn.write(line)
                info[sig] = defn.getvalue()
                defn = None
            elif defn is not None:
                defn.write(line)
    return info

def generateStellaFuncallWrapperDefn(qualName):
    isMethod = isStellaMethodName(qualName)
    if isMethod:
        csig = sigs.getStellaMethodCSignature(qualName)
        wsig = stellaMethCSigToCallWrapperSig(csig)
    else:
        csig = sigs.getStellaFunctionCSignature(qualName)
        wsig = stellaFunCSigToCallWrapperSig(csig)
    if isMethod:
        wdefn = stellaMethCSigToCallWrapperCode(csig)
    else:
        wdefn = stellaFunCSigToCallWrapperCode(csig)
    return wsig, wdefn

def hasStaticFuncallWrapper(qualName):
    """Return True if the funcall wrapper for `qualName' is provided by one of the
    static / pregenerated call wrapper libraries (such as _libstella_wrappers.so).
    """
    wrapperInfo = getStellaFuncallWrapperFileInfo()
    dynamicLibName = wrapperInfo['fullname']
    wrapperName = getStellaFuncallWrapperName(qualName)
    loadedLibs = com.LOADED_STELLA_LIBS
    staticLibs = [slib for slib in com.LOADED_STELLA_LIBS if slib[0] != dynamicLibName]
    try:
        com.LOADED_STELLA_LIBS = staticLibs
        return libs.lookupLibraryFunction(wrapperName) is not None
    finally:
        com.LOADED_STELLA_LIBS = loadedLibs

def generateStellaFuncallWrappers(builder=None, callables=None, static=False):
    """Generate code for a dynamic call wrappers file for all currently registered functions and methods
    whose call wrappers are not already provided by some other loaded libraries (such as per-system libs).
    Preserve any wrappers from an already existing wrappers file, since those might support a different
    process or API.  This means the dynamic call wrappers file will slowly grow like a database.
    If `callables' is passed in, that list will be used instead of all registered functions.
    If `static', it is assumed a static (non-dynamic) per-system call wrappers is being generated.
    """
    ffibuilder = builder or cffi.FFI()
    stellaHome = os.path.realpath(com.STELLA_HOME)
    wrapperInfo = getStellaFuncallWrapperFileInfo()
    wrapperFile = wrapperInfo['source']
    code = StringIO()
    code.write(_stellaSectionHeader + "\n\n")
    code.write('#define STELLA_USE_GC\n')
    code.write('#include "stella/stella-system.hh"\n\n')
    beenThere = set()
    # preserve already existing wrappers since they might support a different API or process:
    if os.path.exists(wrapperFile) and not static:
        for wsig, defn in readStellaFuncallWrappers(wrapperFile).items():
            ffibuilder.cdef(wsig + ';')
            code.write(defn)
            code.write('\n')
            beenThere.add(wsig)
    for sfun in callables or _stellaFuncallRegistry:
        wsig, wdefn = generateStellaFuncallWrapperDefn(sfun)
        if wsig in beenThere:
            continue
        beenThere.add(wsig)
        if hasStaticFuncallWrapper(sfun) and not static:
            # sfun already has a wrapper provided by one of the static wrapper libs loaded:
            continue
        try:
            ffibuilder.cdef(wsig + ';')
        except:
            print('WARNING: failed to build call wrapper for %s: %s' % (sfun, wsig))
            continue
        code.write(wdefn)
        code.write('\n')
    code.write("\n" + _stellaSectionTrailer + "\n")
    return ffibuilder, code.getvalue()

def compileStellaFuncallWrappers(builder=None, module=None, code=None, run=True):
    """Generate and, if `run', compile a call wrappers file for all registered functions and methods.
    Preserve any wrappers from an already existing wrappers file, since those might support a different
    process or different API.  This means the call wrappers file will slowly grow like a database.
    Use `builder' and/or `code' if passed in, otherwise generate them from scratch.  If `run' is false,
    do not actually compile and install the result, just return the modified `builder' object.
    For more fine-grained control, use `generateStellaFuncallWrappers' and then pass in the code.
    """
    # TO DO: make build directory configurable in case we are generating wrapper libs for other systems
    stellaHome = os.path.realpath(com.STELLA_HOME)
    wrapperInfo = getStellaFuncallWrapperFileInfo()
    module = module or wrapperInfo['fullname']
    # ffibuilder.compile runs relative to tmpdir which defaults to the current directory;
    # here we determine the appropriate module parent directory depending on the number of dots (usually 1):
    buildDir = os.path.realpath(os.path.join(wrapperInfo['directory'], *[os.pardir] * module.count('.')))
    ffibuilder = builder
    if code is None:
        ffibuilder, code = generateStellaFuncallWrappers(builder=builder)
    ffibuilder.set_source(module,
                          code,
                          language='c++',
                          source_extension=wrapperInfo['extension'],
                          include_dirs=[os.path.join(stellaHome, 'native', 'cpp'),
                                        # standard source directory location of GC includes:
                                        os.path.join(stellaHome, 'native', 'cpp', 'stella', 'cpp-lib', 'gc', 'include'),
                                        os.path.join(com.stellapiHome, 'include'),
                                        # python install directory location of GC includes:
                                        os.path.join(com.stellapiHome, 'include', 'gc'),
                          ],
                          library_dirs=[com.stellapiHome, os.path.join(com.stellapiHome, '.libs')],
                          # we use the absolute path here, so we can run from other locations:
                          runtime_library_dirs=['$ORIGIN',
                                                os.path.realpath(com.stellapiHome),
                                                os.path.join(os.path.realpath(com.stellapiHome), '.libs')],
                          # this is the reason why we use a trailing _ for these internal libs,
                          # otherwise we'd have to use a -l: syntax which is less portable:
                          libraries = ['stella', 'gc'],
                          # force a consistent SOABI extension in Py3 - causes a warning in Py2:
                          py_limited_api = False,
    )
    if run:
        return ffibuilder.compile(tmpdir=buildDir, verbose=False)
    else:
        return ffibuilder

def collectStellaCallables(modules=['STELLA']):
    """Collect qualified names of callable function and methods whose home module is in one of `modules'.
    """
    # TO DO: clean up minor ugliness with forward ref to API functions:
    import stellapi as spi
    spi.defun('stella/all-functions')
    spi.defun('stella/all-methods')
    spi.defun('stella/native-method?')
    spi.defslot('stella/slot.slot-owner')
    callables = set()
    # exclude some classes that give us problems:
    excluded = [stella.pdef.lookupClassByQualifiedName(name) for name in [
        'STELLA/SECOND-CLASS-OBJECT', 'STELLA/ARGUMENT-LIST']]
    for module in modules:
        module = stella.pdef.getStellaModule(module, True)
        moduleName = module.moduleFullName
        for fn in stella.pdef.allFunctions(module, True):
            if stella.pdef.nativeMethodP(fn):
                qname = moduleName + '/' + fn.slotName.symbolName
                callables.add(qname)
        for meth in stella.pdef.allMethods(module, True):
            if stella.pdef.nativeMethodP(meth):
                owner = stella.pdef.typeToClass(meth.slotOwner)
                if owner not in excluded:
                    qname = moduleName + '/' + owner.name() + '.' + meth.slotName.symbolName
                    if not qname.startswith('/STELLA/SECOND-CLASS-OBJECT.'): # kludge
                        callables.add(qname)
    return callables
    
def generateAllStellaFuncallWrappers(builder=None, modules=['STELLA'], file=None):
    callables = collectStellaCallables(modules)
    builder, code = generateStellaFuncallWrappers(builder=builder, callables=callables, static=True)
    if file is not None:
        with open(file, 'w') as out:
            out.write(code)
    return builder, code

"""
# use this to generate the wrappers file necessary for STELLA install:
>>> import stellapi as spi
>>> res = spi.generateAllStellaFuncallWrappers(file='python/stellapi/_libstella_wrappers.cc.body')
"""

def compileAllStellaFuncallWrappers(builder=None, module=None, modules=['STELLA'], run=True):
    """Precompile and install wrappers for all wrappable STELLA functions.
    This needs to be run during package install time.  If `run' is False,
    do not compile and install and just return the modified builder.
    """
    builder, code = generateAllStellaFuncallWrappers(builder=builder, modules=modules)
    return compileStellaFuncallWrappers(builder=builder, module=module, code=code, run=run)

def lookupFuncallWrapper(wrapperName):
    return libs.lookupLibraryFunction(wrapperName)

def getStellaFuncallWrapperName(qualName):
    isMethod = isStellaMethodName(qualName)
    if isMethod:
        csig = sigs.getStellaMethodCSignature(qualName)
        wrapperName = stellaMethCSigToCallWrapperName(csig)
    else:
        csig = sigs.getStellaFunctionCSignature(qualName)
        wrapperName = stellaFunCSigToCallWrapperName(csig)
    return wrapperName

def lookupStellaFuncallWrapper(qualName):
    return lookupFuncallWrapper(getStellaFuncallWrapperName(qualName))

def getStellaFuncallWrapperNamespace(qualName, wrapperName):
    # For now we allocate all call wrappers in the STELLA CDef namespace, even
    # if they were created by wrapping functions outside of the STELLA module.
    # Creating separate namespace depending on the module of `qualName' that
    # triggered the generation of the wrapper would make things significantly
    # more complicated and introduce duplicate wrappers in different modules:
    return getStellaModuleCDefNamespace('/STELLA')

def activateStellaFuncallWrapper(qualName, code):
    """Activate the funcall wrapper for `qualName' by setting its definition to `code'
    in the funcall wrapper namespace (stella.cdef).  `code' might be an autoloader or
    later the actual C-code entry point replacing it.
    """
    wrapperName = getStellaFuncallWrapperName(qualName)
    wdefns = getStellaFuncallWrapperNamespace(qualName, wrapperName)
    setattr(wdefns, wrapperName, code)

def getStellaFuncallWrapper(qualName):
    #import pdb
    #pdb.set_trace()
    wrapper = lookupStellaFuncallWrapper(qualName)
    if wrapper is not None:
        # link the wrapper to the cdef namespace which will overwrite the autoloader that got us here;
        # we now do this one at a time, since pre-generated wrapper libraries might have lots of them:
        activateStellaFuncallWrapper(qualName, wrapper)
        return wrapper
    if not hasRegisteredStellaFuncallWrapper(qualName):
        raise ApiException('call wrapper for STELLA function ' + qualName + ' has not been registered')
    wrapperInfo = getStellaFuncallWrapperFileInfo()
    if libs.findLibrary(wrapperInfo['fullname']) is None:
        with FileLock(wrapperInfo['lock'], mode='r'):
            if os.path.exists(wrapperInfo['library']):
                #print('loading STELLA funcall wrappers...')
                libs.loadLibrary(wrapperInfo['library'], name=wrapperInfo['fullname'], reload=False)
    if lookupStellaFuncallWrapper(qualName) is None:
        # still no wrapper, dynamically (re)compile and load wrapper code objects for all registered functions:
        with FileLock(wrapperInfo['lock'], mode='w', wait=0.5):
            print('(re)loading STELLA funcall wrappers...')
            wrapperLibFile = compileStellaFuncallWrappers()
            libs.loadLibrary(wrapperLibFile, name=wrapperInfo['fullname'], reload=True)
    wrapper = lookupStellaFuncallWrapper(qualName)
    if wrapper is None:
        raise ApiException('failed to autoload call wrapper for STELLA function: ' + qualName)
    else:
        # "recursive call":
        activateStellaFuncallWrapper(qualName, wrapper)
        return wrapper

"""
# test wrapper file locking:
> seq -w 1 50 | parallel --will-cite --lb python-pli -c "'"import ploompi as pli"'"
"""

def stellaFuncallWrapperAutoLoader(fncode, *args):
    """Autoloader definition used as the initial implementation for STELLA funcall wrappers.
       Once the first autoloader is called, all wrappers for currently registered functions
       will be generated, compiled and loaded and will replace their respective autoload
       wrappers; thus, on the next call, the native wrapper methods will be called instead.
       This is incremental and will reload if necessary if new wrappers are needed for newly
       registered functions not addressed by previously generated wrappers."""
    # do a reverse lookup from a STELLA function code pointer to the qualified name of its host function:
    sfun = lookupRegisteredStellaFunctionNameFromCode(fncode)
    if sfun is None:
        raise ApiException('failed to lookup STELLA function name from code in autoloader')
    wrapperCode = getStellaFuncallWrapper(sfun)
    # now call the wrapper, but in the next call it will find the wrapper code object directly:
    return wrapperCode(fncode, *args)

"""
>>> _stellaFuncallRegistry = set()
>>> registerStellaFuncallWrapper('stella/parse-integer')
>>> registerStellaFuncallWrapper('stella/parse-stella-name')
>>> registerStellaFuncallWrapper('stella/get-stella-module')
>>> registerStellaFuncallWrapper('stella/read-slot-value')
>>> 
>>> compileStellaFuncallWrappers()
'/home/hans/Documents/deft/release/k-aggregator-1.6.10.5/native/cpp/lib/_stella_call_wrappers.so'
>>> sw = loadStellaFuncallWrappers(_)
>>> dir(sw.lib)
['callStellaFun_RcharP_IcharP_Iint_RcharP_RvoidP', 'callStellaFun_Rint_IcharP', 'callStellaFun_RvoidP_IcharP_Iint', 'callStellaFun_RvoidP_IvoidP_IvoidP']

# here are bits and pieces used by `defineStellaFunction' and friends:
>>> sfun = 'stella/parse-integer'
>>> sfun_csig = sigs.getStellaFunctionCSignature(sfun)
>>> sfun_call_wrapper_name = stellaFunCSigToCallWrapperName(sfun_csig)
>>> sfun_code = getStellaFunctionTypedCode(sfun)
>>> sfun_call_wrapper_name
'callStellaFun_Rint_IcharP'
>>> getattr(sw.lib, sfun_call_wrapper_name)(sfun_code, '54321')
54321
>>> stella.cdef.callStellaFun_Rint_IcharP = getattr(sw.lib, sfun_call_wrapper_name)
>>> stella.cdef.parseInteger = sfun_code
>>> stella.cdef.callStellaFun_Rint_IcharP(stella.cdef.parseInteger, '666')
666

# dynamic loading of the call wrapper for a STELLA function:
>>> registerStellaFuncallWrapper('stella/parse-integer')
>>> stella.cdef.parseInteger = getStellaFunctionTypedCode('stella/parse-integer')
>>> stella.cdef.callStellaFun_Rint_IcharP = stellaFuncallWrapperAutoLoader
>>> stella.cdef.callStellaFun_Rint_IcharP
<function stellaFuncallWrapperAutoLoader at 0x7f17d0c857d0>
>>> stella.cdef.callStellaFun_Rint_IcharP(stella.cdef.parseInteger, '666')
666
>>> stella.cdef.callStellaFun_Rint_IcharP
<built-in method callStellaFun_Rint_IcharP of CompiledLib object at 0x7f17d0ca5c58>
>>> stella.cdef.callStellaFun_Rint_IcharP(stella.cdef.parseInteger, '12345')
12345
"""
