;;; -*- Mode: Lisp; Package: STELLA; Syntax: COMMON-LISP; Base: 10 -*-

;;; cpp-class-out.lisp

#|
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
|#

(CL:IN-PACKAGE "STELLA")

;;; Auxiliary variables:

(CL:DEFVAR SGT-CPP-CLASS-OUT-STELLA-OBJECT NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-DOCUMENTATION NULL)
(CL:DEFVAR KWD-CPP-CLASS-OUT-EMBEDDED NULL)
(CL:DEFVAR KWD-CPP-CLASS-OUT-INSTANCE NULL)
(CL:DEFVAR KWD-CPP-CLASS-OUT-CLASS NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-NULL NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_FUNCTION NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_FUNCTION_CALL NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_IDENT NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_ACTUALS NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-SLOT-TYPE-SPECIFIER NULL)
(CL:DEFVAR SGT-CPP-CLASS-OUT-STELLA-ANCHORED-TYPE-SPECIFIER NULL)
(CL:DEFVAR SGT-CPP-CLASS-OUT-STELLA-UNKNOWN NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-DEFINED? NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-NULL? NULL)
(CL:DEFVAR SGT-CPP-CLASS-OUT-STELLA-METHOD-SLOT NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CLASS-CPP-NATIVE-TYPE NULL)
(CL:DEFVAR KWD-CPP-CLASS-OUT-CPP NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-GC NULL)
(CL:DEFVAR KWD-CPP-CLASS-OUT-CPP-STANDALONE NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_CLASS NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_COMMENT NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_DECLARATIONS NULL)
(CL:DEFVAR KWD-CPP-CLASS-OUT-PUBLIC NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_SIGNATURES NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-CPP_DEFINITIONS NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-STARTUP-CPP-CLASS-OUT NULL)
(CL:DEFVAR SYM-CPP-CLASS-OUT-STELLA-METHOD-STARTUP-CLASSNAME NULL)

;;; Forward declarations:

(CL:DECLAIM
 (CL:SPECIAL *STELLA-MODULE* *MODULE* *TRANSLATOROUTPUTLANGUAGE*
  *METHODBEINGWALKED* NIL NULL-STRING-WRAPPER))

;;; (DEFUN (CPP-YIELD-INITIAL-NULL-VALUE CONS) ...)

(CL:DEFUN CPP-YIELD-INITIAL-NULL-VALUE ()
  (CL:RETURN-FROM CPP-YIELD-INITIAL-NULL-VALUE
   (CPP-TRANSLATE-A-TREE NULL)))

;;; (DEFUN (CPP-YIELD-MEMBER-VAR-TREE CONS) ...)

(CL:DEFUN CPP-YIELD-MEMBER-VAR-TREE (SLOT CLASS)
  (CL:LET*
   ((SLOTNAME (TRUE-SLOT-NAME (%SLOT-NAME SLOT) (%CLASS-TYPE CLASS)))
    (SLOTTYPE
     (CL:IF (%SLOT-CONTEXT-SENSITIVE? SLOT)
      SGT-CPP-CLASS-OUT-STELLA-OBJECT
      (COMPUTE-RETURN-TYPE-SPEC SLOT (%CLASS-TYPE CLASS))))
    (ALLOCATION (ALLOCATION SLOT)) (ALLOCATIONFORM NIL)
    (DOCUMENTATION
     (%WRAPPER-VALUE
      (DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS SLOT)
       SYM-CPP-CLASS-OUT-STELLA-DOCUMENTATION NULL-STRING-WRAPPER)))
    (DOCUMENTATIONFORM NIL))
   (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING DOCUMENTATION))
   (CL:COND
    ((CL:EQ ALLOCATION KWD-CPP-CLASS-OUT-EMBEDDED)
     (CL:SETQ ALLOCATIONFORM NIL))
    ((CL:EQ ALLOCATION KWD-CPP-CLASS-OUT-INSTANCE)
     (CL:SETQ ALLOCATIONFORM NIL))
    ((CL:EQ ALLOCATION KWD-CPP-CLASS-OUT-CLASS)
     (CL:SETQ ALLOCATIONFORM (CONS-LIST (WRAP-STRING "static"))))
    (CL:T (CL:SETQ ALLOCATIONFORM NIL)))
   (CL:WHEN (CL:NOT (CL:EQ DOCUMENTATION STELLA::NULL-STRING))
    (CL:SETQ DOCUMENTATIONFORM (CONS (WRAP-STRING DOCUMENTATION) NIL)))
   (CL:RETURN-FROM CPP-YIELD-MEMBER-VAR-TREE
    (LIST*
     (CONCATENATE ALLOCATIONFORM
      (CONS (CPP-TRANSLATE-AND-POINTERIZE-TYPE-SPEC SLOTTYPE) NIL))
     (CPP-TRANSLATE-NAME SLOTNAME)
     (CONCATENATE DOCUMENTATIONFORM NIL)))))

;;; (DEFUN (CPP-YIELD-PARAMETERIZED-MEMBER-VAR-TREE CONS) ...)

(CL:DEFUN CPP-YIELD-PARAMETERIZED-MEMBER-VAR-TREE (SLOT CLASS)
  (CL:LET*
   ((SLOTNAME (TRUE-SLOT-NAME (%SLOT-NAME SLOT) (%CLASS-TYPE CLASS)))
    (ALLOCATION (ALLOCATION SLOT)) (ALLOCATIONFORM NIL))
   (CL:COND
    ((CL:EQ ALLOCATION KWD-CPP-CLASS-OUT-EMBEDDED)
     (CL:SETQ ALLOCATIONFORM NIL))
    ((CL:EQ ALLOCATION KWD-CPP-CLASS-OUT-INSTANCE)
     (CL:SETQ ALLOCATIONFORM NIL))
    ((CL:EQ ALLOCATION KWD-CPP-CLASS-OUT-CLASS)
     (CL:SETQ ALLOCATIONFORM (CONS-LIST (WRAP-STRING "static"))))
    (CL:T (CL:SETQ ALLOCATIONFORM NIL)))
   (CL:RETURN-FROM CPP-YIELD-PARAMETERIZED-MEMBER-VAR-TREE
    (LIST*
     (CONCATENATE ALLOCATIONFORM
      (CONS
       (CPP-TRANSLATE-CLASS-PARAMETER-NAME
        (GET-SLOT-CLASS-PARAMETER-NAME SLOT))
       NIL))
     (CPP-TRANSLATE-NAME SLOTNAME)
     (CONS SYM-CPP-CLASS-OUT-STELLA-NULL NIL)))))

;;; (DEFUN (CPP-YIELD-STATIC-MEMBER-ALLOCATION-TREE CONS) ...)

(CL:DEFUN CPP-YIELD-STATIC-MEMBER-ALLOCATION-TREE (SLOT CLASS)
  (CL:LET*
   ((SLOTNAME (%SLOT-NAME SLOT)) (ALLOCATIONFORM NIL)
    (MOSTGENERALSLOT NULL))
   (CL:SETQ MOSTGENERALSLOT SLOT)
   (CL:LOOP
    (CL:IF
     (CL:NOT (CL:EQ (%SLOT-DIRECT-EQUIVALENT MOSTGENERALSLOT) NULL))
     (CL:SETQ MOSTGENERALSLOT
      (%SLOT-DIRECT-EQUIVALENT MOSTGENERALSLOT))
     (CL:RETURN)))
   (CL:RETURN-FROM CPP-YIELD-STATIC-MEMBER-ALLOCATION-TREE
    (LIST*
     (CONCATENATE ALLOCATIONFORM
      (CONS
       (CPP-TRANSLATE-AND-POINTERIZE-TYPE-SPEC
        (COMPUTE-RETURN-TYPE-SPEC MOSTGENERALSLOT (%CLASS-TYPE CLASS)))
       NIL))
     (CPP-TRANSLATE-NAME SLOTNAME)
     (CONS SYM-CPP-CLASS-OUT-STELLA-NULL NIL)))))

;;; (DEFUN (CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE CONS) ...)

(CL:DEFUN CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE (METHOD)
  (CL:SETQ *METHODBEINGWALKED* METHOD)
  (CL:RETURN-FROM CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE
   (CONS
    (CL:IF (%METHOD-FUNCTION? METHOD) NULL
     (CPP-TRANSLATE-CLASS-NAME
      (INTERN-SYMBOL-IN-MODULE (%SYMBOL-NAME (%SLOT-OWNER METHOD))
       (%HOME-CONTEXT (%SLOT-OWNER METHOD)) CL:NIL)))
    (LIST*
     (CONS (WRAP-STRING "virtual")
      (CONS
       (CPP-TRANSLATE-AND-POINTERIZE-TYPE-SPEC
        (COMPUTE-MOST-GENERAL-RETURN-TYPE METHOD
         (COMPUTE-RETURN-TYPE-SPEC METHOD (%SLOT-OWNER METHOD))))
       NIL))
     (CPP-TRANSLATE-FUNCTION-NAME METHOD CL:NIL)
     (CONS (CPP-TRANSLATE-FUNCTION-PARAMETERS METHOD) NIL)))))

;;; (DEFUN (CPP-YIELD-CONSTRUCTOR-SIGNATURE-TREE CONS) ...)

(CL:DEFUN CPP-YIELD-CONSTRUCTOR-SIGNATURE-TREE (METHOD)
  (CL:SETQ *METHODBEINGWALKED* METHOD)
  (CL:RETURN-FROM CPP-YIELD-CONSTRUCTOR-SIGNATURE-TREE
   (CONS
    (CPP-TRANSLATE-CLASS-NAME
     (INTERN-SYMBOL-IN-MODULE (%SYMBOL-NAME (%SLOT-OWNER METHOD))
      (%HOME-CONTEXT (%SLOT-OWNER METHOD)) CL:NIL))
    (LIST* NIL (CPP-TRANSLATE-CONSTRUCTOR-NAME METHOD)
     (CONS (CPP-TRANSLATE-FUNCTION-PARAMETERS METHOD) NIL)))))

;;; (DEFUN (CPP-YIELD-EXCEPTION-CONSTRUCTOR-DEFINITION CONS) ...)

(CL:DEFUN CPP-YIELD-EXCEPTION-CONSTRUCTOR-DEFINITION (CLASS)
  (CL:LET* ((VALUE-000 NULL))
   (CL:LET*
    ((SUPER NULL)
     (ITER-000 (%THE-CONS-LIST (CLASS-NATIVE-SUPERS CLASS))))
    (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-000 NIL)) DO
     (CL:SETQ SUPER (%%VALUE ITER-000))
     (CL:WHEN (CL:NOT (%MIXIN? (%SURROGATE-VALUE SUPER)))
      (CL:SETQ VALUE-000 SUPER) (CL:RETURN))
     (CL:SETQ ITER-000 (%%REST ITER-000))))
   (CL:LET* ((SUPER VALUE-000))
    (CL:RETURN-FROM CPP-YIELD-EXCEPTION-CONSTRUCTOR-DEFINITION
     (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_FUNCTION NIL
      (CPP-TRANSLATE-CLASS-NAME (%CLASS-TYPE CLASS))
      (LIST*
       (CONS
        (LIST* (WRAP-STRING "const std::string&") (WRAP-STRING "msg")
         NIL)
        NIL)
       NIL
       (CONS
        (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_FUNCTION_CALL
         (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_IDENT
          (CPP-TRANSLATE-CLASS-NAME SUPER) NIL)
         (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_ACTUALS
          (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_IDENT (WRAP-STRING "msg")
           NIL)
          NIL)
         NIL)
        NIL)
       NIL))))))

;;; (DEFUN (SLOT-HAS-CLASS-PARAMETER-TYPE? BOOLEAN) ...)

(CL:DEFUN SLOT-HAS-CLASS-PARAMETER-TYPE? (SLOT CLASS)
  (CL:RETURN-FROM SLOT-HAS-CLASS-PARAMETER-TYPE?
   (CL:AND
    (CL:NOT
     (CL:EQ
      (DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS SLOT)
       SYM-CPP-CLASS-OUT-STELLA-SLOT-TYPE-SPECIFIER NULL)
      NULL))
    (ISA?
     (DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS SLOT)
      SYM-CPP-CLASS-OUT-STELLA-SLOT-TYPE-SPECIFIER NULL)
     SGT-CPP-CLASS-OUT-STELLA-ANCHORED-TYPE-SPECIFIER)
    (CL:EQ (COMPUTE-RETURN-TYPE-SPEC SLOT (%CLASS-TYPE CLASS))
     SGT-CPP-CLASS-OUT-STELLA-UNKNOWN))))

;;; (DEFUN (GET-SLOT-CLASS-PARAMETER-NAME SYMBOL) ...)

(CL:DEFUN GET-SLOT-CLASS-PARAMETER-NAME (SLOT)
  (CL:RETURN-FROM GET-SLOT-CLASS-PARAMETER-NAME
   (%SPECIFIER-PARAMETER-NAME
    (DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS SLOT)
     SYM-CPP-CLASS-OUT-STELLA-SLOT-TYPE-SPECIFIER NULL))))

;;; (DEFUN (CPP-NATIVE-METHOD? BOOLEAN) ...)

(CL:DEFUN CPP-NATIVE-METHOD? (METHODSLOT)
  (CL:LET* ((TEST-VALUE-000 (%SLOT-NAME METHODSLOT)))
   (CL:COND
    ((CL:OR (CL:EQ TEST-VALUE-000 SYM-CPP-CLASS-OUT-STELLA-DEFINED?)
      (CL:EQ TEST-VALUE-000 SYM-CPP-CLASS-OUT-STELLA-NULL?))
     (CL:RETURN-FROM CPP-NATIVE-METHOD? CL:T))
    (CL:T (CL:RETURN-FROM CPP-NATIVE-METHOD? CL:NIL)))))

;;; (DEFUN (CPP-GET-PARAMETERIZED-MEMBER-VARIABLE-DEFINITIONS CONS) ...)

(CL:DEFUN CPP-GET-PARAMETERIZED-MEMBER-VARIABLE-DEFINITIONS (CLASS)
  (CL:LET* ((MEMBERVARDEFS NIL))
   (CL:LET*
    ((SLOT NULL) (ITER-000 (%THE-CONS-LIST (%CLASS-LOCAL-SLOTS CLASS)))
     (COLLECT-000 NULL))
    (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-000 NIL)) DO
     (CL:SETQ SLOT (%%VALUE ITER-000))
     (CL:WHEN
      (CL:AND (STORAGE-SLOT? SLOT) (NATIVE-SLOT? SLOT)
       (SLOT-HAS-CLASS-PARAMETER-TYPE? SLOT CLASS))
      (CL:IF (CL:EQ COLLECT-000 NULL)
       (CL:PROGN
        (CL:SETQ COLLECT-000
         (CONS (CPP-YIELD-PARAMETERIZED-MEMBER-VAR-TREE SLOT CLASS)
          NIL))
        (CL:IF (CL:EQ MEMBERVARDEFS NIL)
         (CL:SETQ MEMBERVARDEFS COLLECT-000)
         (ADD-CONS-TO-END-OF-CONS-LIST MEMBERVARDEFS COLLECT-000)))
       (CL:PROGN
        (CL:SETF (%%REST COLLECT-000)
         (CONS (CPP-YIELD-PARAMETERIZED-MEMBER-VAR-TREE SLOT CLASS)
          NIL))
        (CL:SETQ COLLECT-000 (%%REST COLLECT-000)))))
     (CL:SETQ ITER-000 (%%REST ITER-000))))
   (CL:RETURN-FROM CPP-GET-PARAMETERIZED-MEMBER-VARIABLE-DEFINITIONS
    MEMBERVARDEFS)))

;;; (DEFUN (CPP-GET-MEMBER-VARIABLE-DEFINITIONS CONS CONS) ...)

(CL:DEFUN CPP-GET-MEMBER-VARIABLE-DEFINITIONS (CLASS)
  (CL:LET* ((PUBLICMEMBERVARDEFS NIL) (PROTECTEDMEMBERVARDEFS NIL))
   (CL:LET* ((SLOT NULL) (ITER-000 (CLASS-SLOTS CLASS)))
    (CL:LOOP WHILE (NEXT? ITER-000) DO (CL:SETQ SLOT (%VALUE ITER-000))
     (CL:WHEN
      (CL:AND (STORAGE-SLOT? SLOT) (NATIVE-SLOT? SLOT)
       (CL:EQ (NATIVE-SLOT-HOME SLOT CLASS) CLASS))
      (CL:IF (%SLOT-PUBLIC? SLOT)
       (CL:SETQ PUBLICMEMBERVARDEFS
        (CONS (CPP-YIELD-MEMBER-VAR-TREE SLOT CLASS)
         PUBLICMEMBERVARDEFS))
       (CL:SETQ PROTECTEDMEMBERVARDEFS
        (CONS (CPP-YIELD-MEMBER-VAR-TREE SLOT CLASS)
         PROTECTEDMEMBERVARDEFS))))))
   (CL:RETURN-FROM CPP-GET-MEMBER-VARIABLE-DEFINITIONS
    (CL:VALUES (REVERSE PUBLICMEMBERVARDEFS)
     (REVERSE PROTECTEDMEMBERVARDEFS)))))

;;; (DEFUN (CPP-GET-STATIC-VARIABLE-DEFINITIONS CONS) ...)

(CL:DEFUN CPP-GET-STATIC-VARIABLE-DEFINITIONS (CLASS)
  (CL:LET* ((STATICMEMBERVARDEFS NIL))
   (CL:LET* ((SLOT NULL) (ITER-000 (CLASS-SLOTS CLASS)))
    (CL:LOOP WHILE (NEXT? ITER-000) DO (CL:SETQ SLOT (%VALUE ITER-000))
     (CL:WHEN
      (CL:AND (STORAGE-SLOT? SLOT) (NATIVE-SLOT? SLOT)
       (CL:EQ (ALLOCATION SLOT) KWD-CPP-CLASS-OUT-CLASS)
       (CL:NOT (%SLOT-HARDWIRED? SLOT)) (CL:NOT (%SLOT-MARKED? SLOT))
       (CL:EQ (NATIVE-SLOT-HOME SLOT CLASS) CLASS))
      (CL:SETQ STATICMEMBERVARDEFS
       (CONS (CPP-YIELD-STATIC-MEMBER-ALLOCATION-TREE SLOT CLASS)
        STATICMEMBERVARDEFS)))))
   (CL:RETURN-FROM CPP-GET-STATIC-VARIABLE-DEFINITIONS
    STATICMEMBERVARDEFS)))

;;; (DEFUN (CPP-GET-CONSTRUCTOR-DEFINITIONS CONS) ...)

(CL:DEFUN CPP-GET-CONSTRUCTOR-DEFINITIONS (CLASS)
  (CL:LET* ((CONSTRUCTORDEFS NIL))
   (CL:LET*
    ((SLOT NULL) (ITER-000 (CLASS-SLOTS CLASS)) (COLLECT-000 NULL))
    (CL:LOOP WHILE (NEXT? ITER-000) DO (CL:SETQ SLOT (%VALUE ITER-000))
     (CL:WHEN
      (CL:AND (CL:NOT (%SLOT-MARKED? SLOT))
       (CL:EQ (PRIMARY-TYPE SLOT) SGT-CPP-CLASS-OUT-STELLA-METHOD-SLOT)
       (LOCAL-SLOT? SLOT CLASS) (CPP-CONSTRUCTOR? SLOT))
      (CL:IF (CL:EQ COLLECT-000 NULL)
       (CL:PROGN
        (CL:SETQ COLLECT-000
         (CONS (CPP-YIELD-CONSTRUCTOR-SIGNATURE-TREE SLOT) NIL))
        (CL:IF (CL:EQ CONSTRUCTORDEFS NIL)
         (CL:SETQ CONSTRUCTORDEFS COLLECT-000)
         (ADD-CONS-TO-END-OF-CONS-LIST CONSTRUCTORDEFS COLLECT-000)))
       (CL:PROGN
        (CL:SETF (%%REST COLLECT-000)
         (CONS (CPP-YIELD-CONSTRUCTOR-SIGNATURE-TREE SLOT) NIL))
        (CL:SETQ COLLECT-000 (%%REST COLLECT-000)))))))
   (CL:RETURN-FROM CPP-GET-CONSTRUCTOR-DEFINITIONS CONSTRUCTORDEFS)))

;;; (DEFUN (CPP-GET-METHOD-DEFINITIONS CONS CONS) ...)

(CL:DEFUN CPP-GET-METHOD-DEFINITIONS (CLASS)
  (CL:LET* ((PUBLICMEMBERFUNCDEFS NIL) (PROTECTEDMEMBERFUNCDEFS NIL))
   (CL:LET*
    ((SLOT NULL)
     (ITER-000 (%THE-CONS-LIST (%CLASS-LOCAL-SLOTS CLASS))))
    (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-000 NIL)) DO
     (CL:SETQ SLOT (%%VALUE ITER-000))
     (CL:COND
      ((SUBTYPE-OF-METHOD-SLOT? (SAFE-PRIMARY-TYPE SLOT))
       (CL:PROGN
        (CL:WHEN
         (CL:AND (CL:NOT (%SLOT-MARKED? SLOT)) (NATIVE-METHOD? SLOT)
          (CL:NOT (CPP-CONSTRUCTOR? SLOT))
          (CL:NOT (CPP-NATIVE-METHOD? SLOT)))
         (CL:IF (%SLOT-PUBLIC? SLOT)
          (CL:SETQ PUBLICMEMBERFUNCDEFS
           (CONS (CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE SLOT)
            PUBLICMEMBERFUNCDEFS))
          (CL:SETQ PROTECTEDMEMBERFUNCDEFS
           (CONS (CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE SLOT)
            PROTECTEDMEMBERFUNCDEFS))))))
      (CL:T))
     (CL:SETQ ITER-000 (%%REST ITER-000))))
   (CL:LET*
    ((METHOD NULL)
     (ITER-001 (%THE-CONS-LIST (CLASS-AUXILIARY-METHODS CLASS))))
    (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-001 NIL)) DO
     (CL:SETQ METHOD (%%VALUE ITER-001))
     (CL:IF (%SLOT-PUBLIC? METHOD)
      (CL:SETQ PUBLICMEMBERFUNCDEFS
       (CONS (CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE METHOD)
        PUBLICMEMBERFUNCDEFS))
      (CL:SETQ PROTECTEDMEMBERFUNCDEFS
       (CONS (CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE METHOD)
        PROTECTEDMEMBERFUNCDEFS)))
     (CL:SETQ ITER-001 (%%REST ITER-001))))
   (CL:RETURN-FROM CPP-GET-METHOD-DEFINITIONS
    (CL:VALUES (REVERSE PUBLICMEMBERFUNCDEFS)
     (REVERSE PROTECTEDMEMBERFUNCDEFS)))))

;;; (DEFUN (MARK-RENAMING-SLOTS VOID) ...)

(CL:DEFUN MARK-RENAMING-SLOTS (CLASS)
  (CL:LET* ((SLOT NULL) (ITER-000 (CLASS-SLOTS CLASS)))
   (CL:LOOP WHILE (NEXT? ITER-000) DO (CL:SETQ SLOT (%VALUE ITER-000))
    (CL:SETF (%SLOT-MARKED? SLOT) CL:NIL)))
  (CL:LET* ((SLOT NULL) (ITER-001 (CLASS-SLOTS CLASS)))
   (CL:LOOP WHILE (NEXT? ITER-001) DO (CL:SETQ SLOT (%VALUE ITER-001))
    (CL:WHEN (CL:NOT (%SLOT-MARKED? SLOT))
     (CL:WHEN
      (CL:AND (CL:NOT (CL:EQ (%SLOT-DIRECT-EQUIVALENT SLOT) NULL))
       (CL:NOT (%SLOT-RENAMED? (%SLOT-DIRECT-EQUIVALENT SLOT))))
      (MARK-DIRECT-EQUIVALENT-SLOT SLOT)
      (CL:SETF (%SLOT-MARKED? SLOT) CL:NIL)))))
  :VOID)

;;; (DEFUN (CPP-CLASS-HAS-ONLY-NATIVE-PARENTS? BOOLEAN) ...)

(CL:DEFUN CPP-CLASS-HAS-ONLY-NATIVE-PARENTS? (CLASS)
  (CL:LET* ((SUPER NULL) (ITER-000 (%CLASS-ALL-SUPER-CLASSES CLASS)))
   (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-000 NIL)) DO
    (CL:SETQ SUPER (%%VALUE ITER-000))
    (CL:WHEN (CL:NOT (%MIXIN? SUPER))
     (CL:WHEN
      (CL:AND (CREATE-NATIVE-CLASS? SUPER)
       (CL:EQ
        (%WRAPPER-VALUE
         (DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS SUPER)
          SYM-CPP-CLASS-OUT-STELLA-CLASS-CPP-NATIVE-TYPE
          NULL-STRING-WRAPPER))
        STELLA::NULL-STRING))
      (CL:RETURN-FROM CPP-CLASS-HAS-ONLY-NATIVE-PARENTS? CL:NIL)))
    (CL:SETQ ITER-000 (%%REST ITER-000))))
  (CL:RETURN-FROM CPP-CLASS-HAS-ONLY-NATIVE-PARENTS? CL:T))

;;; (DEFUN (CPP-TRANSLATE-DEFINE-NATIVE-CLASS-UNIT CONS) ...)

(CL:DEFUN CPP-TRANSLATE-DEFINE-NATIVE-CLASS-UNIT (UNIT)
  (CL:LET*
   ((CLASS (%THE-OBJECT UNIT)) (BASECLASSES NIL)
    (PARAMETERIZEDMEMBERVARDEFS NIL) (PUBLICMEMBERVARDEFS NIL)
    (PROTECTEDMEMBERVARDEFS NIL) (PUBLICMEMBERFUNCDEFS NIL)
    (PROTECTEDMEMBERFUNCDEFS NIL) (CONSTRUCTORDEFS NIL)
    (PARAMETERS NIL) (STATICMEMBERVARDEFS NIL))
   (CL:LET*
    ((SUPER NULL)
     (ITER-000 (%THE-CONS-LIST (CLASS-NATIVE-SUPERS CLASS)))
     (COLLECT-000 NULL))
    (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-000 NIL)) DO
     (CL:SETQ SUPER (%%VALUE ITER-000))
     (CL:WHEN
      (CL:OR (CL:NOT (%MIXIN? (%SURROGATE-VALUE SUPER)))
       (CL:NOT (TRANSLATE-TO-SINGLE-INHERITANCE-LANGUAGE?)))
      (CL:IF (CL:EQ COLLECT-000 NULL)
       (CL:PROGN
        (CL:SETQ COLLECT-000
         (CONS (CPP-TRANSLATE-CLASS-NAME SUPER) NIL))
        (CL:IF (CL:EQ BASECLASSES NIL)
         (CL:SETQ BASECLASSES COLLECT-000)
         (ADD-CONS-TO-END-OF-CONS-LIST BASECLASSES COLLECT-000)))
       (CL:PROGN
        (CL:SETF (%%REST COLLECT-000)
         (CONS (CPP-TRANSLATE-CLASS-NAME SUPER) NIL))
        (CL:SETQ COLLECT-000 (%%REST COLLECT-000)))))
     (CL:SETQ ITER-000 (%%REST ITER-000))))
   (CL:WHEN
    (CL:AND
     (CL:OR (CL:EQ BASECLASSES NIL)
      (CPP-CLASS-HAS-ONLY-NATIVE-PARENTS? CLASS))
     (CL:NOT (%MIXIN? CLASS))
     (CL:EQ *TRANSLATOROUTPUTLANGUAGE* KWD-CPP-CLASS-OUT-CPP)
     (CPP-USE-GARBAGE-COLLECTOR?))
    (CL:SETQ BASECLASSES
     (CONS (CPP-TRANSLATE-NAME SYM-CPP-CLASS-OUT-STELLA-GC)
      BASECLASSES)))
   (CL:LET*
    ((PARAMETER NULL)
     (ITER-001 (%THE-CONS-LIST (CLASS-PARAMETERS CLASS)))
     (COLLECT-001 NULL))
    (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-001 NIL)) DO
     (CL:SETQ PARAMETER (%%VALUE ITER-001))
     (CL:IF (CL:EQ COLLECT-001 NULL)
      (CL:PROGN
       (CL:SETQ COLLECT-001
        (CONS (CPP-TRANSLATE-CLASS-PARAMETER-NAME PARAMETER) NIL))
       (CL:IF (CL:EQ PARAMETERS NIL) (CL:SETQ PARAMETERS COLLECT-001)
        (ADD-CONS-TO-END-OF-CONS-LIST PARAMETERS COLLECT-001)))
      (CL:PROGN
       (CL:SETF (%%REST COLLECT-001)
        (CONS (CPP-TRANSLATE-CLASS-PARAMETER-NAME PARAMETER) NIL))
       (CL:SETQ COLLECT-001 (%%REST COLLECT-001))))
     (CL:SETQ ITER-001 (%%REST ITER-001))))
   (MARK-RENAMING-SLOTS CLASS)
   (CL:WHEN
    (CL:EQ *TRANSLATOROUTPUTLANGUAGE* KWD-CPP-CLASS-OUT-CPP-STANDALONE)
    (CL:SETQ CONSTRUCTORDEFS (CPP-GET-CONSTRUCTOR-DEFINITIONS CLASS)))
   (CL:WHEN (CPP-OUTPUT-TEMPLATE-CLASSES?)
    (CL:SETQ PARAMETERIZEDMEMBERVARDEFS
     (CPP-GET-PARAMETERIZED-MEMBER-VARIABLE-DEFINITIONS CLASS)))
   (CL:MULTIPLE-VALUE-SETQ (PUBLICMEMBERVARDEFS PROTECTEDMEMBERVARDEFS)
    (CPP-GET-MEMBER-VARIABLE-DEFINITIONS CLASS))
   (CL:MULTIPLE-VALUE-SETQ
    (PUBLICMEMBERFUNCDEFS PROTECTEDMEMBERFUNCDEFS)
    (CPP-GET-METHOD-DEFINITIONS CLASS))
   (CL:SETQ STATICMEMBERVARDEFS
    (CPP-GET-STATIC-VARIABLE-DEFINITIONS CLASS))
   (CL:RETURN-FROM CPP-TRANSLATE-DEFINE-NATIVE-CLASS-UNIT
    (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_CLASS
     (CPP-TRANSLATE-CLASS-NAME
      (INTERN-SYMBOL-IN-MODULE (%SYMBOL-NAME (%CLASS-TYPE CLASS))
       (%HOME-CONTEXT (%CLASS-TYPE CLASS)) CL:NIL))
     (CONS PARAMETERS
      (CONS BASECLASSES
       (CONS STATICMEMBERVARDEFS
        (CONCATENATE
         (CL:IF
          (CL:NOT
           (CL:EQ
            (%WRAPPER-VALUE
             (DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS CLASS)
              SYM-CPP-CLASS-OUT-STELLA-DOCUMENTATION
              NULL-STRING-WRAPPER))
            STELLA::NULL-STRING))
          (CONS
           (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_COMMENT
            (WRAP-STRING
             (%WRAPPER-VALUE
              (DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS CLASS)
               SYM-CPP-CLASS-OUT-STELLA-DOCUMENTATION
               NULL-STRING-WRAPPER)))
            NIL)
           NIL)
          NIL)
         (CONCATENATE
          (CL:IF (CL:NOT (CL:EQ PARAMETERIZEDMEMBERVARDEFS NIL))
           (CONS
            (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_DECLARATIONS
             KWD-CPP-CLASS-OUT-PUBLIC PARAMETERIZEDMEMBERVARDEFS NIL)
            NIL)
           NIL)
          (CONCATENATE
           (CL:IF (CL:NOT (CL:EQ PUBLICMEMBERVARDEFS NIL))
            (CONS
             (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_DECLARATIONS
              KWD-CPP-CLASS-OUT-PUBLIC PUBLICMEMBERVARDEFS NIL)
             NIL)
            NIL)
           (CONCATENATE
            (CL:IF (CL:NOT (CL:EQ PROTECTEDMEMBERVARDEFS NIL))
             (CONS
              (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_DECLARATIONS
               KWD-CPP-CLASS-OUT-PUBLIC PROTECTEDMEMBERVARDEFS NIL)
              NIL)
             NIL)
            (CONCATENATE
             (CL:IF (CL:NOT (CL:EQ CONSTRUCTORDEFS NIL))
              (CONS
               (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_SIGNATURES
                KWD-CPP-CLASS-OUT-PUBLIC CONSTRUCTORDEFS NIL)
               NIL)
              NIL)
             (CONCATENATE
              (CL:IF (EXCEPTION-CLASS? CLASS)
               (CONS
                (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_DEFINITIONS
                 KWD-CPP-CLASS-OUT-PUBLIC
                 (CONS
                  (CPP-YIELD-EXCEPTION-CONSTRUCTOR-DEFINITION CLASS)
                  NIL)
                 NIL)
                NIL)
               NIL)
              (CONCATENATE
               (CL:IF (CL:NOT (CL:EQ PUBLICMEMBERFUNCDEFS NIL))
                (CONS
                 (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_SIGNATURES
                  KWD-CPP-CLASS-OUT-PUBLIC PUBLICMEMBERFUNCDEFS NIL)
                 NIL)
                NIL)
               (CONCATENATE
                (CL:IF (CL:NOT (CL:EQ PROTECTEDMEMBERFUNCDEFS NIL))
                 (CONS
                  (LIST* SYM-CPP-CLASS-OUT-STELLA-CPP_SIGNATURES
                   KWD-CPP-CLASS-OUT-PUBLIC PROTECTEDMEMBERFUNCDEFS
                   NIL)
                  NIL)
                 NIL)
                NIL)))))))))))))))

(CL:DEFUN STARTUP-CPP-CLASS-OUT ()
  (CL:LET* ((*MODULE* *STELLA-MODULE*) (*CONTEXT* *MODULE*))
   (CL:DECLARE (CL:SPECIAL *MODULE* *CONTEXT*))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 2)
    (CL:SETQ SGT-CPP-CLASS-OUT-STELLA-OBJECT
     (INTERN-RIGID-SYMBOL-WRT-MODULE "OBJECT" NULL 1))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-DOCUMENTATION
     (INTERN-RIGID-SYMBOL-WRT-MODULE "DOCUMENTATION" NULL 0))
    (CL:SETQ KWD-CPP-CLASS-OUT-EMBEDDED
     (INTERN-RIGID-SYMBOL-WRT-MODULE "EMBEDDED" NULL 2))
    (CL:SETQ KWD-CPP-CLASS-OUT-INSTANCE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "INSTANCE" NULL 2))
    (CL:SETQ KWD-CPP-CLASS-OUT-CLASS
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CLASS" NULL 2))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-NULL
     (INTERN-RIGID-SYMBOL-WRT-MODULE "NULL" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_FUNCTION
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_FUNCTION" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_FUNCTION_CALL
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_FUNCTION_CALL" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_IDENT
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_IDENT" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_ACTUALS
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_ACTUALS" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-SLOT-TYPE-SPECIFIER
     (INTERN-RIGID-SYMBOL-WRT-MODULE "SLOT-TYPE-SPECIFIER" NULL 0))
    (CL:SETQ SGT-CPP-CLASS-OUT-STELLA-ANCHORED-TYPE-SPECIFIER
     (INTERN-RIGID-SYMBOL-WRT-MODULE "ANCHORED-TYPE-SPECIFIER" NULL 1))
    (CL:SETQ SGT-CPP-CLASS-OUT-STELLA-UNKNOWN
     (INTERN-RIGID-SYMBOL-WRT-MODULE "UNKNOWN" NULL 1))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-DEFINED?
     (INTERN-RIGID-SYMBOL-WRT-MODULE "DEFINED?" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-NULL?
     (INTERN-RIGID-SYMBOL-WRT-MODULE "NULL?" NULL 0))
    (CL:SETQ SGT-CPP-CLASS-OUT-STELLA-METHOD-SLOT
     (INTERN-RIGID-SYMBOL-WRT-MODULE "METHOD-SLOT" NULL 1))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CLASS-CPP-NATIVE-TYPE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CLASS-CPP-NATIVE-TYPE" NULL 0))
    (CL:SETQ KWD-CPP-CLASS-OUT-CPP
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP" NULL 2))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-GC
     (INTERN-RIGID-SYMBOL-WRT-MODULE "GC" NULL 0))
    (CL:SETQ KWD-CPP-CLASS-OUT-CPP-STANDALONE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP-STANDALONE" NULL 2))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_CLASS
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_CLASS" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_COMMENT
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_COMMENT" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_DECLARATIONS
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_DECLARATIONS" NULL 0))
    (CL:SETQ KWD-CPP-CLASS-OUT-PUBLIC
     (INTERN-RIGID-SYMBOL-WRT-MODULE "PUBLIC" NULL 2))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_SIGNATURES
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_SIGNATURES" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-CPP_DEFINITIONS
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CPP_DEFINITIONS" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-STARTUP-CPP-CLASS-OUT
     (INTERN-RIGID-SYMBOL-WRT-MODULE "STARTUP-CPP-CLASS-OUT" NULL 0))
    (CL:SETQ SYM-CPP-CLASS-OUT-STELLA-METHOD-STARTUP-CLASSNAME
     (INTERN-RIGID-SYMBOL-WRT-MODULE "METHOD-STARTUP-CLASSNAME" NULL
      0)))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 6) (FINALIZE-CLASSES))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 7)
    (DEFINE-FUNCTION-OBJECT "CPP-YIELD-INITIAL-NULL-VALUE"
     "(DEFUN (CPP-YIELD-INITIAL-NULL-VALUE CONS) ())"
     (CL:FUNCTION CPP-YIELD-INITIAL-NULL-VALUE) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-YIELD-MEMBER-VAR-TREE"
     "(DEFUN (CPP-YIELD-MEMBER-VAR-TREE CONS) ((SLOT STORAGE-SLOT) (CLASS CLASS)))"
     (CL:FUNCTION CPP-YIELD-MEMBER-VAR-TREE) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-YIELD-PARAMETERIZED-MEMBER-VAR-TREE"
     "(DEFUN (CPP-YIELD-PARAMETERIZED-MEMBER-VAR-TREE CONS) ((SLOT STORAGE-SLOT) (CLASS CLASS)))"
     (CL:FUNCTION CPP-YIELD-PARAMETERIZED-MEMBER-VAR-TREE) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-YIELD-STATIC-MEMBER-ALLOCATION-TREE"
     "(DEFUN (CPP-YIELD-STATIC-MEMBER-ALLOCATION-TREE CONS) ((SLOT STORAGE-SLOT) (CLASS CLASS)))"
     (CL:FUNCTION CPP-YIELD-STATIC-MEMBER-ALLOCATION-TREE) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE"
     "(DEFUN (CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE CONS) ((METHOD METHOD-SLOT)))"
     (CL:FUNCTION CPP-YIELD-MEMBER-FUNC-SIGNATURE-TREE) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-YIELD-CONSTRUCTOR-SIGNATURE-TREE"
     "(DEFUN (CPP-YIELD-CONSTRUCTOR-SIGNATURE-TREE CONS) ((METHOD METHOD-SLOT)))"
     (CL:FUNCTION CPP-YIELD-CONSTRUCTOR-SIGNATURE-TREE) NULL)
    (DEFINE-FUNCTION-OBJECT
     "CPP-YIELD-EXCEPTION-CONSTRUCTOR-DEFINITION"
     "(DEFUN (CPP-YIELD-EXCEPTION-CONSTRUCTOR-DEFINITION CONS) ((CLASS CLASS)))"
     (CL:FUNCTION CPP-YIELD-EXCEPTION-CONSTRUCTOR-DEFINITION) NULL)
    (DEFINE-FUNCTION-OBJECT "SLOT-HAS-CLASS-PARAMETER-TYPE?"
     "(DEFUN (SLOT-HAS-CLASS-PARAMETER-TYPE? BOOLEAN) ((SLOT STORAGE-SLOT) (CLASS CLASS)))"
     (CL:FUNCTION SLOT-HAS-CLASS-PARAMETER-TYPE?) NULL)
    (DEFINE-FUNCTION-OBJECT "GET-SLOT-CLASS-PARAMETER-NAME"
     "(DEFUN (GET-SLOT-CLASS-PARAMETER-NAME SYMBOL) ((SLOT STORAGE-SLOT)))"
     (CL:FUNCTION GET-SLOT-CLASS-PARAMETER-NAME) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-NATIVE-METHOD?"
     "(DEFUN (CPP-NATIVE-METHOD? BOOLEAN) ((METHODSLOT METHOD-SLOT)))"
     (CL:FUNCTION CPP-NATIVE-METHOD?) NULL)
    (DEFINE-FUNCTION-OBJECT
     "CPP-GET-PARAMETERIZED-MEMBER-VARIABLE-DEFINITIONS"
     "(DEFUN (CPP-GET-PARAMETERIZED-MEMBER-VARIABLE-DEFINITIONS CONS) ((CLASS CLASS)))"
     (CL:FUNCTION CPP-GET-PARAMETERIZED-MEMBER-VARIABLE-DEFINITIONS)
     NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-GET-MEMBER-VARIABLE-DEFINITIONS"
     "(DEFUN (CPP-GET-MEMBER-VARIABLE-DEFINITIONS CONS CONS) ((CLASS CLASS)))"
     (CL:FUNCTION CPP-GET-MEMBER-VARIABLE-DEFINITIONS) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-GET-STATIC-VARIABLE-DEFINITIONS"
     "(DEFUN (CPP-GET-STATIC-VARIABLE-DEFINITIONS CONS) ((CLASS CLASS)))"
     (CL:FUNCTION CPP-GET-STATIC-VARIABLE-DEFINITIONS) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-GET-CONSTRUCTOR-DEFINITIONS"
     "(DEFUN (CPP-GET-CONSTRUCTOR-DEFINITIONS CONS) ((CLASS CLASS)))"
     (CL:FUNCTION CPP-GET-CONSTRUCTOR-DEFINITIONS) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-GET-METHOD-DEFINITIONS"
     "(DEFUN (CPP-GET-METHOD-DEFINITIONS CONS CONS) ((CLASS CLASS)))"
     (CL:FUNCTION CPP-GET-METHOD-DEFINITIONS) NULL)
    (DEFINE-FUNCTION-OBJECT "MARK-RENAMING-SLOTS"
     "(DEFUN (MARK-RENAMING-SLOTS VOID) ((CLASS CLASS)))"
     (CL:FUNCTION MARK-RENAMING-SLOTS) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-CLASS-HAS-ONLY-NATIVE-PARENTS?"
     "(DEFUN (CPP-CLASS-HAS-ONLY-NATIVE-PARENTS? BOOLEAN) ((CLASS CLASS)))"
     (CL:FUNCTION CPP-CLASS-HAS-ONLY-NATIVE-PARENTS?) NULL)
    (DEFINE-FUNCTION-OBJECT "CPP-TRANSLATE-DEFINE-NATIVE-CLASS-UNIT"
     "(DEFUN (CPP-TRANSLATE-DEFINE-NATIVE-CLASS-UNIT CONS) ((UNIT TRANSLATION-UNIT)))"
     (CL:FUNCTION CPP-TRANSLATE-DEFINE-NATIVE-CLASS-UNIT) NULL)
    (DEFINE-FUNCTION-OBJECT "STARTUP-CPP-CLASS-OUT"
     "(DEFUN STARTUP-CPP-CLASS-OUT () :PUBLIC? TRUE)"
     (CL:FUNCTION STARTUP-CPP-CLASS-OUT) NULL)
    (CL:LET*
     ((FUNCTION
       (LOOKUP-FUNCTION
        SYM-CPP-CLASS-OUT-STELLA-STARTUP-CPP-CLASS-OUT)))
     (SET-DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS FUNCTION)
      SYM-CPP-CLASS-OUT-STELLA-METHOD-STARTUP-CLASSNAME
      (WRAP-STRING "_StartupCppClassOut") NULL-STRING-WRAPPER)))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 8) (FINALIZE-SLOTS)
    (CLEANUP-UNFINALIZED-CLASSES))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 9)
    (%IN-MODULE (COPY-CONS-TREE (WRAP-STRING "/STELLA")))))
  :VOID)
