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
Garbage collection protection and related support.
"""

from __future__ import print_function, division, absolute_import

import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] >= 3
if PY3:
    unicode = str
    long = int

import weakref

import stellapi.common as com
from   stellapi.common import FFI as _ffi
from   stellapi.namespaces import boot, stella
from   stellapi.bootstrap import _stellalib


### Protecting STELLA objects pointed to by Python from premature STELLA-side garbage collection

# The basic problem is that the C++ garbage collector collects objects as soon as there are no more
# global or local variable references to them.  In C/C++, we can assign objects to variables, thus,
# protecting them from being GC-ed is easy.  In Python we don't have that option, since Python variable
# references to C++ objects are not seen by the collector, since they used a different malloc.  We
# can protect such objects by wrapping them in uncollectable wrappers (special memory understood by the
# STELLA GC to not be collected), however, then the additional complication is that these wrappers and
# their protection should be released when Python objects pointing to STELLA objects get GC-ed by Python.
#
# Our approach to address this is the following:
# - Each C-callable API function saves its result in a single value global variable buffer before returning.
#   This guarantees that the return value will stay alive at least until the next API function call is made.
#   Assignment to a global buffer variable is handled by the STELLA translator now during wrapper generation.
#   In a multi-threading environment, locking might be required to assure GC-protection.
# - we now have STELLA-level support via `stella_gcProtectObject' to protect a return value from garbage
#   collection until it is released by a call to `stella_gcReleaseObject'.  Protection is handled by creating
#   uncollectable wrappers via GC_MALLOC_UNCOLLECTABLE that point to the protected object.
# - On the Python side, we want to be able to release an object from GC protection and free its wrapper as
#   soon as the last Python reference to it is eliminated.  To do that, we use Python's weak references,
#   since those allow us to register a finalizer/destructor that is called when the weakly referenced object
#   is garbage collected.  See `gcProtectObject' below for details.
# - this is somewhat tricky and complicated and might have some peformance implications, but it is safe

_gcObjectRegistry = {}

def gcProtectObject(obj):
    if obj != _ffi.NULL:
        # create a GC-protection wrapper via STELLA's `gcProtectObject' which will
        # prevent `obj' from being C++-garbage collected until `spi_gcReleaseObject' is called:
        wrapper = boot.gcProtectObject(obj)
        #print 'gcProtectObject', 'wrapper=', wrapper, 'obj=', obj
        # next we create a weak reference to `obj' whose primary purpose is that it
        # allows us to register a destructor to be called when `obj' gets GC-ed by Python:
        weakRef = weakref.ref(obj, gcReleaseObject)
        # now we have to store the weak reference in a global table to prevent it from being
        # GC-ed by Python before the protected `obj' is GC-ed;  additionally, we need to store
        # the associated protective wrapper, so we can free it when the registered destructor
        # is called; we cannot attach the wrapper to the protected object in any way, since
        # that object is not available anymore when the destructor is called, thus we store it
        # with the weak reference in the global object registry; another minor wrinkle is that
        # weak refs aren't hashable, so we hash on their object ID - phew:
        _gcObjectRegistry[id(weakRef)] = (weakRef, wrapper)
    return obj

def gcReleaseObject(weakRef):
    # Destructor called when the object pointed to by `weakRef' gets GC-ed by Python.
    # First we lookup and remove the object's protection wrapper from the object registry:
    (weakRef, wrapper) = _gcObjectRegistry.pop(id(weakRef))
    #print 'gcReleaseObject', 'wrapper=', wrapper
    # Then we release the C++ object from C++ GC-protection - we have to use a low-level call
    # here, since during exit the `boot' object gets GC-ed away which loses the function pointer:
    #boot.gcReleaseObject(wrapper)
    _stellalib.stella_gcReleaseObject(wrapper)

# Not used + has forward refs to types:
# def withGcProtection(obj):
#     # Wrapper to add GC-protection around a PLI call (just for illustration).
#     if isinstance(obj, _cdataType) and _ffi._backend.typeof(obj) in _pointerTypes:
#         gcProtectObject(obj)
#     return obj


### Storing Python object references inside STELLA objects

# We also want to support to have STELLA objects "point" to Python objects, for example, to
# interface the PowerLoom neural net inference module with TensorFlow.  While it's probably
# possible to stick a PyObject* pointer into a STELLA object somewhere, that requires some low-level
# interfacing we don't want to get into right now.  Instead, we store the `id' of a Python object
# on the STELLA side and then have the `id' point to the Python object within `_gcObjectRegistry'.
# The only wrinkle in this scheme is that we want to eliminate the link in `_gcObjectRegistry' once
# the enclosing STELLA object gets GC-ed (the converse of what we do above).  This can be handled
# by registering a finalizer via `GC_register_finalizer' which then has to point to a callback.
# Even if we manage to work with the `PyObject*' pointer directly, we would still have to stick
# the object into some Python data structure to prevent its premature garbage collection, and then
# would have to remove it from there with a finalizer.

# So the protocol goes like this:
# - call `getPythonObjectStellaPointer' on some Python object to create a pointer object that can
#   be assigned to some STELLA slot or variable of type LONG-INTEGER-WRAPPER (or its supers).
# - assign that pointer to some STELLA object slot or variable to prevent its garbage collection
# - AFTER that, call `getPythonObjectFromStellaPointer' or `unregisterPythonObjectStellaPointer'
#   on the pointer at least once to allow STELLA-side garbage collection once all references to
#   the pointer have been eliminated (at that point it will be automatically freed on the Python side)
# - use `getPythonObjectFromStellaPointer' to access the Python object associated with the pointer

def getPythonObjectStellaPointer(pyobj, fullEntry=False, trace=False):
    """Create a STELLA pointer object that can be used to access the Python object `pyobj'.
    For now, these pointers are of type LONG-INTEGER-WRAPPER which point to `pyobj's id.
    If the object has already been associated with a pointer earlier, simply return that one.
    After the pointer has been created, it needs to be assigned to a STELLA variable or slot
    to prevent its garbage collection.  Once that is done, the first call to the function
    `getPythonObjectFromStellaPointer' will unprotect it so that it can be GC-ed in STELLA
    once all references to it there have been eliminated.  If `fullEntry' we return the whole
    entry instead of just the pointer, which allows us to store a different payload than the
    `pyobj' that created the reference.  This is useful for some obscure numpy/word2vec cases.
    If `trace', print a message when the pointer gets GC-ed on the STELLA side.
    """
    pyobjId = id(pyobj)
    pyobjPointer = _gcObjectRegistry.get(pyobjId)
    if pyobjPointer is None:
        # we use a STELLA LongIntegerWrapper to store the `id' of the Python object:
        pyobjPointer = boot.wrapLongInteger(pyobjId)
        # TRICKY: until the LongIntegerWrapper is assigned to some STELLA variable or slot,
        # we have to protect it from premature garbage collection:
        gcWrapper = boot.gcProtectObject(pyobjPointer)
        # register a STELLA GC finalizer on the LongIntegerWrapper, so if it gets GC-ed in STELLA it will be unregistered here
        # - note that garbage collection there cannot happen until we explicitly call gcReleaseObject on the GC wrapper:
        boot.gcRegisterFinalizerIgnoreSelf(pyobjPointer, _pythonObjectStellaPointerFinalizer, stella.cdef.NULL, stella.cdef.NULL, stella.cdef.NULL)
        # create the Python wrapper for the pointer object right here, since that's what we'll usually use;
        # we store all relevant info as a list so we can release the GC protection wrapper later:
        pyobjPointer = [pyobj, stella.pdef.LongIntegerWrapper(_stobj=pyobjPointer), gcWrapper, trace]
        _gcObjectRegistry[pyobjId] = pyobjPointer
    if fullEntry:
        return pyobjPointer
    else:
        return pyobjPointer[1]

@_ffi.callback("void(void*, void*)")
def _pythonObjectStellaPointerFinalizer(pyobjPointer, clientData):
    """STELLA GC finalizer called to unregister `pyobjPointer' from the registry, `clientData' is ignored.
    `pyobjPointer' is a native STELLA object, after this call it will be invalid.
    """
    # if this gets called, we know that the GC protection for the wrapper must have been removed already:
    pyobjId = boot.unwrapLongInteger(pyobjPointer)
    # tested, seems to work:
    entry = _gcObjectRegistry.pop(pyobjId)
    if entry[3] == True:
        sys.stderr.write(">>> Python object pointer GC-ed by STELLA: %s %s\n" % (entry[0], pyobjPointer))

def unregisterPythonObjectStellaPointer(pyobjPointer):
    """Explicitly unregister `pyobjPointer' from the registry, after this call it will be invalid."""
    if isinstance(pyobjPointer, stella.pdef.LongIntegerWrapper):
        pyobjPointer = pyobjPointer._stellaObject
    pyobjId = boot.unwrapLongInteger(pyobjPointer)
    entry = _gcObjectRegistry[pyobjId]
    if entry[2] is not None:
        # we were called explicitly, remove the GC protection wrapper so it can be GC'ed on the STELLA side also:
        boot.gcReleaseObject(entry[2])
        entry[2] = None
    _gcObjectRegistry.pop(pyobjId)

def getPythonObjectFromStellaPointer(pyobjPointer):
    """Return the Python object associated with `pyobjPointer'.  As a side effect, remove STELLA GC protection
    to allow garbage collection there once all STELLA references to the pointer have been eliminated.
    """
    # TO DO: should we make this a method on LongIntegerWrapper?
    if isinstance(pyobjPointer, stella.pdef.LongIntegerWrapper):
        pyobjPointer = pyobjPointer._stellaObject
    pyobjId = boot.unwrapLongInteger(pyobjPointer)
    entry = _gcObjectRegistry[pyobjId]
    if entry[2] is not None:
        # remove the GC protection wrapper from `pyobjPointer', which means if at this point the pointer
        # is not assigned to some STELLA variable or slot, it will eventually be garbage collected there:
        boot.gcReleaseObject(entry[2])
        entry[2] = None
    return entry[0]

def getPythonObjectFromStellaPointerId(pyobjId):
    """Variant of `getPythonObjectFromStellaPointer' that works directly on the unwrapped object ID.
    """
    entry = _gcObjectRegistry[pyobjId]
    if entry[2] is not None:
        # remove the GC protection wrapper from `pyobjPointer', which means if at this point the pointer
        # is not assigned to some STELLA variable or slot, it will eventually be garbage collected there:
        boot.gcReleaseObject(entry[2])
        entry[2] = None
    return entry[0]

"""
# Here's an alternative way to map an `id' onto the Python object via ctypes, however, dict lookup is faster:
# see https://stackoverflow.com/questions/1396668/get-object-by-id
>>> import ctypes
>>> id(spi.stella.pdef.Object)
94383746383680
>>> ctypes.cast(94383746383680, ctypes.py_object).value
<class 'Object'>
>>> _ is spi.stella.pdef.Object
True
"""
