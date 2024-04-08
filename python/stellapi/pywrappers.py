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
Defining Python wrappers for STELLA functions and objects.
"""

from __future__ import print_function, division, absolute_import

import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str
    long = int

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO
import re

import stellapi.common as com
from   stellapi.common import FFI as _ffi
from   stellapi.utils import ApiException
from   stellapi.namespaces import boot, stella, \
           getStellaModuleCDefNamespace, getStellaModulePDefNamespace
from   stellapi.gcollect import gcProtectObject
from   stellapi.exceptions import clearLastException, getLastException
import stellapi.signatures as sigs
import stellapi.callwrappers as cws
import stellapi.types as types
# TO DO: for now this is needed to make the type converter references in wrappers work:
from   stellapi.types import *


### Defining/Wrapping C-level API functions

# Suppose we want to generate the stella.pdef wrapper for 'stella/type-to-class', we have these steps:
# (1) access the STELLA C-code that actually calls the implementation (bound to stella.cdef.typeToClass)
# (2) create a wrapper method that handles all the type conversion, GC protection, exception handling,
#     this also deals with automatic creation of proxy classes behind the scenes
# (3) link the wrapper method to an appropriate Python name and namespace
# Here is the automatically generated Python wrapper code using a STELLA function call wrapper:

"""
>>> print(defineStellaFunctionPythonWrapperCode('stella/type-to-class'))
def pdef_typeToClass(type):
    type = pythonToStellaObjectOfType(type, stellapi.stella.pdef.Surrogate)
    clearLastException()
    _vaL = stellapi.stella.cdef.callStellaFun_RvoidP_IvoidP(stellapi.stella.cdef.typeToClass, type)
    if _vaL == _ffi.NULL:
        if getLastException() != None:
            raise getLastException()
    if _vaL != _ffi.NULL:
        gcProtectObject(_vaL)
    return stellaToPythonObject(_vaL)

# this part is handled by defineStellaFunction:
stella.pdef.typeToClass = pdef_typeToClass
"""

def lookupObjectByQualifiedName(qualName):
    """Convenience accessor that finds an object with this qualified name.  Note that these
    names can be ambiguous - e.g., the `cons' function or class, so there is a preference order.
    NOTE: this will not work correctly during bootstrap.
    """
    return (stella.pdef.lookupFunctionByQualifiedName(qualName) or
            stella.pdef.lookupSlotByQualifiedName(qualName) or
            stella.pdef.lookupClassByQualifiedName(qualName) or
            stella.pdef.lookupGlobalVariableByQualifiedName(qualName))

def getValueReference(value, nameDict):
    """Create a string representation of `value' that can be used to refer to it.
    For objects or complex lists, etc. we create a unique new name in `nameDict'
    (usually globals() or locals()) pointing to `value'.
    """
    valueType = type (value)
    if value is None or valueType in (int, float, long, bool):
        return str(value)
    elif valueType in (str, unicode):
        return '"""' + value + '"""'
    else:
        try:
            i = (hash(value) % 10000) + 999
        except:
            i = (hash(repr(value)) % 10000) + 999
        while True:
            initName = '_init' + str(i)
            if nameDict.get(initName) is None:
                nameDict[initName] = value
            if nameDict.get(initName) is value:
                break
            i += (i % 1000) + 11
        return initName

def getApiObjectReference(pobj):
    """Return a string that allows us to access `pobj' from this Python module.
    `pobj' is assumed to be an API object such as a namespace or function that is visible
    or reachable from here.  This is a more specialized version of `getValueReference'
    that doesn't require the introduction of a name in some globals or locals dictionary.
    """
    if pobj == _ffi.CData:
        # special-case this one, since it points to '_cffi_backend.CData':
        return '_ffi.CData'
    mod = pobj.__module__
    if not isinstance(mod, str):
        mod = mod.__name__
    if mod in ['__builtin__', '__main__', com.stellapiModule]:
        return pobj.__name__
    else:
        ref = mod + '.' + pobj.__name__
        # since we renamed the file, we access the actual module here based on this fn:
        thismod = getApiObjectReference.__module__ + '.'
        # remove redundant prefixes not needed to access from this module:
        while ref.startswith(thismod):
            ref = ref[len(thismod):]
        return ref

def getObjectFullname(pobj):
    """Return the fully qualified name of `pobj'."""
    mod = pobj.__module__
    if not isinstance(mod, str):
        mod = mod.__name__
    return mod + '.' + pobj.__name__

def analyzeQualifiedFunctionName(qualName):
    # Derive various bits of function definition information based on `qualName'.
    isMethod = cws.isStellaMethodName(qualName)
    if isMethod:
        cppsig = sigs.getStellaMethodCppSignature(qualName)
        csig = sigs.getStellaMethodCSignature(qualName)
    else:
        cppsig = sigs.getStellaFunctionCppSignature(qualName)
        csig = sigs.getStellaFunctionCSignature(qualName)
    cppns, cppfn = types.parseCppQualifiedName(sigs.stellaSigFunctionName(cppsig))
    if isMethod:
        cppfn = cppfn.replace('::', '_')
    if isMethod:
        wrapperName = cws.stellaMethCSigToCallWrapperName(csig)
    else:
        wrapperName = cws.stellaFunCSigToCallWrapperName(csig)
    if isMethod:
        cCode = sigs.getStellaMethodCode(qualName)
    else:
        cCode = sigs.getStellaFunctionTypedCode(qualName)
    # this is getting long, maybe use a dict instead:
    return (isMethod, cppsig, csig, cppns, cppfn, wrapperName, cCode)

def defineStellaFunctionPythonWrapperCode(qualName, gc='auto', exceptions=True, useWrapper='auto', pyin=True, pyout=True, 
                                          doc=None, argSpecs=None, preproc=None):
    """Return a Python wrapper definition to call the STELLA function named `qualName'.
    This handles all the intricacies of GC protection, exception handling and call wrapper
    generation and usage.  If in doubt about what's going on with a specific wrapper, call
    this function and print the result to see the generated code.  Set `pyin' to False to
    prevent Python to CData conversion of input parameters, similarly, set `pyout' to False
    to leave return values as CData and prevent automatic conversion to Python types.
    """
    ### TO DO: figure out whether sequential GC-protection of multiple return values is safe
    isMethod, cppsig, csig, cppns, cppfn, wrapperName, cCode = analyzeQualifiedFunctionName(qualName)
    rtype = sigs.stellaSigStellaReturnType(cppsig)
    isvoid = rtype == '/STELLA/@VOID'
    ismulti = False
    isptr = sigs.stellaSigNativeReturnType(csig).endswith('*')
    arity = sigs.stellaSigArity(cppsig)
    defn = StringIO()
    fnname = 'pdef_' + cppfn

    # generate function name and parameter list:
    argSpecs = argSpecs or {}
    needComma = False
    defn.write('def %s(' % fnname)
    for i in range(arity):
        if sigs.stellaSigIsReturnPara(cppsig, i):
            ismulti = True
            continue
        if needComma:
            defn.write(', ')
        paraName = sigs.stellaSigParaNativeName(cppsig, i)
        defn.write(paraName)
        needComma = True
        if paraName in argSpecs:
            # parameter has been made optional with possible initial value:
            defn.write('=%s' % argSpecs[paraName])
            del argSpecs[paraName]
    # add any remaining auxiliary parameters that might be used in preprocessing:
    for paraName, paraValue in argSpecs.items():
        if needComma:
            defn.write(', ')
        defn.write('%s=%s' % (paraName, paraValue))
        needComma = True
    defn.write('):\n')

    # add documentation:
    if doc is not None:
        doc = '"""%s\n"""' % doc
        doc = re.sub('^', '    ', doc, flags=re.MULTILINE)
        defn.write(doc)
        defn.write('\n')

    # add any preprocessing statements:
    preproc = type(preproc) in (list, tuple) and list(preproc) or preproc and [preproc] or []
    for stmt in preproc:
        defn.write(re.sub('^', '    ', stmt, flags=re.MULTILINE))
        defn.write('\n')

    # convert input arguments to their proper STELLA types:
    for i in range(arity):
        pname = sigs.stellaSigParaNativeName(cppsig, i)
        ptype = sigs.stellaSigParaStellaType(cppsig, i)
        ppxtype = types.getStellaTypeProxyClass(ptype)
        toStella = types.lookupTypeInfoFacet(ptype, 'toStella')
        if not sigs.stellaSigIsReturnPara(cppsig, i):
            if pyin and toStella is not None:
                if toStella != '':
                    defn.write('    %s = %s(%s)\n' % (pname, toStella, pname))
            elif pyin:
                ptype = getApiObjectReference(ppxtype)
                defn.write('    %s = pythonToStellaObjectOfType(%s, %s)\n' % (pname, pname, ptype))
        else:
            ptype = sigs.stellaSigParaNativeCppType(csig, i)
            defn.write('    %s = _ffi.new("%s[]", 1)\n' % (pname, ptype[0:-1]))

    # prepare for exception handling:
    if exceptions:
        defn.write('    clearLastException()\n')

    # create STELLA function call either directly or via call wrapper:
    qualCppFn = getApiObjectReference(getStellaModuleCDefNamespace(qualName)) + '.' + cppfn
    qualWrapper = cws.getStellaFuncallWrapperNamespace(qualName, wrapperName).name + '.' + wrapperName
    defn.write('    ')
    if not isvoid:
        defn.write('_vaL = ')
    defn.write((useWrapper and qualWrapper) or qualCppFn)
    defn.write('(')
    if useWrapper:
        defn.write('%s, ' % qualCppFn)
    for i in range(arity):
        if i > 0:
            defn.write(', ')
        pname = sigs.stellaSigParaNativeName(cppsig, i)
        defn.write(pname)
    defn.write(')\n')

    # check whether any exceptions occurred and raise them on the Python side:
    if exceptions:
        if isvoid or not isptr:
            defn.write('    if getLastException() != None:\n')
            defn.write('        raise getLastException()\n')
        else:
            defn.write('    if _vaL == _ffi.NULL:\n')
            defn.write('        if getLastException() != None:\n')
            defn.write('            raise getLastException()\n')

    if ismulti:
        # dereference multiple return values:
        for i in range(arity):
            if sigs.stellaSigIsReturnPara(cppsig, i):
                pname = sigs.stellaSigParaNativeName(cppsig, i)
                defn.write('    %s = %s[0]\n' % (pname, pname))

    # GC-protect any return value(s) if necessary:
    if not isvoid and (gc == True or (gc == 'auto' and isptr)):
        # for some extra complexity, we could combine this NULL test with the one above:
        defn.write('    if _vaL != _ffi.NULL:\n')
        defn.write('        gcProtectObject(_vaL)\n')
    if ismulti:
        for i in range(arity):
            if sigs.stellaSigIsReturnPara(cppsig, i):
                pname = sigs.stellaSigParaNativeName(cppsig, i)
                ptype = sigs.stellaSigParaNativeCppType(csig, i)
                if gc == True or (gc == 'auto' and ptype.find('*') > 0):
                    defn.write('    if %s != _ffi.NULL:\n' % pname)
                    defn.write('        gcProtectObject(%s)\n' % pname)

    # handle Python type conversion for return value(s):
    if not isvoid:
        defn.write('    return ')
        if ismulti:
            # if we have multiple return values, we return a tuple:
            defn.write('(')
        rpxtype = types.getStellaTypeProxyClass(rtype)
        toPython = types.lookupTypeInfoFacet(rtype, 'toPython')
        if not pyout or toPython == '':
            defn.write('_vaL')
        elif toPython is not None:
            defn.write('%s(_vaL)' % toPython)
        elif issubclass(rpxtype, stella.pdef.Object):
            # determine proper proxy object type dynamically:
            defn.write('stellaToPythonObject(_vaL)')
        else:
            # wrap return value in proxy object indicated by return type:
            defn.write('stellaToPythonObjectOfType(_vaL, %s)' % getApiObjectReference(rpxtype))
        # handle conversion of remaining return values:
        if ismulti:
            for i in range(arity):
                if sigs.stellaSigIsReturnPara(cppsig, i):
                    pname = sigs.stellaSigParaNativeName(cppsig, i)
                    ptype = sigs.stellaSigParaStellaType(cppsig, i)
                    ppxtype = types.getStellaTypeProxyClass(ptype)
                    toPython = types.lookupTypeInfoFacet(ptype, 'toPython')
                    defn.write(',\n            ')
                    if not pyout or toPython == '':
                        defn.write(pname)
                    elif toPython is not None:
                        defn.write('%s(%s)' % (toPython, pname))
                    elif issubclass(ppxtype, stella.pdef.Object):
                        defn.write('stellaToPythonObject(%s)' % pname)
                    else:
                        defn.write('stellaToPythonObjectOfType(%s, %s)' % (pname, getApiObjectReference(ppxtype)))
        if ismulti:
            defn.write(')')
        defn.write('\n')
    return defn.getvalue()

def normalizeArgumentSpecs(argSpecs, nameDict):
    """Given a set of argument specs `argSpecs' which contains parameter names with initial values, normalize the
    given values to strings that can be used as initial keyword argument values in the definition of a function.
    """
    normArgSpecs = {}
    for para, argSpec in (argSpecs or {}).items():
        normArgSpecs[para] = getValueReference(argSpec, nameDict)
    return normArgSpecs

def getCombinedDocumentation(qualName, pydoc):
    objectDoc = None
    if com._bootstrapCompleted:
        object = lookupObjectByQualifiedName(qualName)
        if object is not None:
            objectDoc = object.documentation
    doc = None
    if objectDoc is not None:
        doc = objectDoc
        if pydoc is not None:
            doc += '\n' + pydoc
    elif pydoc is not None:
        doc = pydoc
    return doc

def defineStellaFunction(qualName, gc='auto', exceptions=True, useWrapper='auto', pyin=True, pyout=True, doc=None, argSpecs=None, preproc=None):
    isMethod, cppsig, csig, cppns, fnname, wrapperName, cCode = analyzeQualifiedFunctionName(qualName)
    ### TO DO: for now, use a wrapper unless explicitly told otherwise:
    useWrapper = isMethod or (useWrapper is True) or (useWrapper == 'auto' and exceptions)
    argSpecs = normalizeArgumentSpecs(argSpecs, locals())
    comboDoc = getCombinedDocumentation(qualName, doc)
    pfunSourceCode = defineStellaFunctionPythonWrapperCode(qualName, gc=gc, exceptions=exceptions, useWrapper=useWrapper, 
                                                           pyin=pyin, pyout=pyout, doc=comboDoc, argSpecs=argSpecs, preproc=preproc)
    exec(pfunSourceCode, globals(), locals())
    pfunName = 'pdef_' + fnname
    pfunCode = locals()[pfunName]
    cdefns = getStellaModuleCDefNamespace(qualName)
    pdefns = getStellaModulePDefNamespace(qualName)
    setattr(cdefns, fnname, cCode)
    # link Python code object back to the namespace:
    setattr(pfunCode, '__module__', pdefns)
    if not isMethod:
        setattr(pdefns, fnname, pfunCode)
        setattr(pfunCode, '__name__', fnname)
    if com.PRESERVE_WRAPPER_SOURCE:
        # this is useful for inspection and debugging:
        setattr(pfunCode, 'func_source', pfunSourceCode)
    if useWrapper:
        cws.registerStellaFuncallWrapper(qualName)
        wrapper = cws.lookupStellaFuncallWrapper(qualName)
        cws.activateStellaFuncallWrapper(qualName, wrapper or cws.stellaFuncallWrapperAutoLoader)
    return pfunCode

def defineStellaMethod(qualName, gc='auto', exceptions=True, useWrapper='auto', pyin=True, pyout=True, doc=None, argSpecs=None, preproc=None):
    # TO DO: figure out whether we should/need to define all super methods as well.
    slot, klass = stella.pdef.lookupSlotAndClassByQualifiedName(qualName)
    if slot is None or not isinstance(slot, stella.pdef.MethodSlot):
        raise ApiException('No method with this name: ' + qualName)
    pfunCode = defineStellaFunction(qualName, gc=gc, exceptions=exceptions, useWrapper=useWrapper, pyin=pyin, pyout=pyout,
                                    doc=doc, argSpecs=argSpecs, preproc=preproc)
    cppsig = sigs.getStellaMethodCppSignature(qualName)
    # for methods we have to do this twice to also get rid of the class prefix:
    slotns, slotname = types.parseCppQualifiedName(sigs.stellaSigFunctionName(cppsig))
    slotns, slotname = types.parseCppQualifiedName(slotname)
    # NOTE: we mirror allocation by attaching the code method on the native slot home:
    homeProxyClass = types.getStellaTypeProxyClass(stella.pdef.nativeSlotHome(slot, klass))
    # unfortunately we cannot do this for builtin types, only for STELLA classes:
    if issubclass(homeProxyClass, types.ProxyClass):
        setattr(homeProxyClass, slotname, pfunCode)
        # KLUDGE: check if we are dealing with a method on a literal slot which is implemented via a
        # C++ function that starts with the literal type as its name - only matters for MUTABLE-STRING:
        if not issubclass(homeProxyClass, stella.pdef.Object) and slotname.lower().startswith(homeProxyClass.__name__.lower()):
            # split off the type prefix, e.g., convert mutableStringLength => length:
            slotname = slotname[len(homeProxyClass.__name__):]
            slotname = slotname[0].lower() + slotname[1:]
            setattr(homeProxyClass, slotname, pfunCode)
        setattr(pfunCode, '__name__', slotname)
        return homeProxyClass, slotname
    else:
        return homeProxyClass, pfunCode

def defineStellaStorageSlot(qualName):
    slot, klass = stella.pdef.lookupSlotAndClassByQualifiedName(qualName)
    if slot is None or not isinstance(slot, stella.pdef.StorageSlot):
        raise ApiException('No storage slot with this name: ' + qualName)
    cppsig = sigs.getStellaStorageSlotCppSignature(qualName)
    slotns, slotname = types.parseCppQualifiedName(sigs.stellaSigFunctionName(cppsig))
    slottype = sigs.stellaSigStellaReturnType(cppsig)
    # NOTE: we mirror allocation by putting the accessor property on the native slot home which does
    # the right thing for slots such as 'iterator.value' that are inherited from abstract classes;
    # we also assume that `getStellaTypeProxyClass' will raise an error if `klass' does not have a proxy:
    homeProxyClass = types.getStellaTypeProxyClass(stella.pdef.nativeSlotHome(slot, klass))
    valueProxyClass = types.getStellaTypeProxyClass(slottype)
    # lookup various type conversion info:
    normType = types.lookupTypeInfoFacet(slottype, 'type', slottype)
    cType = types.lookupTypeInfoFacet(normType, 'cType')
    toPython = types.lookupTypeInfoFacet(normType, 'toPython')
    toStella = types.lookupTypeInfoFacet(normType, 'toStella')
    gcProtect = types.lookupTypeInfoFacet(normType, 'gcProtect', True)
    wrapfn = types.lookupTypeWrapper(slottype)
    unwrapfn = types.lookupTypeUnwrapper(slottype)

    # check if we can perform native slot access on klass.slot which should be faster than read/write-slot-value:
    nativeOffset = -1
    if stella.pdef.nativeSlotP(slot) and not boot.definedListP(boot.classRequiredSlotNames(klass._stellaObject)):
        constructor = stella.pdef.getConstructor(klass, False)
        if constructor is not None:
            sobj = _ffi.cast('void* (*)()', constructor)()
            nativeOffset = stella.cdef.cppFindNativeSlotValueOffset(sobj, slot._stellaObject)

    # construct the reader method - we generate the source code first and then call `exec' due to the various different
    # incantations, however, closures don't work with string exec's, since the string gets compiled first before globals
    # and locals are considered, so we pass them in via parameter init values for speed (also see `defconstructor'):
    rdr = StringIO()
    rdr.write('def slotReader(self%s):\n')
    locvars = ''
    if nativeOffset >= 0:
        # return _toPython(gcProtectObject(_ffi.cast('void**', self._stellaObject + NO)[0]))
        cTypePtr = _ffi.typeof(cType + '*')
        locvars += ', _cTypePtr=cTypePtr'
        expr = '_ffi.cast(_cTypePtr, self._stellaObject + %d)[0]' % nativeOffset
        if gcProtect:
            expr = 'gcProtectObject(' + expr + ')'
        if toPython is not None and toPython != '':
            toPython = types.evalTypeInfoName(toPython)
            locvars += ', _toPython=toPython'
            expr = '_toPython(' + expr + ')'
        rdr.write('    return ' + expr + '\n')
    elif unwrapfn is not None:
        # handles literal-valued dynamic slots for example:
        unwrapfn = types.evalTypeInfoName(unwrapfn)
        locvars += ', _slot=slot, _unwrapfn=unwrapfn'
        rdr.write('    return _unwrapfn(stella.pdef.readSlotValue(self, _slot))\n')
    else:
        # handles object-valued dynamic slots for example:
        locvars += ', _slot=slot'
        rdr.write('    return stella.pdef.readSlotValue(self, _slot)\n')
    rdr = rdr.getvalue() % locvars
    rdrSource = rdr
    exec(rdr, globals(), locals())
    rdr = locals()['slotReader']

    # construct the write method - same considerations apply:
    wtr = StringIO()
    wtr.write('def slotWriter(self, value%s):\n')
    locvars = ''
    if nativeOffset >= 0:
        locvars += ', _cTypePtr=cTypePtr'
        if normType == '@OBJECT':
            valueExpr = 'value and value._stellaObject or _ffi.NULL'
        elif toStella is not None and toStella != '':
            toStella = types.evalTypeInfoName(toStella)
            locvars += ', toStella=toStella'
            valueExpr = 'toStella(value)'
        else:
            valueExpr = 'value'
        wtr.write('    _ffi.cast(_cTypePtr, self._stellaObject + %d)[0] = %s\n' % (nativeOffset, valueExpr))
    elif wrapfn is not None:
        wrapfn = types.evalTypeInfoName(wrapfn)
        locvars += ', _slot=slot, _wrapfn=wrapfn'
        wtr.write('    stella.pdef.writeSlotValue(self, _slot, _wrapfn(value))\n')
    else:
        locvars += ', _slot=slot'
        wtr.write('    stella.pdef.writeSlotValue(self, _slot, value)\n')
    wtr = wtr.getvalue() % locvars
    wtrSource = wtr
    exec(wtr, globals(), locals())
    wtr = locals()['slotWriter']

    # now attach reader and writer as a property object to slot's home proxy class:
    setattr(homeProxyClass, slotname, property(rdr, wtr))
    if com.PRESERVE_WRAPPER_SOURCE:
        # this is useful for inspection and debugging, check like this:
        # > print spi.stella.pdef.Cons.value.fget.func_source
        # > print spi.stella.pdef.Cons.value.fset.func_source
        setattr(rdr, 'func_source', rdrSource)
        setattr(wtr, 'func_source', wtrSource)
    # return a representation of the Python object:
    return homeProxyClass, slotname

"""
# here's how to access an object slot directly via a byte offset which we obtained like this:
#    std::cout << "Class.classTaxonomyNode: " << offsetof(Class, classTaxonomyNode) << std::endl;
# this means we could store a native access object which would be a Lisp symbol, C++ byte offset
# or Java field and use that to read the slot (or global var) instead of creating access methods.

>>> sgt = spi.stella.pdef.internSurrogate('fumbar')
>>> klass = sgt.primaryClass()
>>> klass._stellaObject
<cdata 'void *' 0xe4b5a0>
>>> klass._stellaObject + 120
<cdata 'void *' 0xe4b618>
>>> spi._ffi.cast('void**', klass._stellaObject + 120)
<cdata 'void * *' 0xe4b618>
>>> spi._ffi.cast('void**', klass._stellaObject + 120)[0]
<cdata 'void *' 0xe5a2a0>
>>> spi.stellaToPythonObject(_)
<proxy.TaxonomyNode |TN|5900 ([5801,5900]) |C|SURROGATE>
"""

def defineStellaGlobalVariable(qualName):
    # TO DO: consider accessing globals directly at their variable address instead of through accessors
    globalVar = stella.pdef.lookupGlobalVariableByQualifiedName(qualName)
    if globalVar is None:
        raise ApiException('No global variable with this name: ' + qualName)
    cdefGlobalVar = globalVar._stellaObject
    cppsig = sigs.getStellaGlobalVariableCppSignature(qualName)
    gvns, gvname = types.parseCppQualifiedName(sigs.stellaSigFunctionName(cppsig))
    gvtype = sigs.stellaSigStellaReturnType(cppsig)
    valueProxyClass = types.getStellaTypeProxyClass(gvtype)
    wrapfn = types.lookupTypeWrapper(gvtype)
    unwrapfn = types.lookupTypeUnwrapper(gvtype)
    cdefns = getStellaModuleCDefNamespace(qualName)
    pdefns = getStellaModulePDefNamespace(qualName)
    if wrapfn is not None:
        def varReader(self):
            return unwrapfn(stella.pdef.readGlobalVariableValue(globalVar))
        def varWriter(self, value):
            stella.pdef.writeGlobalVariableValue(globalVar, wrapfn(value))
        cdefWrapfn = types.lookupCDefTypeWrapper(gvtype)
        cdefUnwrapfn = types.lookupCDefTypeUnwrapper(gvtype)
        def cdefVarReader(self):
            return cdefUnwrapfn(stella.cdef.readGlobalVariableValue(cdefGlobalVar))
        def cdefVarWriter(self, value):
            stella.cdef.writeGlobalVariableValue(cdefGlobalVar, cdefWrapfn(value))
    else:
        def varReader(self):
            return stella.pdef.readGlobalVariableValue(globalVar)
        def varWriter(self, value):
            # support NULL values, however, we might need a more sophisticated test/conversion here:
            if isinstance(value, valueProxyClass) or value is None:
                stella.pdef.writeGlobalVariableValue(globalVar, value)
            else:
                raise ApiException("Object " + str(value) + " is not of type " + str(valueProxyClass))
        def cdefVarReader(self):
            return stella.cdef.readGlobalVariableValue(cdefGlobalVar)
        def cdefVarWriter(self, value):
            stella.cdef.writeGlobalVariableValue(cdefGlobalVar, value)
    # the property has to be linked to a class, hence, we use type(pdefns):
    setattr(type(pdefns), gvname, property(varReader, varWriter))
    setattr(type(cdefns), gvname, property(cdefVarReader, cdefVarWriter))
    return pdefns, gvname
