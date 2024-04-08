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
Mapping STELLA types onto Python and vice versa.
"""

from __future__ import print_function, division, absolute_import

import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str
    long = int

import stellapi.common as com
from   stellapi.common import FFI as _ffi
from   stellapi.utils import to_bytes, ffi_to_string, ApiException
from   stellapi.namespaces import boot, stella, stellapi, \
           getStellaModuleCDefNamespace, getStellaModulePDefNamespace
from   stellapi.gcollect import gcProtectObject
from   stellapi.signatures import parseCppQualifiedName


### Early function wrappers needed during the bootstrap of the type system

@boot
def _boot_defineSlotReader(classTypeName, slotName):
    """Define a low-level slot reader for class.slot that we can use during bootstrap.
    IMPORTANT: no GC or exception protection is provided here.
    """
    klass = boot.typeToClass(boot.readSExpressionFromString(to_bytes(classTypeName)))
    slotName = boot.readSExpressionFromString(to_bytes(slotName))
    slot = boot.lookupSlot(klass, slotName)
    readerCode = boot.getGenericSlotAccessor(slot, klass, 0)
    readerCode = _ffi.cast("void* (*) (void* obj, void* slotName, void* val, bool set)", readerCode)
    def _slotReader(obj):
        #if obj == _ffi.NULL:
        #    raise ApiException("boot.slotReader: obj is None")
        return gcProtectObject(readerCode(obj, slotName, _ffi.NULL, 0))
    return _slotReader

boot.consValue = boot.defineSlotReader('stella/@cons', 'stella/value')
boot.consRest = boot.defineSlotReader('stella/@cons', 'stella/rest')
boot.classAllSuperClasses = boot.defineSlotReader('stella/@class', 'stella/class-all-super-classes')
boot.classRequiredSlotNames = boot.defineSlotReader('stella/@class', 'stella/class-required-slot-names')

@boot
def _boot_stellaConsToPythonList(cons):
    """Convert a STELLA CData `cons' list into a Python list of CData values."""
    consList = []
    rest = boot.consRest(cons)
    # this worked around some bug with a NULL at the end of a cons list which is fixed now:
    #while rest != _ffi.NULL and cons != rest:
    while cons != rest:
        consList.append(boot.consValue(cons))
        cons = rest
        rest = boot.consRest(rest)
    return consList

@stella.pdef
def _coerceToString(object):
    """Manually wrapped version of `coerceToString' for early usage."""
    object = pythonToStellaObjectOfType(object, stella.pdef.Object)
    value = boot.coerceToString(object)
    # this isn't really necessary for strings, but just for good measure:
    gcProtectObject(value)
    return stellaToPythonObjectOfType(value, str)

@stella.pdef
def _lookupClassCppTypeByName(qualName):
    """Manually wrapped version of `lookupClassCppTypeByName' for early usage."""
    # can't yet call this during bootstrap:
    #qualName = pythonToStellaObjectOfType(qualName, str)
    assert(isinstance(qualName, str))
    value = boot.lookupClassCppTypeByName(to_bytes(qualName))
    # this isn't really necessary for strings, but just for good measure:
    gcProtectObject(value)
    # can't yet call this during bootstrap:
    #return stellaToPythonObjectOfType(value, str)
    return ffi_to_string(value)


### Partial STELLA proxy class hierarchy

# Proxy classes now provide a partial mirror of the STELLA class hierarchy to facilitate type
# and subtype tests as well as slot and method inheritance.  Slots and method hierarchies
# might also be mirrored only partially as needed.  However, we do not need to know or mirror the
# exact superclasses for each mapped STELLA class, that aspect is handled automatically.
# Proxy classes can be defined in three ways:
# (1) Explicitly as done for various STELLA classes below.  In this case they must use `ProxyClass'
#     as their sole parent as well as appropriate namespace annotations to smoothly interoperate with
#     implicitly defined classes, and they must provide a proper `_stellaTypePath'.  Explicit classes
#     are useful to add or overide methods.  They must also be defined before any implicit definition
#     of the class ocurs, otherwise an error will be raised.
# (2) Implicitly behind the scenes when a new object type is mapped for the first time, or when a
#     proxy super class is needed during a class definition (see `ProxyMetaClass' below).
# (3) Via `defclass' which for now simply forces an implicit definition for the specified class
# The resulting proxy class hierarchy is partial in the sense that only the various materialized or
# otherwise referenced object types exist, together with the upward closure of their super types.
# By mirroring the class hiearchy to this degree, slot and method inheritance works automatically as
# expected which was not the case for the __subclasshook__ machinery we used before.  Inheritance also
# changes dynamically if we add new slots (properties) or methods anywhere in the proxy class hierarchy.

_cdataType    = _ffi.CData
_voidstarType = _ffi.typeof('void *')
_charstarType = _ffi.typeof('char *')
_pointerTypes = [_voidstarType, _charstarType]
_intType      = _ffi.typeof("int")
_doubleType   = _ffi.typeof("double")

typeInfoTable = {}

def normalizeTypeInfoType(typeSpec):
    proxyClass = lookupStellaTypeProxyClass(typeSpec)
    if proxyClass is not None and issubclass(proxyClass, getStellaTypeProxyClass('/STELLA/@OBJECT')):
        return '/STELLA/@OBJECT'
    else:
        return typeSpec

def lookupTypeInfo(typeSpec, norm=True):
    if norm:
        typeSpec = normalizeTypeInfoType(typeSpec)
    return typeInfoTable.get(typeSpec)

def lookupTypeInfoFacet(typeSpec, facet, dflt=None, norm=True):
    typeInfo = lookupTypeInfo(typeSpec, norm=norm)
    if typeInfo is not None:
        value = typeInfo.get(facet)
        if value is not None:
            return value
    return dflt

def insertTypeInfo(info):
    typeInfoTable[info['type']] = info
    typeInfoTable['/STELLA/' + info['type']] = info
    wrappedType = typeInfoTable.get('wrappedType')
    if wrappedType is not None:
        typeInfoTable[wrappedType] = info
        typeInfoTable['/STELLA/' + wrappedType] = info

def evalTypeInfoName(name):
    if isinstance(name, str):
        return eval(name)
    else:
        return name
    
for info in [
    # we use the empty string for toPython and toStella to indicate "no transformation", since that will
    # also lead to legal syntax when a conversion function call is constructed where the fn is empty:
    {'type': '@OBJECT', 'pythonType': '_ffi.CData', 'cType': 'void*', 'proxyType': 'stella.pdef.Object',
     'gcProtect': True, 'toPython': 'stellaToPythonObject'}, # for now, we might want a more specialized converter later
    {'type': '@INTEGER', 'pythonType': 'int', 'cType': 'int', 'gcProtect': False, 'toPython': '', 'toStella': '',
     'wrappedType': '@INTEGER-WRAPPER', 'wrapFunction': 'wrapInteger', 'unwrapFunction': 'unwrapInteger'},
    {'type': '@LONG-INTEGER', 'pythonType': 'long', 'cType': 'long long int', 'gcProtect': False, 'toPython': '', 'toStella': '',
     'wrappedType': '@LONG-INTEGER-WRAPPER', 'wrapFunction': 'wrapLongInteger', 'unwrapFunction': 'unwrapLongInteger'},
    {'type': '@FLOAT', 'pythonType': 'float', 'cType': 'double', 'gcProtect': False, 'toPython': '', 'toStella': '',
     'wrappedType': '@FLOAT-WRAPPER', 'wrapFunction': 'wrapFloat', 'unwrapFunction': 'unwrapFloat'},
    # ISSUE: we need GC-protection only if strings stay at C-level, not if we copy them into or out of Python:
    {'type': '@STRING', 'pythonType': 'str', 'cType': 'const char*', 'gcProtect': True,
     'toPython': 'ffi_to_string', 'toStella': 'pythonStringToStellaString',
     'wrappedType': '@STRING-WRAPPER', 'wrapFunction': 'wrapString', 'unwrapFunction': 'unwrapString'},
    {'type': '@MUTABLE-STRING', 'pythonType': 'str', 'cType': 'char*', 'gcProtect': True,
     'toPython': '(lambda x: stella.pdef.MutableString(x))', 'toStella': '(lambda x: pythonToStellaObjectOfType(x, stella.pdef.MutableString))',
     'wrappedType': '@MUTABLE-STRING-WRAPPER', 'wrapFunction': 'wrapMutableString', 'unwrapFunction': 'unwrapMutableString'},
    {'type': '@CHARACTER', 'pythonType': 'bytes', 'cType': 'char', 'gcProtect': False, 'toPython': '_ffi.string', 'toStella': '',
     'wrappedType': '@CHARACTER-WRAPPER', 'wrapFunction': 'wrapCharacter', 'unwrapFunction': 'unwrapCharacter'},
    {'type': '@FUNCTION-CODE', 'pythonType': '_ffi.CData', 'cType': 'void*', 'gcProtect': False,
     'wrappedType': '@FUNCTION-CODE-WRAPPER', 'wrapFunction': 'wrapFunctionCode', 'unwrapFunction': 'unwrapFunctionCode'},
    {'type': '@METHOD-CODE', 'pythonType': '_ffi.CData', 'cType': 'void*', 'gcProtect': False,
     'wrappedType': '@METHOD-CODE-WRAPPER', 'wrapFunction': 'wrapMethodCode', 'unwrapFunction': 'unwrapMethodCode'},
    {'type': '@BOOLEAN', 'pythonType': 'bool', 'cType': 'bool', 'gcProtect': False, 'toPython': 'bool', 'toStella': '',
     'wrappedType': '@BOOLEAN-WRAPPER', 'wrapFunction': 'wrapBoolean', 'unwrapFunction': 'unwrapBoolean'},
    ]:
    insertTypeInfo(info)


stellaToProxyClassMap = {}

stellaToProxyClassMap[_charstarType] = str
stellaToProxyClassMap[_intType] = int
stellaToProxyClassMap[_doubleType] = float

stellaToProxyClassMap['/STELLA/@STRING'] = str
# we now use a dedicated proxy class defined below:
#stellaToProxyClassMap['/STELLA/@MUTABLE-STRING']
stellaToProxyClassMap['/STELLA/@CHARACTER'] = str
stellaToProxyClassMap['/STELLA/@INTEGER'] = int
stellaToProxyClassMap['/STELLA/@LONG-INTEGER'] = long
stellaToProxyClassMap['/STELLA/@FLOAT'] = float
stellaToProxyClassMap['/STELLA/@BOOLEAN'] = bool
stellaToProxyClassMap['/STELLA/@FUNCTION-CODE'] = _ffi.CData
stellaToProxyClassMap['/STELLA/@METHOD-CODE'] = _ffi.CData
# for now, until we handle arrays more generally:
stellaToProxyClassMap['/STELLA/@ARRAY'] = _ffi.CData


def allSubClasses(root):
    """Generate all proxy subclasses starting from `root' (using some nested list comprehension magic)."""
    # obsolete now
    return [root] + [cls for sub in root.__subclasses__()
                             for cls in allSubClasses(sub)]

def allStellaSuperClasses(klass):
    """Generate the list of CData STELLA superclasses from `klass' which can be a STELLA or proxy class."""
    # obsolete now
    if isinstance(klass, stella.pdef.Class):
        klass = klass._stellaObject
    return [stella.pdef.Class(_stobj=sup) for sup in boot.stellaConsToPythonList(boot.classAllSuperClasses(klass))]


def typePathToStellaSurrogate(typePath):
    "Access the ffi.cdata STELLA surrogate named by `typePath'."
    return boot.readSExpressionFromString(to_bytes(typePath))

def stellaSurrogateToTypePath(surrogate):
    "Access the type path indicated by this ffi.cdata STELLA `surrogate' object."
    return ffi_to_string(boot.symbolAbsoluteName(surrogate, True))

def typePathToStellaClass(typePath):
    "Access the ffi.cdata STELLA class object named by `typePath'."
    return boot.typeToClass(boot.readSExpressionFromString(to_bytes(typePath)))

def stellaClassToTypePath(cls):
    "Access the type path naming this ffi.cdata STELLA class object."
    return ffi_to_string(boot.symbolAbsoluteName(boot.classSurrogate(cls), True))

def mapTypePathToProxyClass(typePath, proxyClass):
    """Record that the qualified STELLA 'typePath' corresponds to this Python 'proxyClass'.
    We are flexible here and allow non-proxy class type to handle aliased literal types.
    """
    #print 'mapTypePathToProxyClass:', typePath
    stellaSurrogate = typePathToStellaSurrogate(typePath)
    stellaClass = typePathToStellaClass(typePath)
    stellaToProxyClassMap[typePath] = proxyClass
    # also map STELLA surrogate and class objects:
    stellaToProxyClassMap[stellaSurrogate] = proxyClass
    stellaToProxyClassMap[stellaClass] = proxyClass
    # also add inverse mapping:
    stellaToProxyClassMap[proxyClass] = stellaClass
    # guard for cases where `proxyClass' isn't really a proxy class:
    if isinstance(proxyClass, ProxyMetaClass):
        # cache STELLA class on proxy class for fast type tests:
        proxyClass._stellaClass = stellaClass
        # set this too in case we are defining a new class:
        proxyClass._stellaTypePath = typePath

def lookupStellaTypeProxyClass(stellaTypeSpec):
    """Lookup the Python proxy class indicated by 'stellaTypeSpec' which might be a path,
    native STELLA class or Python proxy instance of Class.  Return None if it doesn't exist.
    """
    proxyClass = stellaToProxyClassMap.get(stellaTypeSpec)
    # complex test due to bootstrap case where stella.pdef.Class is not yet defined:
    if proxyClass is None and hasattr(stella.pdef, 'Class') and isinstance(stellaTypeSpec, stella.pdef.Class):
        proxyClass = stellaToProxyClassMap.get(stellaTypeSpec._stellaObject)
    return proxyClass

def getStellaTypeProxyClass(stellaTypeSpec):
    """Lookup or create the Python proxy class indicated by 'stellaTypeSpec' which might be a path,
    native STELLA class or Python proxy instance of Class.
    """
    proxyClass = stellaToProxyClassMap.get(stellaTypeSpec)
    if proxyClass is not None:
        # the standard, fast case:
        return proxyClass
    # complex test due to bootstrap case where stella.pdef.Class is not yet defined:
    if hasattr(stella.pdef, 'Class') and isinstance(stellaTypeSpec, stella.pdef.Class):
        # `stellaTypeSpec' is a proxy Class object, see if its STELLA object is mapped already:
        proxyClass = stellaToProxyClassMap.get(stellaTypeSpec._stellaObject)
        stellaTypeSpec = stellaClassToTypePath(stellaTypeSpec._stellaObject)
    if proxyClass is not None:
        return proxyClass
    # in case we had an unmapped proxy class, we now have a type path as `stellaTypeSpec':
    proxyClass = lookupStellaTypeProxyClass(stellaTypeSpec)
    if proxyClass is not None:
        return proxyClass
    # no luck looking it up, define a new proxy class on the fly:
    defineProxyClassForTypePath(stellaTypeSpec)
    proxyClass = stellaToProxyClassMap.get(stellaTypeSpec)
    return proxyClass

def defineProxyClassForTypePath(typePath):
    """Define a new Python proxy class for the STELLA class identified by `typePath' assuming no
    appropriate proxy class exists at this point, and add it to `stellaToProxyClassMap' for fast lookups.
    """
    stellaSurrogate = typePathToStellaSurrogate(typePath)
    if boot.definedTypeP(stellaSurrogate):
        # we have a defined type such as `(deftype CHARACTER-SET (CONS OF CHARACTER-WRAPPER))':
        stellaSurrogate = stella.pdef.Surrogate(stellaSurrogate)
        canonType = stella.pdef.typeSpecToBaseType(stella.pdef.realTypeSpecifier(stellaSurrogate))
        canonType = stella.pdef.canonicalType(canonType)._stellaObject
        canonTypePath = stellaSurrogateToTypePath(canonType)
        proxyClass = getStellaTypeProxyClass(canonTypePath)
        mapTypePathToProxyClass(typePath, proxyClass)
        return
    if stellaSurrogate != boot.canonicalType(stellaSurrogate):
        # we have an aliased type such as @TYPE or @FILE-NAME:
        canonTypePath = stellaSurrogateToTypePath(boot.canonicalType(stellaSurrogate))
        proxyClass = getStellaTypeProxyClass(canonTypePath)
        mapTypePathToProxyClass(typePath, proxyClass)
        return
    cppType = stella.pdef.lookupClassCppTypeByName(typePath)
    if cppType is None:
        raise ApiException("Non-existing STELLA class: " + typePath)
    namespace, name = parseCppQualifiedName(cppType)
    if namespace is None:
        # must be a literal type or some other problem:
        raise ApiException("Unhandled STELLA class: " + typePath)
    pdef = getStellaModulePDefNamespace(typePath)
    if hasattr(pdef, name):
        # we already have a definition with this name, assume it is an explicitly defined proxy class:
        proxyClass = getattr(pdef, name)
        if not isinstance(proxyClass, ProxyMetaClass):
            raise ApiException(str(pdef) + '.' + name + ' points to a non ProxyClass object')
    else:
        initDict = {'_stellaClass': typePathToStellaClass(typePath),
                    '_stellaTypePath': typePath}
        proxyClass = type(name, (ProxyClass,), initDict)
        proxyClass.__module__ = pdef
        setattr(pdef, name, proxyClass)
    mapTypePathToProxyClass(typePath, proxyClass)


class ProxyMetaClass(type):
    """Metaclass that computes an MRO for a proxy class based on the STELLA class hierarchy.
    We originally used ABCMeta for this but __subclasshook__ didn't do what we wanted it to do
    for inheritance and the mro() machinery is really all we need.
    """
    def mro(cls):
        """Compute an MRO for the proxy class `cls' which is about to be defined.  For this to work, `cls'
        must have `_stellaTypePath' defined in its __dict__ at a minimum.  Since the MRO is not yet computed
        at this point, attributes need to be accessed in a more roundabout way than usual.  Each proxy class
        gets proxy supers for all its STELLA supers plus the two top-level classes `ProxyClass' and `object'.
        """
        standardMro = super(ProxyMetaClass, cls).mro()
        if cls.__name__ in ['ProxyClass', 'UnmappedObject']:
            return standardMro
        classVars = cls.__dict__
        if classVars.get('_stellaTypePath') is None:
            raise ApiException("ProxyMetaClass.mro(): '_stellaTypePath' not initialized for proxy class: " + cls.__name__)
        stellaClass = classVars.get('_stellaClass') or typePathToStellaClass(classVars['_stellaTypePath'])
        supers = [cls]
        for superClass in boot.stellaConsToPythonList(boot.classAllSuperClasses(stellaClass)):
            # this will recursively define MROs for any not yet defined proxy supers:
            supers.append(getStellaTypeProxyClass(stellaClassToTypePath(superClass)))
        supers += [ProxyClass, object]
        return tuple(supers)

class ProxyClass(object):
    """Top-level STELLA API proxy class.  All proxy subclasses will be subs of this and all methods
    and attributes defined here will be inherited by all but can be overridden if necessary.
    """

    # we use our own metaclass so we can use the STELLA subclass test and
    # don't have to mirror the complete class hierarchy on the Python side
    # (see Py2/3 universal code below to add metaclass):
    #__metaclass__ = ProxyMetaClass

    _stellaTypePath = None
    _stellaClass = None

    def primaryClass(self):
        # Implements the STELLA method of the same name, but this version is faster.
        # NOTE: proxy classes are not instances of Class, hence, they can't be used directly
        #       when class objects are needed - this is different from the STELLA side
        # TO DO: figure out if we want to make these instances of Class as well and how
        return stella.pdef.Class(_stobj=self._stellaClass)

    def primaryType(self):
        # Implements the STELLA method of the same name, but this version is faster.
        return stella.pdef.Surrogate(_stobj=boot.classSurrogate(self._stellaClass))

    def __init__(self, _stobj=None):
        self._stellaObject = _stobj

    def __str__(self):
        if self._stellaObject is not None:
            return stella.pdef.coerceToString(self)
        else:
            return '<proxy.' + type(self).__name__ + ' NULL>'

    def __repr__(self):
        return '<proxy.' + type(self).__name__ + ' ' + str(self) + '>'

    def __hash__(self):
        # TO DO: maybe use OBJECT.hash-code() instead?
        return self._stellaObject.__hash__()

    def __eq__(self, other):
        return isinstance(other, stella.pdef.Object) and bool(boot.eqlP(self._stellaObject, other._stellaObject))

    def __ne__(self, other):
        return not isinstance(other, stella.pdef.Object) or not bool(boot.eqlP(self._stellaObject, other._stellaObject))

    def __nonzero__(self):
        # Python 2: still needed for truth value testing so `len' isn't called in boolean expressions
        return True

    def __bool__(self):
        # Python 3: needed for truth value testing so `len' isn't called in boolean expressions
        return True

# Py2/3 universal code to add metaclass adapted from six.add_metaclass (various other adapters failed);
# this should not be this difficult, the Python guys really screwed up on that one:
ProxyClass = ProxyMetaClass('ProxyClass', (object,), {k: v for k, v in ProxyClass.__dict__.items()
                                                      if k not in ['__dict__', '__weakref__']})
    
@stella.pdef
class _Object(ProxyClass):
    _stellaTypePath = '/STELLA/@OBJECT'

    def __iter__(self):
        it = self.allocateIterator()
        it._iter = None
        return it

    def __len__(self):
        return len(self.allocateIterator())

    def pythonify(self):
        """Convert `self' into a possibly nested Python object, list (or tree), that uses natural
        Python equivalents of STELLA data structures wherever possible (e.g. for lists & literals).
        """
        return self

@stella.pdef
class _Cons(ProxyClass):
    _stellaTypePath = "/STELLA/@CONS"

    # iteration support methods:
    def __len__(self):
        return stella.pdef.Cons.length(self)

    def __iter__(self):
        return stella.pdef.Cons(_stobj=self._stellaObject)

    def __next__(self):
        cursor = self._stellaObject
        # use low-level calls here to squeeze out some extra speed (using specialized
        # STELLA access functions for value/rest could improve this further):
        rest = boot.consRest(cursor)
        if cursor == rest:
            # we found NIL or a circular cell:
            raise StopIteration()
        else:
            value = boot.consValue(cursor)
            gcProtectObject(value)
            self._stellaObject = rest
            return stellaToPythonObject(value)

    if PY2:
        next = __next__

    def pythonify(self):
        return [elt.pythonify() for elt in self]

    # for backwards compatibility:
    tree = pythonify

@stella.pdef
class _List(ProxyClass):
    _stellaTypePath = "/STELLA/@LIST"

    def __len__(self):
        return len(self.theConsList)

    def __iter__(self):
        return self.theConsList.__iter__()

    def pythonify(self):
        return self.theConsList.pythonify()

@stella.pdef
class _AbstractIterator(ProxyClass):
    _stellaTypePath = "/STELLA/@ABSTRACT-ITERATOR"

    # We define these here, so they'll be inherited to other iterators by class finalization.
    # This is slightly tricky, since we want to support list(iter) as well as len(iter),
    # however, list calls len which therefore cannot exhaust the iterator to measure its
    # length; for that reason we materialize its items in that case and store them in _iter:
    def __iter__(self):
        if not hasattr(self, '_iter'):
            self._iter = None
        return self

    def __next__(self):
        if self._iter is not None:
            return next(self._iter)
        elif self.nextP():
            return self.value
        else:
            raise StopIteration()

    if PY2:
        next = __next__

    def __len__(self):
        if not hasattr(self, '_iter') or self._iter is None:
            items = [x for x in self]
        else:
            items = [x for x in self._iter]
        self._iter = iter(items)
        return len(items)

@stella.pdef
class _Class(ProxyClass):
    _stellaTypePath = "/STELLA/@CLASS"

@stella.pdef
class _StorageSlot(ProxyClass):
    _stellaTypePath = "/STELLA/@STORAGE-SLOT"

@stella.pdef
class _MethodSlot(ProxyClass):
    _stellaTypePath = "/STELLA/@METHOD-SLOT"

@stella.pdef
class _Module(ProxyClass):
    _stellaTypePath = "/STELLA/@MODULE"
    # TO DO: this stack is not thread safe, but neither are the C++ globals
    _moduleStack = []
    # points to native variable address which gets initialized once we are far enough in the bootstrap:
    _oMODULEo = None

    def __enter__(self):
        # Context manager method to support `with stella.pdef.getStellaModule(...) as mod:'
        self._moduleStack.append(self._oMODULEo[0])
        # NOTE: this runs *change-module-hooks*, maybe use something more low-level:
        stella.cdef.changeCurrentModule(self._stellaObject)
        return self

    def __exit__(self, *_exc):
        stella.cdef.changeCurrentModule(self._moduleStack.pop())

@stella.pdef
class _Surrogate(ProxyClass):
    _stellaTypePath = "/STELLA/@SURROGATE"

@stella.pdef
class _GlobalVariable(ProxyClass):
    _stellaTypePath = "/STELLA/@GLOBAL-VARIABLE"

@stella.pdef
class _LiteralWrapper(ProxyClass):
    """We define various Python operators on literal wrappers to
    make them behave identically to the literal values they wrap.
    """
    _stellaTypePath = "/STELLA/@LITERAL-WRAPPER"

    def __str__(self):
        return str(self.unwrapLiteral())

    def __int__(self):
        return int(self.unwrapLiteral())

    def __long__(self, unwrap=boot.unwrapInteger):
        return long(self.unwrapLiteral())

    def __float__(self, unwrap=boot.unwrapInteger):
        return float(self.unwrapLiteral())

    def __hash__(self):
        return hash(self.unwrapLiteral())

    def __nonzero__(self):
        # Python 2:
        return bool(self.unwrapLiteral())
    def __bool__(self, unwrap=boot.unwrapBoolean):
        # Python 3:
        return bool(self.unwrapLiteral())

    def __lt__(self, other):
        return other > self.unwrapLiteral()
    def __le__(self, other):
        return other >= self.unwrapLiteral()
    def __eq__(self, other):
        return other == self.unwrapLiteral()
    def __ne__(self, other):
        return other != self.unwrapLiteral()
    def __ge__(self, other):
        return other <= self.unwrapLiteral()
    def __gt__(self, other):
        return other < self.unwrapLiteral()

    def pythonify(self):
        return self.unwrapLiteral()

@stella.pdef
class _IntegerWrapper(ProxyClass):
    _stellaTypePath = "/STELLA/@INTEGER-WRAPPER"

    def unwrapLiteral(self, unwrap=boot.unwrapInteger):
        return unwrap(self._stellaObject)

@stella.pdef
class _LongIntegerWrapper(ProxyClass):
    _stellaTypePath = "/STELLA/@LONG-INTEGER-WRAPPER"

    def unwrapLiteral(self, unwrap=boot.unwrapLongInteger):
        return unwrap(self._stellaObject)

@stella.pdef
class _FloatWrapper(ProxyClass):
    _stellaTypePath = "/STELLA/@FLOAT-WRAPPER"

    def unwrapLiteral(self, unwrap=boot.unwrapFloat):
        return unwrap(self._stellaObject)

@stella.pdef
class _StringWrapper(ProxyClass):
    _stellaTypePath = "/STELLA/@STRING-WRAPPER"

    def unwrapLiteral(self, unwrap=boot.unwrapString):
        return ffi_to_string(unwrap(self._stellaObject))

@stella.pdef
class _MutableStringWrapper(ProxyClass):
    _stellaTypePath = "/STELLA/@MUTABLE-STRING-WRAPPER"

    def unwrapLiteral(self, unwrap=boot.unwrapMutableString):
        return _MutableString(unwrap(self._stellaObject))

@stella.pdef
class _CharacterWrapper(ProxyClass):
    _stellaTypePath = "/STELLA/@CHARACTER-WRAPPER"

    def unwrapLiteral(self, unwrap=boot.unwrapCharacter):
        return unwrap(self._stellaObject)

@stella.pdef
class _BooleanWrapper(ProxyClass):
    _stellaTypePath = "/STELLA/@BOOLEAN-WRAPPER"

    def unwrapLiteral(self, unwrap=boot.unwrapBoolean):
        return unwrap(self._stellaObject)

class UnmappedObject(ProxyClass):
    _stellaTypePath = None

    def __init__(self, _stobj=None):
        self._stellaObject = _stobj
        self._stellaType = "UNKNOWN"
        try:
            self._stellaType = ffi_to_string(boot.coerceToString(boot.classSurrogate(boot.primaryClass(self._stellaObject))))
        except:
            pass

    def __str__(self):
        try:
            return ffi_to_string(boot.coerceToString(self._stellaObject))
        except:
            return '<proxy.UNMAPPED_OBJECT ???>'

    def __repr__(self):
        return '<proxy.UNMAPPED_OBJECT ' + self._stellaType + ' ' + str(self) + '>'

@stella.pdef
class _MutableString(ProxyClass):
    # We give mutable strings their own proxy class so we can link to, access and update the
    # underlying memory as opposed to dealing with copies only as we do for regular strings.
    _stellaTypePath = "/STELLA/@MUTABLE-STRING"

    def __repr__(self):
        if self._stellaObject is not None:
            # we use a universal encoding here, so we can display arbitrary bytes:
            value = _ffi.string(self._stellaObject).decode('latin1')
        else:
            value = 'NULL'
        return '<proxy.MutableString "%s">' % value

    def __str__(self):
        if self._stellaObject is not None:
            return ffi_to_string(self._stellaObject)
        else:
            return 'NULL'

    def __len__(self):
        return self.length()

    # these methods allow slicing and destructive updates on the underlying char* array:
    def __getitem__(self, key):
        return _MutableString(self._stellaObject[key])

    def __setitem__(self, key, value):
        self._stellaObject[key] = value

mapTypePathToProxyClass("/STELLA/@MUTABLE-STRING", stella.pdef.MutableString)


### STELLA to Python object conversion

def stellaObjectToPythonType(obj):
    """Map a STELLA ffi.cdata object `obj' onto its corresponding Python type.
       Raise an error if no corresponding Python type could be found."""
    if isinstance(obj, _ffi.CData):
        ctype = _ffi.typeof(obj)
        if ctype == _voidstarType:
            stellaClass = boot.primaryClass(obj)
            proxyClass = lookupStellaTypeProxyClass(stellaClass)
            if proxyClass is None:
                # define proxy classes on the fly if necessary, e.g., to handle subtypes:
                proxyClass = getStellaTypeProxyClass(stellaClassToTypePath(stellaClass))
            if proxyClass is not None:
                return proxyClass
            else:
                #return UnmappedObject
                raise ApiException("Cannot map STELLA object " + str(obj) + " of type " + str(ctype) + " onto Python type")
        else:
            # handle non-object literal types:
            pythonClass = stellaToProxyClassMap.get(ctype)
            if pythonClass is not None:
                return pythonClass
            else:
                raise ApiException("Cannot map STELLA object " + str(obj) + " of type " + str(ctype) + " onto Python type")
    else:
        # we already have a Pyton object, e.g., an int:
        return type(obj)

def stellaToPythonObject(obj):
    """Map a STELLA ffi.cdata object `obj' onto its corresponding Python representation.
       This determines the required target type dynamically using 'stellaObjectToPythonType'."""
    if obj == _ffi.NULL:
        return None
    else:
        cls = stellaObjectToPythonType(obj)
        if cls == str:
            return ffi_to_string(obj)
        elif cls in (int, float, long, _ffi.CData):
            return obj
        elif cls == bool:
            return not obj == 0
        else:
            return cls(_stobj=obj)

def stellaToPythonObjectOfType(obj, cls):
    """Map a STELLA ffi.cdata object `obj' onto a Python representation of type `cls'.
       This is more efficient for cases where we are certain of the required target type."""
    if obj == _ffi.NULL:
        return None
    else:
        if cls == str:
            return ffi_to_string(obj)
        elif cls in (int, float, long, _ffi.CData):
            return obj
        elif cls == bool:
            return not obj == 0
        else:
            return cls(_stobj=obj)


### Python to STELLA object conversion

def pythonStringToStellaString(string):
    "Return a GC-protected STELLA-string copy of the Python string `string'."
    if string is None:
        return _ffi.NULL
    else:
        value = boot.stringCopy(to_bytes(string))
        gcProtectObject(value)
        return value

def pythonToStellaObject(obj, _enc=com.DEFAULT_ENCODING):
    """Map a Python object 'obj' onto its corresponding STELLA ffi.cdata representation
       so it can be passed to a STELLA function."""
    if obj is None:
        # ISSUE: this assumes the (unknown) target type has the generic NULL value:
        return _ffi.NULL
    # in PY3 the `str' test will always dominate the `unicode' test in the next clause:
    elif isinstance(obj, str) or isinstance(obj, bytes):
        # we need to allocate strings on the STELLA side to avoid premature reclamation.
        # NOTE: we do rely on gc-protect/release here in case multiple string arguments
        # need to be allocated before they are passed to a function:
        return pythonStringToStellaString(obj)
    elif PY2 and isinstance(obj, unicode):
        obj = obj.encode(_enc)
        return pythonStringToStellaString(obj)
    elif isinstance(obj, list) or isinstance(obj, tuple):
        obj = pythonToStellaTree(obj)
    # int/float/bool is handled automatically, no conversion needed:
    if isinstance(obj, ProxyClass):
        obj = obj._stellaObject
    if obj is None:
        return _ffi.NULL
    else:
        return obj

def pythonToStellaObjectOfType(obj, cls, _enc=com.DEFAULT_ENCODING):
    """Map a Python object 'obj' onto its corresponding STELLA ffi.cdata representation
       so it can be passed to a STELLA function.  Additionally checks that `obj' is in
       fact or can be converted to an object of type `cls'."""
    if obj is None:
        # TO DO: this doesn't do the right thing if `cls' is a type with special NULL value:
        return _ffi.NULL
    # in PY3 the `str' test will always dominate the `unicode' test in the next clause:
    if (isinstance(obj, str) or isinstance(obj, bytes)) and cls == str:
        # need to allocate strings on STELLA side (see above):
        return pythonStringToStellaString(obj)
    elif PY2 and isinstance(obj, unicode) and cls == str:
        obj = obj.encode(_enc)
        return pythonStringToStellaString(obj)
    if isinstance(obj, list) or isinstance(obj, tuple):
        obj = pythonToStellaTree(obj)
    if isinstance(obj, cls):
        # int/float/bool is handled automatically, no conversion needed:
        if isinstance(obj, ProxyClass):
            obj = obj._stellaObject
        if obj is None:
            return _ffi.NULL
        else:
            return obj
    else:
        raise ApiException("Object " + str(obj) + " is not of type " + str(cls))

def pythonToStellaTree(tree, _enc=com.DEFAULT_ENCODING):
    """Convert the Python `tree' into an equivalent STELLA Cons tree.
    Literals such as numbers and strings will automatically be wrapped.
    """
    if isinstance(tree, list) or isinstance(tree, tuple):
        # create a GC-protected cons list of the proper size::
        consTree = stella.pdef.makeConsList(len(tree))
        stree = consTree._stellaObject
        setfn = stella.cdef.consSetFirstGetNext
        for elt in tree:
            # now set values at STELLA level to avoid extraneous wrapping and checking -
            # BUT: this is very tricky!  We have to make sure that all 'elt's and cons-cells
            # are and stay GC-protected before any potential GC-triggering STELLA calls:
            elt = pythonToStellaTree(elt)
            selt = elt._stellaObject if elt is not None else _ffi.NULL
            stree = setfn(stree, selt)
        return consTree
    elif isinstance(tree, stella.pdef.Object):
        return tree
    # in PY3 the `str' test will always dominate the `unicode' test in the next clause:
    elif isinstance(tree, str):
        return stella.pdef.wrapString(tree)
    elif PY2 and isinstance(tree, unicode):
        tree = tree.encode(_enc)
        return stella.pdef.wrapString(tree)
    # need to test before int, since True/False are also int's:
    elif isinstance(tree, bool):
        return stella.pdef.wrapBoolean(tree)
    elif isinstance(tree, int):
        if PY3:
            return stella.pdef.wrapIntegerValue(tree)
        else:
            return stella.pdef.wrapInteger(tree)
    elif isinstance(tree, float):
        return stella.pdef.wrapFloat(tree)
    elif isinstance(tree, long):
        return stella.pdef.wrapLongInteger(tree)
    elif tree is None:
        return tree
    else:
        raise ApiException("Don't know how to convert " + str(tree) + " into a STELLA Cons-tree element")

# inverse to pythonify:
stellafy = pythonToStellaTree


### Type wrapping and unwrapping

# TO DO: possibly also capture/use low-level boot unwrappers

def lookupTypeWrapper(basetypeSpec):
    wrapper = lookupTypeInfoFacet(basetypeSpec, 'wrapFunction')
    if wrapper is not None:
        return getattr(getStellaModulePDefNamespace('/STELLA'), wrapper)
    else:
        return None

def lookupTypeUnwrapper(basetypeSpec):
    unwrapper = lookupTypeInfoFacet(basetypeSpec, 'unwrapFunction')
    if unwrapper is not None:
        return getattr(getStellaModulePDefNamespace('/STELLA'), unwrapper)
    else:
        return None

def lookupCDefTypeWrapper(basetypeSpec):
    wrapper = lookupTypeInfoFacet(basetypeSpec, 'wrapFunction')
    if wrapper is not None:
        return getattr(getStellaModuleCDefNamespace('/STELLA'), wrapper)
    else:
        return None

def lookupCDefTypeUnwrapper(basetypeSpec):
    unwrapper = lookupTypeInfoFacet(basetypeSpec, 'unwrapFunction')
    if unwrapper is not None:
        return getattr(getStellaModuleCDefNamespace('/STELLA'), unwrapper)
    else:
        return None
