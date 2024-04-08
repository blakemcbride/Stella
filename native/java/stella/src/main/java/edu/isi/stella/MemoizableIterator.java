//  -*- Mode: Java -*-
//
// MemoizableIterator.java

/*
+---------------------------- BEGIN LICENSE BLOCK ---------------------------+
|                                                                            |
| Version: MPL 1.1/GPL 2.0/LGPL 2.1                                          |
|                                                                            |
| The contents of this file are subject to the Mozilla Public License        |
| Version 1.1 (the "License"); you may not use this file except in           |
| compliance with the License. You may obtain a copy of the License at       |
| http://www.mozilla.org/MPL/                                                |
|                                                                            |
| Software distributed under the License is distributed on an "AS IS" basis, |
| WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License   |
| for the specific language governing rights and limitations under the       |
| License.                                                                   |
|                                                                            |
| The Original Code is the STELLA Programming Language.                      |
|                                                                            |
| The Initial Developer of the Original Code is                              |
| UNIVERSITY OF SOUTHERN CALIFORNIA, INFORMATION SCIENCES INSTITUTE          |
| 4676 Admiralty Way, Marina Del Rey, California 90292, U.S.A.               |
|                                                                            |
| Portions created by the Initial Developer are Copyright (C) 1996-2023      |
| the Initial Developer. All Rights Reserved.                                |
|                                                                            |
| Contributor(s):                                                            |
|                                                                            |
| Alternatively, the contents of this file may be used under the terms of    |
| either the GNU General Public License Version 2 or later (the "GPL"), or   |
| the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),   |
| in which case the provisions of the GPL or the LGPL are applicable instead |
| of those above. If you wish to allow use of your version of this file only |
| under the terms of either the GPL or the LGPL, and not to allow others to  |
| use your version of this file under the terms of the MPL, indicate your    |
| decision by deleting the provisions above and replace them with the notice |
| and other provisions required by the GPL or the LGPL. If you do not delete |
| the provisions above, a recipient may use your version of this file under  |
| the terms of any one of the MPL, the GPL or the LGPL.                      |
|                                                                            |
+---------------------------- END LICENSE BLOCK -----------------------------+
*/

package edu.isi.stella;

import edu.isi.stella.javalib.*;

/** Iterator class with value buffering that can be used to memoize some
 * <code>baseIterator</code> without having to generate all its values first.  The
 * memoized iterator needs to be cloned to allow multiple iterations over
 * the collection represented by the memoized iterator.  Use the following
 * idiom to memoize some arbitrary iterator and return a properly cloned value:
 * 	 
 *  (clone-memoized-iterator
 *    (memoize (...) &lt;options&gt;*
 *             (new MEMOIZABLE-ITERATOR
 *                  :base-iterator &lt;base-iterator&gt;)))
 * 	
 * This will ensure that &lt;base-iterator&gt; is exhausted exactly once even if
 * there are multiple clones for the same memoized value, and that each value
 * is generated as late as absolutely possible.  THIS IS NOT YET THREAD SAFE!
 * @author Stella Java Translator
 */
public class MemoizableIterator extends Iterator {
    /** This slot is only needed to pass the base iterator
     * to the constructor.  Once <code>self</code> is initialized it will be cleared.
     */
    public Iterator baseIterator;
    /** Holds the base iterator and the values generated
     * so far.  This slot is structure shared between the memoized iterator and
     * all its clones to make sure everybody sees any new values generated by
     * any one of the clones, and that everybody can see when the base iterator
     * is exhausted.
     */
    public Cons iteratorAndValues;
    /** Trailing cursor to the list of values generated
     * so far.  Once the end of the list is reached this slot is used to add new
     * values to the end of <code>iteratorAndValues</code>.
     */
    public Cons cursor;

  public static MemoizableIterator newMemoizableIterator(Iterator baseIterator) {
    { MemoizableIterator self = null;

      self = new MemoizableIterator();
      self.baseIterator = baseIterator;
      self.firstIterationP = true;
      self.value = null;
      self.cursor = null;
      self.iteratorAndValues = null;
      self.initializeMemoizableIterator();
      return (self);
    }
  }

  /** Generate the next value of the memoized iterator <code>self</code> (or
   * one of its clones) by either using one of the values generated so far or by
   * generating and saving the next value of the <code>baseIterator</code>.
   * @return boolean
   */
  public boolean nextP() {
    { MemoizableIterator self = this;

      { Iterator iterator = null;
        Cons cursor = self.cursor;
        Cons values = cursor.rest;

        if (!(values == Stella.NIL)) {
          self.value = values.value;
          self.cursor = values;
          return (true);
        }
        iterator = ((Iterator)(self.iteratorAndValues.value));
        if (iterator != null) {
          if (iterator.nextP()) {
            self.value = iterator.value;
            cursor.rest = Cons.cons(self.value, Stella.NIL);
            self.cursor = cursor.rest;
            return (true);
          }
          self.iteratorAndValues.firstSetter(null);
        }
        return (false);
      }
    }
  }

  /** Alias for <code>cloneMemoizedIterator</code>.
   * @return AbstractIterator
   */
  public AbstractIterator allocateIterator() {
    { MemoizableIterator self = this;

      return (MemoizableIterator.cloneMemoizedIterator(self));
    }
  }

  /** Clone the memoized iterator <code>self</code> so it can be used to
   * iterate over the collection represented by <code>self</code>, while allowing to iterate
   * over it multiple times via multiple clones.
   * @param self
   * @return Iterator
   */
  public static Iterator cloneMemoizedIterator(MemoizableIterator self) {
    { Cons iterandvalues = self.iteratorAndValues;

      if (iterandvalues.value != null) {
        { MemoizableIterator child = new MemoizableIterator();

          child.firstIterationP = true;
          child.iteratorAndValues = iterandvalues;
          child.cursor = iterandvalues;
          return (child);
        }
      }
      else {
        return (iterandvalues.rest.allocateIterator());
      }
    }
  }

  public void initializeMemoizableIterator() {
    { MemoizableIterator self = this;

      { Cons iterandvalues = Cons.cons(self.baseIterator, Stella.NIL);

        self.iteratorAndValues = iterandvalues;
        self.cursor = iterandvalues;
        self.baseIterator = null;
      }
    }
  }

  public static Stella_Object accessMemoizableIteratorSlotValue(MemoizableIterator self, Symbol slotname, Stella_Object value, boolean setvalueP) {
    if (slotname == Stella.SYM_STELLA_BASE_ITERATOR) {
      if (setvalueP) {
        self.baseIterator = ((Iterator)(value));
      }
      else {
        value = self.baseIterator;
      }
    }
    else if (slotname == Stella.SYM_STELLA_ITERATOR_AND_VALUES) {
      if (setvalueP) {
        self.iteratorAndValues = ((Cons)(value));
      }
      else {
        value = self.iteratorAndValues;
      }
    }
    else if (slotname == Stella.SYM_STELLA_CURSOR) {
      if (setvalueP) {
        self.cursor = ((Cons)(value));
      }
      else {
        value = self.cursor;
      }
    }
    else {
      { OutputStringStream stream000 = OutputStringStream.newOutputStringStream();

        stream000.nativeStream.print("`" + slotname + "' is not a valid case option");
        throw ((StellaException)(StellaException.newStellaException(stream000.theStringReader()).fillInStackTrace()));
      }
    }
    return (value);
  }

  public Surrogate primaryType() {
    { MemoizableIterator self = this;

      return (Stella.SGT_STELLA_MEMOIZABLE_ITERATOR);
    }
  }

}

