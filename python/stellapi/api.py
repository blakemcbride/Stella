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
# Portions created by the Initial Developer are Copyright (C) 1996-2022      #
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
Python foreign function interface to connect to STELLA functions and objects.
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

import stellapi.common as com
from   stellapi.common import FFI as _ffi
from   stellapi.utils import to_bytes, ffi_to_string, ApiException
from   stellapi.namespaces import boot, stella
import stellapi.bootstrap as libs
import stellapi.signatures as sigs
import stellapi.callwrappers as cws
import stellapi.pywrappers as pws
import stellapi.types as types

# API exports from other packages:
from stellapi.common import FFI
from stellapi.namespaces import defineStellaModuleNamespace
from stellapi.bootstrap  import loadLibrary
from stellapi.gcollect import gcProtectObject, getPythonObjectStellaPointer, \
    unregisterPythonObjectStellaPointer, getPythonObjectFromStellaPointer, \
    getPythonObjectFromStellaPointerId
from stellapi.exceptions import StellaException
from stellapi.types import stellaObjectToPythonType, stellaToPythonObject, \
    stellaToPythonObjectOfType, pythonStringToStellaString, pythonToStellaObject, \
    pythonToStellaObjectOfType, pythonToStellaTree, stellafy, \
    ProxyClass, lookupStellaTypeProxyClass


### Top-level definition commands

# For top-level definition commands we return the (or a spec of) the defined Python object,
# a qualified name that can be used to access it, and the corresponding STELLA object (if it exists).

def defun(qualName, _gc='auto', _except=True, _wrapper='auto', _pyin=True, _pyout=True, _doc=None, _pre=None, **kwargs):
    """Top-level STELLA function definition command."""
    if cws.isStellaMethodName(qualName):
        raise ApiException('Trying to define a STELLA function that is actually a method: ' + qualName)
    pfun = pws.defineStellaFunction(qualName, gc=_gc, exceptions=_except, useWrapper=_wrapper, pyin=_pyin, pyout=_pyout, 
                                    doc=_doc, argSpecs=kwargs, preproc=_pre)
    sfun = com._bootstrapCompleted and stella.pdef.lookupFunctionByQualifiedName(qualName) or None
    return pfun, pws.getObjectFullname(pfun), sfun

def defmethod(qualName, _gc='auto', _except=True, _wrapper='auto', _pyin=True, _pyout=True, _doc=None, _pre=None, **kwargs):
    """Top-level STELLA method definition command."""
    if not cws.isStellaMethodName(qualName):
        raise ApiException('Trying to define a STELLA method that is actually a function: ' + qualName)
    homeProxyClass, slotspec = pws.defineStellaMethod(qualName, gc=_gc, exceptions=_except, useWrapper=_wrapper,
                                                      pyin=_pyin, pyout=_pyout, doc=_doc, argSpecs=kwargs, preproc=_pre)
    # for non-object methods we have a code object instead of a name:
    slotname = isinstance(slotspec, str) and slotspec or slotspec.__name__
    slot = com._bootstrapCompleted and stella.pdef.lookupSlotByQualifiedName(qualName) or None
    return (homeProxyClass, slotname), pws.getObjectFullname(homeProxyClass) + '.' + slotname, slot

def defslot(qualName):
    """Top-level STELLA storage slot definition command."""
    homeProxyClass, slotname = pws.defineStellaStorageSlot(qualName)
    slot = com._bootstrapCompleted and stella.pdef.lookupSlotByQualifiedName(qualName) or None
    return (homeProxyClass, slotname), pws.getObjectFullname(homeProxyClass) + '.' + slotname, slot

def defextslot(qualName, _type='STELLA/OBJECT'):
    """Defines a new dynamic slot on STELLA objects that inherit DYNAMIC-SLOT-MIXIN.
    If the class does not support dynamic slots, an error is raised.
    This is primarily useful to add slots to hold pointers to Python objects, e.g.,
    to stick a Python object into a STELLA module, PowerLoom proposition, etc.
    If `qualName' names an existing slot, this behaves just like `defslot'.
    """
    slot, klass = stella.pdef.lookupSlotAndClassByQualifiedName(qualName)
    if slot is None:
        className = klass.name()
        symName, modName, kind = stella.pdef.parseStellaName(qualName, True)
        if symName[len(className)] != '.':
            raise ApiException('Illegal slot name: ' + qualName)
        slotName = symName[len(className)+1:]
        defn = '(STELLA/DEFSLOT %s %s :type %s)' % (className, slotName, _type)
        with klass.homeModule() as mod:
            slot = stella.pdef.defineExternalSlotFromStringifiedSource(defn)
            if slot is None:
                raise ApiException('Illegal external slot definition: ' + qualName)
    # now that we know the slot is defined, simply run `defslot':
    return defslot(qualName)

def defclass(qualName):
    """Top-level STELLA class definition command."""
    stellaClass = stella.pdef.lookupClassByQualifiedName(qualName)
    if stellaClass is None:
        raise ApiException('No such STELLA class: ' + qualName)
    # IMPORTANT:  we pass in the class here to get a normalized absolute type path:
    proxyClass = types.getStellaTypeProxyClass(stellaClass)
    return proxyClass, pws.getObjectFullname(proxyClass), stellaClass

def defconstructor(qualName, _wrapper='auto', _pyin=True):
    """Top-level STELLA constructor definition command for the class named by `qualName'.
    If the constructor has required slot parameters, they can be given by slot name, or
    otherwise in the same order they are listed in their C++ equivalent.
    """
    klass = stella.pdef.lookupClassByQualifiedName(qualName)
    if klass is None:
        raise ApiException('No class with this name: ' + qualName)
    code = stella.pdef.getConstructor(klass, True)
    if code is None:
        raise ApiException('No constructor available for class: ' + qualName)
    # we basically create a method object for the constructor function here which is not auxiliary,
    # thus, it will be added to the current function lookup table and findable via `methodQualName':
    defn = stella.pdef.yieldConstructorDefinition(klass)
    method = stella.pdef.defineMethodFromParseTree(defn)
    method.functionCode = code
    methodQualName = ffi_to_string(boot.symbolAbsoluteName(method.slotName._stellaObject, 1))
    #wrapperCode = defun(methodQualName, _except=False, _wrapper=_wrapper, _pyin=_pyin, _pyout=False)
    wrapperCode = pws.defineStellaFunction(methodQualName, exceptions=False, useWrapper=_wrapper, pyin=_pyin, pyout=False)
    csig = sigs.getStellaFunctionCSignature(methodQualName)
    paraNames = sigs.stellaSigParameterNativeNames(csig)
    paraNamesWithInits = ', '.join([name + '=None' for name in paraNames]) + (paraNames and ', ' or '')
    paraNames = ', '.join(paraNames)
    initName = '_py__init__'

    # we call the constructor if no native STELLA object was provided, otherwise, we simply wrap the given object:
    initCode = """def %s(self, %s_stobj=None):
    self._stellaObject = _stobj or wrapperCode(%s)\n""" % (initName, paraNamesWithInits, paraNames)

    # tricky: closures don't work with string exec's, since the string gets compiled first before
    # globals/locals are considered, so we have to put the relevant link into the exec's globals:
    exec(initCode, {'wrapperCode': wrapperCode}, locals())
    # link to `klass's proxy's __init__ method - but we can only do this for STELLA classes:
    homeProxyClass = types.getStellaTypeProxyClass(klass) 
    if issubclass(homeProxyClass, types.ProxyClass):
        setattr(homeProxyClass, '__init__', locals()[initName])
        return (homeProxyClass, '__init__'), pws.getObjectFullname(homeProxyClass) + '(' + paraNamesWithInits + ')', method
    else:
        return wrapperCode, pws.getObjectFullname(wrapperCode), method

def defglobal(qualName):
    """Top-level STELLA global variable definition command."""
    pdefns, gvname = pws.defineStellaGlobalVariable(qualName)
    globalVar = com._bootstrapCompleted and stella.pdef.lookupGlobalVariableByQualifiedName(qualName) or None
    return (type(pdefns), gvname), pdefns.__name__ + '.' + gvname, globalVar

def defnamespace(moduleSpec, nsName=None):
    """Define the Python classes and module instances necessary for the Python namespace
    `nsName' to hold objects of STELLA module `moduleSpec'.  If `nsName' is None, it will
    be based on the C++ namespace used for module `moduleSpec'.  This creates Python modules
    `stellapi.ns', `stellapi.ns.pdef' and `stellapi.ns.cdef'. In addition, a separate class
    is generated for each generated Python module to host properties.
    """
    return defineStellaModuleNamespace(moduleSpec, nsName=nsName)

def loadSystem(systemName, libspec=None):
    """Load the STELLA system `systemName' by calling its STELLA startup function.
    If `libspec' is None, it is assumed that a relevant library has either already been
    loaded, or that a dynamic library 'lib<systemName>' can be used to load the system.
    Otherwise, `libspec' is loaded using `loadLibrary'.  For more fine-grained control
    of load options, `loadLibrary' should be called explicitly before this function.
    After the first call, subsequent calls to this function are no-ops.
    """
    if libspec is not None:
        kind = libspec.endswith(libs.getSharedLibSuffix()) and 'dynlib' or 'module'
        libs.loadLibrary(libspec, kind=kind)
    # exploit new STELLA scheme that allocates C-callable system startup functions in the STELLA module:
    startupFnName = ('STARTUP-' + systemName + '-SYSTEM').upper()
    startupFnSymbol = stella.pdef.internSymbolInModule(startupFnName, stella.pdef.oSTELLA_MODULEo, True)
    startupFnCppName = str(stella.pdef.cppTranslateName(startupFnSymbol))
    startupFnCName = 'stella_' + startupFnCppName
    if libs.lookupLibraryFunction(startupFnCName) is None:
        _ffi.cdef('void ' + startupFnCName + '();')
    if libs.lookupLibraryFunction(startupFnCName) is None:
        if libspec is None:
            libname = 'lib' + systemName + libs.getSharedLibSuffix()
            loadSystem(systemName, libspec=libname)
        else:
            raise ApiException('Cannot find the implementation of ' + startupFnCName + ' in loaded libraries')
    else:
        # call the startup function:
        libs.lookupLibraryFunction(startupFnCName)()

def loadFile(file):
    """Load a file of STELLA commands using STELLA's `load-file' command (which see).
    This is primarily intended to explicitly load STELLA system definition files.
    """
    stella.pdef.loadFile(file)

def translateSystem(system, lang='cpp', twoPass=False, force=False, recursive=False, devel=False,
                    rootSourceDir=None, rootNativeDir=None, rootBinDir=None):
    """Translate the STELLA system `system' using STELLA's `translate-system' command (which see).
    """
    lang = lang and ':language :%s' % lang or ''
    twoPass = twoPass and ':two-pass? TRUE' or ''
    force = force and ':force-translation? TRUE' or ''
    recursive = recursive and ':recursive? TRUE' or ''
    devel = devel and ':development-settings? TRUE' or ':production-settings? TRUE'
    rootSourceDir = rootSourceDir and ':root-source-directory "%s"' % rootSourceDir or ''
    rootNativeDir = rootNativeDir and ':root-native-directory "%s"' % rootNativeDir or ''
    rootBinDir = rootBinDir and ':root-binary-directory "%s"' % rootBinDir or ''
    command = """(translate-system "%s" %s %s %s %s %s %s %s %s)""" % (
                      system, lang, twoPass, force, recursive, devel,
                      rootSourceDir, rootNativeDir, rootBinDir)
    with stella.pdef.oSTELLA_MODULEo as mod:
        stella.pdef.evaluateString(command)

"""
>>> defun('stella/parse-integer')
(<function parseInteger at 0x7fa186634320>, 'stellapi.stella.pdef.parseInteger', <proxy.MethodSlot |F|PARSE-INTEGER>)

>>> stella.pdef.parseInteger('12345')
(re)loading STELLA funcall wrappers...
12345
"""


### High-level Python wrappers for various STELLA functions and objects

defun('stella/wrap-integer', _except=False, _pyin=False)
defun('stella/unwrap-integer', _except=False)
defun('stella/wrap-long-integer', _except=False, _pyin=False)
defun('stella/unwrap-long-integer', _except=False)
defun('stella/wrap-integer-value', _except=False, _pyin=False)
defun('stella/wrap-float', _except=False, _pyin=False)
defun('stella/unwrap-float', _except=False)
defun('stella/wrap-string', _except=False)
defun('stella/unwrap-string', _except=False)
defun('stella/wrap-character', _except=False, _pyin=PY3)
defun('stella/unwrap-character', _except=False)
defun('stella/wrap-boolean', _except=False, _pyin=False)
defun('stella/unwrap-boolean', _except=False)

defun('stella/wrap-mutable-string', _except=False)
defun('stella/unwrap-mutable-string', _except=False)
defun('stella/wrap-function-code', _except=False)
defun('stella/unwrap-function-code', _except=False)
defun('stella/wrap-method-code', _except=False)
defun('stella/unwrap-method-code', _except=False)

#defun('stella/coerce-to-string') # done manually
defun('stella/parse-integer')
defun('stella/parse-stella-name')
defun('stella/get-stella-module')
defun('stella/change-current-module')

defun('stella/lookup-symbol')
defun('stella/intern-symbol')
defun('stella/lookup-symbol-in-module')
defun('stella/intern-symbol-in-module')
defun('stella/lookup-transient-symbol')
defun('stella/intern-transient-symbol')
defun('stella/lookup-surrogate')
defun('stella/intern-surrogate')
defun('stella/lookup-keyword')
defun('stella/intern-keyword')
defun('stella/lookup-stella-name')
defun('stella/intern-stella-name')

defun('stella/lookup-function-by-qualified-name')
defun('stella/lookup-slot-by-qualified-name')
defun('stella/lookup-slot-and-class-by-qualified-name')
defun('stella/native-slot?')
defun('stella/native-slot-home')
defun('stella/read-slot-value')
defun('stella/write-slot-value')
defun('stella/cpp-find-native-slot-value-offset')
defun('stella/get-constructor')
defun('stella/lookup-slot')
defslot('stella/slot.slot-name')

defun('stella/lookup-class-by-qualified-name')
#defun('stella/lookup-class-cpp-type-by-name') # done manually
#defun('stella/get-constructor')               # needed earlier
defmethod('stella/class.name')
defmethod('stella/class.all-class-slots')
defmethod('stella/class.direct-super-classes')
defmethod('stella/class.super-classes')
defslot('stella/relation.documentation')

defun('stella/type-to-class')
defun('stella/defined-type?')
defun('stella/canonical-type')
defslot('stella/surrogate.surrogate-value')
defun('stella/real-type-specifier')
defun('stella/type-spec-to-base-type')

defmethod('stella/symbol.lookup-global-variable')
defun('stella/lookup-global-variable-by-qualified-name')
defun('stella/read-global-variable-value')
defun('stella/write-global-variable-value')

defglobal('stella/NIL')
defslot('stella/cons.value')
defslot('stella/cons.rest')
defun('stella/cons', _except=False)
defun('stella/nil?', _except=False)
defmethod('stella/cons.empty?')
defmethod('stella/cons.length')
defmethod('stella/cons.first')
defmethod('stella/cons.nth')
defmethod('stella/cons.nth-rest')
defmethod('stella/cons.reverse')
defmethod('stella/cons.remove')
defun('stella/append')
defmethod('stella/object.consify')
defmethod('stella/cons.consify')
defun('stella/make-cons-list', _except=False)
defun('stella/cons-set-first-get-next', _except=False)

defglobal('stella/NIL-LIST')
defslot('stella/list.the-cons-list')
defmethod('stella/list.consify')

defmethod('stella/vector.allocate-iterator')
defmethod('stella/vector.length')
defmethod('stella/vector.nth')
defmethod('stella/vector.consify')

defslot('stella/generalized-symbol.symbol-name')

defslot('stella/iterator.value')
defmethod('stella/cons-iterator.next?')
defmethod('stella/list-iterator.next?')
defmethod('stella/all-class-slots-iterator.next?')
defmethod('stella/types-to-classes-iterator.next?')
defmethod('stella/all-purpose-iterator.next?')
defmethod('stella/abstract-iterator.length')
defmethod('stella/iterator.consify')

defglobal('stella/*module*')
stella.pdef.Module._oMODULEo = _ffi.cast("void**", 
    boot.getGlobalVariableNativeObject(stella.pdef.lookupGlobalVariableByQualifiedName('stella/*module*')._stellaObject))
defglobal('stella/*context*')
defglobal('stella/*root-module*')
defglobal('stella/*stella-module*')
defslot('stella/module.module-full-name')
defmethod('stella/object.home-module')
defun('stella/cpp-yield-namespace-prefix-from-module')
defun('stella/cpp-translate-name')

defmethod('stella/mutable-string.length')

defun('stella/yield-constructor-definition')
defun('stella/define-method-from-parse-tree')
defslot('stella/method-slot.function-code')
defun('stella/define-external-slot-from-stringified-source')

defconstructor('stella/cons')

# make sure a few essential function wrappers have been properly installed before bootstrap ends:
for qname in ['stella/parse-stella-name', 'stella/get-stella-module']:
    cws.getStellaFuncallWrapper(qname)

com._bootstrapCompleted = True

# other useful definitions:

defglobal('stella/*stella-version*')
defglobal('stella/*stella-gc-version*')

defun('stella/load-file')
defun('stella/evaluate-string')

defun('stella/define-logical-host-property')
defun('stella/lookup-logical-host-property')
defun('stella/get-logical-host-property')

if stella.pdef.lookupLogicalHostProperty("ST", stella.pdef.internKeyword('root-directory')) is None:
    stella.pdef.defineLogicalHostProperty(
        "ST", stella.pdef.internKeyword('root-directory'), stella.pdef.wrapString(com.STELLA_HOME))
