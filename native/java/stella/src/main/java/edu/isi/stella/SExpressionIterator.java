//  -*- Mode: Java -*-
//
// SExpressionIterator.java

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

/** Iterator that yields s-expressions from an input stream.
 * @author Stella Java Translator
 */
public class SExpressionIterator extends StreamIterator {
    /** The current value of this iterator
     */
    public Stella_Object value;

  public static SExpressionIterator newSExpressionIterator() {
    { SExpressionIterator self = null;

      self = new SExpressionIterator();
      self.firstIterationP = true;
      self.value = null;
      self.theStream = null;
      return (self);
    }
  }

  public boolean nextP() {
    { SExpressionIterator self = this;

      self.firstIterationP = false;
      { Stella_Object renamed_Object = null;
        boolean eofP = false;

        { Object [] caller_MV_returnarray = new Object[1];

          renamed_Object = InputStream.readSExpression(self.theStream, caller_MV_returnarray);
          eofP = ((boolean)(((BooleanWrapper)(caller_MV_returnarray[0])).wrapperValue));
        }
        if (eofP) {
          Stream.closeStream(self.theStream);
          return (false);
        }
        else {
          self.value = renamed_Object;
          return (true);
        }
      }
    }
  }

  public static Stella_Object accessSExpressionIteratorSlotValue(SExpressionIterator self, Symbol slotname, Stella_Object value, boolean setvalueP) {
    if (slotname == Stella.SYM_STELLA_VALUE) {
      if (setvalueP) {
        self.value = value;
      }
      else {
        value = self.value;
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
    { SExpressionIterator self = this;

      return (Stella.SGT_STELLA_S_EXPRESSION_ITERATOR);
    }
  }

  public void free() {
    { SExpressionIterator self = this;

      if (StreamIterator.terminateStreamIteratorP(self)) {
        Stella_Object.unmake(self);
      }
    }
  }

}

