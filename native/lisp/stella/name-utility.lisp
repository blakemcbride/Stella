;;; -*- Mode: Lisp; Package: STELLA; Syntax: COMMON-LISP; Base: 10 -*-

;;; name-utility.lisp

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

(CL:DEFVAR KWD-NAME-UTILITY-CLEVER NULL)
(CL:DEFVAR KWD-NAME-UTILITY-TITLECASE NULL)
(CL:DEFVAR KWD-NAME-UTILITY-BREAK-ON-CAP NULL)
(CL:DEFVAR KWD-NAME-UTILITY-NO NULL)
(CL:DEFVAR KWD-NAME-UTILITY-BREAK-ON-NUMBER NULL)
(CL:DEFVAR KWD-NAME-UTILITY-BREAK-ON-SEPARATORS NULL)
(CL:DEFVAR KWD-NAME-UTILITY-REMOVE-PREFIX NULL)
(CL:DEFVAR KWD-NAME-UTILITY-REMOVE-SUFFIX NULL)
(CL:DEFVAR KWD-NAME-UTILITY-ADD-PREFIX NULL)
(CL:DEFVAR KWD-NAME-UTILITY-ADD-SUFFIX NULL)
(CL:DEFVAR KWD-NAME-UTILITY-CASE NULL)
(CL:DEFVAR KWD-NAME-UTILITY-SEPARATOR NULL)
(CL:DEFVAR KWD-NAME-UTILITY-PREFIX NULL)
(CL:DEFVAR KWD-NAME-UTILITY-SUFFIX NULL)
(CL:DEFVAR KWD-NAME-UTILITY-TRANSLATION-TABLE NULL)
(CL:DEFVAR KWD-NAME-UTILITY-USE-ACRONYM-HEURISTICS? NULL)
(CL:DEFVAR KWD-NAME-UTILITY-DIGIT NULL)
(CL:DEFVAR KWD-NAME-UTILITY-PRESERVE NULL)
(CL:DEFVAR KWD-NAME-UTILITY-ALLCAPS NULL)
(CL:DEFVAR KWD-NAME-UTILITY-UPCASE NULL)
(CL:DEFVAR KWD-NAME-UTILITY-DOWNCASE NULL)
(CL:DEFVAR KWD-NAME-UTILITY-CAPITALIZE NULL)
(CL:DEFVAR KWD-NAME-UTILITY-TITLECASEX NULL)
(CL:DEFVAR SYM-NAME-UTILITY-STELLA-STARTUP-NAME-UTILITY NULL)
(CL:DEFVAR SYM-NAME-UTILITY-STELLA-METHOD-STARTUP-CLASSNAME NULL)

;;; Forward declarations:

(CL:DECLAIM
 (CL:SPECIAL *STELLA-MODULE* *MODULE* NULL-CHARACTER
  *CHARACTER-TYPE-TABLE* NULL-INTEGER TRUE-WRAPPER NIL))

;;; (DEFUN (MAKE-MATCHING-NAME STRING) ...)

(CL:DECLAIM
 (CL:FTYPE
  (CL:FUNCTION (CL:SIMPLE-STRING CL:&REST CL:T) CL:SIMPLE-STRING)
  MAKE-MATCHING-NAME))
(CL:DEFUN MAKE-MATCHING-NAME (ORIGINAL CL:&REST OPTIONS)
  "Keyword options:
  :break-on-cap    one of  :YES :NO :CLEVER         default is :CLEVER
  :break-on-number one of  :YES :NO :CLEVER         default is :CLEVER
  :break-on-separators string                       default is \"-_ \"
  :remove-prefix   string
  :remove-suffix   string
  
  :case            one of  :UPCASE :TitleCase :titleCaseX :downcase :Capitalize :preserve
                                                     default is :TitleCase
  :separator       string                            default is \"\"
  :add-prefix      string
  :add-suffix      string

  MAKE-MATCHING-NAME returns a matching name (a string) for the input name (a string).
A matching name is constructed by breaking the input into 'words' and then applying
appropriate transforms.  The arguments are used as follows:
  `original'         is the input name.  It is a string.
  :break-on-cap    is a keyword controlling whether changes in capitalization is used
                   to indicate word boundaries.  If :YES, then all capitalization
                   changes delineate words.  If :CLEVER, then unbroken runs of
                   capitalized letters are treated as acronyms and remain grouped.
                   If :NO or NULL, there is no breaking of words based on capitalization.
  :break-on-number is a flag controlling whether encountering a number indicates
                   a word boundary.  If :YES, then each run of numbers is treated as
		   a word separate from surrounding words.  If :CLEVER, then an 
		   attempt is made to recognize ordinal numbers (ie, 101st) and
		   treat them as separate words.  If :NO or NULL, there is no breaking
                   of words when numbers are encountered.
  :break-on-separators   A string of characters which constitute word delimiters in
                         the input word.  This is used to determine how to break
                   the name into individual words.  Defaults are space, '-' and '_'.
  :remove-prefix   Specifies a prefix or suffix that is stripped from the input
  :remove-suffix   name before any other processing.  This allows the removal of
                   any naming convention dictated prefixes or suffixes.
  :add-prefix      Specifies a prefix or suffix that is added to the output name
  :add-suffix      after all other processing.  This allows the addition of any
                   naming convention dictated prefixes or suffixes.
  :case            The case of the resulting name.  This is applied to the name 
                   before adding prefixes or suffixes.  The two title case options 
                   differ only in how the first word of the name is treated.
                   :TitleCase capitalizes the first letter of the first word and
                       also the first letter of all other words.
                   :TitleCaseX does not capitalizes the first letter of the first
		       word but capitalizes the first letter of all subsequent words.
		   :preserve results in no change in case.
  :separator       This is a string specifying the word separator to use in the
                   returned name.  An empty string (the default) means that the
                   resulting words are concatenated without any separation.  This
                   normally only makes sense when using one of the title case values
                   for the case keyword."
  (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING ORIGINAL))
  #+MCL
  (CL:CHECK-TYPE ORIGINAL CL:SIMPLE-STRING)
  (CL:LET* ((SELF-000 (NEW-PROPERTY-LIST)))
   (CL:LET* ((ARGLIST-000 NIL))
    (CL:LET* ((ARG-000 NULL) (ITER-000 OPTIONS) (COLLECT-000 NULL))
     (CL:LOOP WHILE ITER-000 DO (CL:SETQ ARG-000 (CL:POP ITER-000))
      (CL:IF (CL:EQ COLLECT-000 NULL)
       (CL:PROGN (CL:SETQ COLLECT-000 (CONS ARG-000 NIL))
        (CL:IF (CL:EQ ARGLIST-000 NIL)
         (CL:SETQ ARGLIST-000 COLLECT-000)
         (ADD-CONS-TO-END-OF-CONS-LIST ARGLIST-000 COLLECT-000)))
       (CL:PROGN (CL:SETF (%%REST COLLECT-000) (CONS ARG-000 NIL))
        (CL:SETQ COLLECT-000 (%%REST COLLECT-000))))))
    (CL:SETF (%THE-PLIST SELF-000) ARGLIST-000))
   (CL:LET*
    ((PLIST SELF-000) (BREAKONCAP KWD-NAME-UTILITY-CLEVER)
     (BREAKONNUMBER KWD-NAME-UTILITY-CLEVER) (BREAKONSEPARATORS "-_ ")
     (REMOVEPREFIX "") (REMOVESUFFIX "") (ADDPREFIX "") (ADDSUFFIX "")
     (OUTPUTCASE KWD-NAME-UTILITY-TITLECASE) (OUTPUTSEPARATOR ""))
    (CL:DECLARE
     (CL:TYPE CL:SIMPLE-STRING BREAKONSEPARATORS REMOVEPREFIX
      REMOVESUFFIX ADDPREFIX ADDSUFFIX OUTPUTSEPARATOR))
    (VET-OPTIONS PLIST
     (GET-QUOTED-TREE
      "((:BREAK-ON-CAP :BREAK-ON-NUMBER :BREAK-ON-SEPARATORS :REMOVE-PREFIX :REMOVE-SUFFIX :ADD-PREFIX :ADD-SUFFIX :CASE :SEPARATOR) \"/STELLA\")"
      "/STELLA"))
    (CL:LET* ((KEY NULL) (VALUE NULL) (ITER-001 (%THE-PLIST PLIST)))
     (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-001 NIL)) DO
      (CL:SETQ KEY (%%VALUE ITER-001))
      (CL:SETQ VALUE (%%VALUE (%%REST ITER-001)))
      (CL:LET* ((TEST-VALUE-000 KEY))
       (CL:COND
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-BREAK-ON-CAP)
         (CL:IF (CL:NOT (CL:EQ VALUE NULL)) (CL:SETQ BREAKONCAP VALUE)
          (CL:SETQ BREAKONCAP KWD-NAME-UTILITY-NO)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-BREAK-ON-NUMBER)
         (CL:IF (CL:NOT (CL:EQ VALUE NULL))
          (CL:SETQ BREAKONNUMBER VALUE)
          (CL:SETQ BREAKONNUMBER KWD-NAME-UTILITY-NO)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-BREAK-ON-SEPARATORS)
         (CL:SETQ BREAKONSEPARATORS (%WRAPPER-VALUE VALUE)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-REMOVE-PREFIX)
         (CL:SETQ REMOVEPREFIX (%WRAPPER-VALUE VALUE)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-REMOVE-SUFFIX)
         (CL:SETQ REMOVESUFFIX (%WRAPPER-VALUE VALUE)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-ADD-PREFIX)
         (CL:SETQ ADDPREFIX (%WRAPPER-VALUE VALUE)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-ADD-SUFFIX)
         (CL:SETQ ADDSUFFIX (%WRAPPER-VALUE VALUE)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-CASE)
         (CL:SETQ OUTPUTCASE VALUE))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-SEPARATOR)
         (CL:SETQ OUTPUTSEPARATOR (%WRAPPER-VALUE VALUE)))
        (CL:T
         (CL:LET* ((STREAM-000 (NEW-OUTPUT-STRING-STREAM)))
          (%%PRINT-STREAM (%NATIVE-STREAM STREAM-000) "`"
           TEST-VALUE-000 "' is not a valid case option")
          (CL:ERROR
           (NEW-STELLA-EXCEPTION (THE-STRING-READER STREAM-000)))))))
      (CL:SETQ ITER-001 (%%REST (%%REST ITER-001)))))
    (CL:RETURN-FROM MAKE-MATCHING-NAME
     (MAKE-MATCHING-NAME-FULL ORIGINAL BREAKONCAP BREAKONNUMBER
      BREAKONSEPARATORS REMOVEPREFIX REMOVESUFFIX ADDPREFIX ADDSUFFIX
      OUTPUTCASE OUTPUTSEPARATOR)))))

;;; (DEFUN (DECOMPOSE-NAMESTRING (CONS OF STRING-WRAPPER)) ...)

(CL:DEFUN DECOMPOSE-NAMESTRING (NAMESTRING CL:&REST OPTIONS)
  "Keyword options:
  :break-on-cap    one of  :YES :NO :CLEVER         default is :CLEVER
  :break-on-number one of  :YES :NO :CLEVER         default is :CLEVER
  :break-on-separators string                       default is \"-_ \"

  DECOMPOSE-NAMESTRING returns a cons of STRING-WRAPPERS that are the decomposition of the
input STRING.  The arguments are used as follows:
  `namestring'       is the input string.
  :break-on-cap    is a keyword controlling whether changes in capitalization is used
                   to indicate word boundaries.  If :YES, then all capitalization
                   changes delineate words.  If :CLEVER, then unbroken runs of
                   capitalized letters are treated as acronyms and remain grouped.
                   If :NO or NULL, there is no breaking of words based on capitalization.
  :break-on-number is a flag controlling whether encountering a number indicates
                   a word boundary.  If :YES, then each run of numbers is treated as
		   a word separate from surrounding words.  If :CLEVER, then an 
		   attempt is made to recognize ordinal numbers (ie, 101st) and
		   treat them as separate words.  If :NO or NULL, there is no breaking
                   of words when numbers are encountered.
  :break-on-separators   A string of characters which constitute word delimiters in
                         the input word.  This is used to determine how to break
                   the name into individual words.  Defaults are space, '-' and '_'."
  (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING NAMESTRING))
  #+MCL
  (CL:CHECK-TYPE NAMESTRING CL:SIMPLE-STRING)
  (CL:LET* ((SELF-000 (NEW-PROPERTY-LIST)))
   (CL:LET* ((ARGLIST-000 NIL))
    (CL:LET* ((ARG-000 NULL) (ITER-000 OPTIONS) (COLLECT-000 NULL))
     (CL:LOOP WHILE ITER-000 DO (CL:SETQ ARG-000 (CL:POP ITER-000))
      (CL:IF (CL:EQ COLLECT-000 NULL)
       (CL:PROGN (CL:SETQ COLLECT-000 (CONS ARG-000 NIL))
        (CL:IF (CL:EQ ARGLIST-000 NIL)
         (CL:SETQ ARGLIST-000 COLLECT-000)
         (ADD-CONS-TO-END-OF-CONS-LIST ARGLIST-000 COLLECT-000)))
       (CL:PROGN (CL:SETF (%%REST COLLECT-000) (CONS ARG-000 NIL))
        (CL:SETQ COLLECT-000 (%%REST COLLECT-000))))))
    (CL:SETF (%THE-PLIST SELF-000) ARGLIST-000))
   (CL:LET*
    ((PLIST SELF-000) (BREAKONCAP KWD-NAME-UTILITY-CLEVER)
     (BREAKONNUMBER KWD-NAME-UTILITY-CLEVER) (BREAKONSEPARATORS "-_ "))
    (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING BREAKONSEPARATORS))
    (VET-OPTIONS PLIST
     (GET-QUOTED-TREE
      "((:BREAK-ON-CAP :BREAK-ON-NUMBER :BREAK-ON-SEPARATORS) \"/STELLA\")"
      "/STELLA"))
    (CL:LET* ((KEY NULL) (VALUE NULL) (ITER-001 (%THE-PLIST PLIST)))
     (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-001 NIL)) DO
      (CL:SETQ KEY (%%VALUE ITER-001))
      (CL:SETQ VALUE (%%VALUE (%%REST ITER-001)))
      (CL:LET* ((TEST-VALUE-000 KEY))
       (CL:COND
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-BREAK-ON-CAP)
         (CL:IF (CL:NOT (CL:EQ VALUE NULL)) (CL:SETQ BREAKONCAP VALUE)
          (CL:SETQ BREAKONCAP KWD-NAME-UTILITY-NO)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-BREAK-ON-NUMBER)
         (CL:IF (CL:NOT (CL:EQ VALUE NULL))
          (CL:SETQ BREAKONNUMBER VALUE)
          (CL:SETQ BREAKONNUMBER KWD-NAME-UTILITY-NO)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-BREAK-ON-SEPARATORS)
         (CL:SETQ BREAKONSEPARATORS (%WRAPPER-VALUE VALUE)))
        (CL:T
         (CL:LET* ((STREAM-000 (NEW-OUTPUT-STRING-STREAM)))
          (%%PRINT-STREAM (%NATIVE-STREAM STREAM-000) "`"
           TEST-VALUE-000 "' is not a valid case option")
          (CL:ERROR
           (NEW-STELLA-EXCEPTION (THE-STRING-READER STREAM-000)))))))
      (CL:SETQ ITER-001 (%%REST (%%REST ITER-001)))))
    (CL:RETURN-FROM DECOMPOSE-NAMESTRING
     (DECOMPOSE-NAMESTRING-FULL NAMESTRING BREAKONCAP BREAKONNUMBER
      BREAKONSEPARATORS)))))

;;; (DEFUN (COMPOSE-NAMESTRING STRING) ...)

(CL:DECLAIM
 (CL:FTYPE (CL:FUNCTION (CL:T CL:&REST CL:T) CL:SIMPLE-STRING)
  COMPOSE-NAMESTRING))
(CL:DEFUN COMPOSE-NAMESTRING (NAME-COMPONENTS CL:&REST OPTIONS)
  "`name-components' is a cons to be processed into a namestring.
':prefix' and ':suffix' are strings that will NOT be case-converted.
':case' is one of :UPCASE :TitleCase :titleCaseX :downcase :Capitalize
        default is :TitleCase
':separator' is a string that should separate word elements.  It does not
       separate the prefix or suffix.  Default is \"\"
':translation-table' should be a STRING-HASH-TABLE hash table that strings into their
       desired printed representation as a string.  In general the argument
       will be strings, but that is not strictly necessary.
"
  (CL:LET* ((SELF-000 (NEW-PROPERTY-LIST)))
   (CL:LET* ((ARGLIST-000 NIL))
    (CL:LET* ((ARG-000 NULL) (ITER-000 OPTIONS) (COLLECT-000 NULL))
     (CL:LOOP WHILE ITER-000 DO (CL:SETQ ARG-000 (CL:POP ITER-000))
      (CL:IF (CL:EQ COLLECT-000 NULL)
       (CL:PROGN (CL:SETQ COLLECT-000 (CONS ARG-000 NIL))
        (CL:IF (CL:EQ ARGLIST-000 NIL)
         (CL:SETQ ARGLIST-000 COLLECT-000)
         (ADD-CONS-TO-END-OF-CONS-LIST ARGLIST-000 COLLECT-000)))
       (CL:PROGN (CL:SETF (%%REST COLLECT-000) (CONS ARG-000 NIL))
        (CL:SETQ COLLECT-000 (%%REST COLLECT-000))))))
    (CL:SETF (%THE-PLIST SELF-000) ARGLIST-000))
   (CL:LET*
    ((PLIST SELF-000) (PREFIX "") (SUFFIX "")
     (OUTPUTCASE KWD-NAME-UTILITY-TITLECASE) (OUTPUTSEPARATOR "")
     (TRANSLATION-TABLE NULL) (USE-ACRONYM-HEURISTICS? CL:NIL))
    (CL:DECLARE
     (CL:TYPE CL:SIMPLE-STRING PREFIX SUFFIX OUTPUTSEPARATOR))
    (VET-OPTIONS PLIST
     (GET-QUOTED-TREE
      "((:PREFIX :SUFFIX :CASE :SEPARATOR :TRANSLATION-TABLE :USE-ACRONYM-HEURISTICS?) \"/STELLA\")"
      "/STELLA"))
    (CL:LET* ((KEY NULL) (VALUE NULL) (ITER-001 (%THE-PLIST PLIST)))
     (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-001 NIL)) DO
      (CL:SETQ KEY (%%VALUE ITER-001))
      (CL:SETQ VALUE (%%VALUE (%%REST ITER-001)))
      (CL:LET* ((TEST-VALUE-000 KEY))
       (CL:COND
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-PREFIX)
         (CL:SETQ PREFIX (%WRAPPER-VALUE VALUE)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-SUFFIX)
         (CL:SETQ SUFFIX (%WRAPPER-VALUE VALUE)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-CASE)
         (CL:SETQ OUTPUTCASE VALUE))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-SEPARATOR)
         (CL:SETQ OUTPUTSEPARATOR (%WRAPPER-VALUE VALUE)))
        ((CL:EQ TEST-VALUE-000 KWD-NAME-UTILITY-TRANSLATION-TABLE)
         (CL:SETQ TRANSLATION-TABLE VALUE))
        ((CL:EQ TEST-VALUE-000
          KWD-NAME-UTILITY-USE-ACRONYM-HEURISTICS?)
         (CL:SETQ USE-ACRONYM-HEURISTICS? (CL:EQ VALUE TRUE-WRAPPER)))
        (CL:T
         (CL:LET* ((STREAM-000 (NEW-OUTPUT-STRING-STREAM)))
          (%%PRINT-STREAM (%NATIVE-STREAM STREAM-000) "`"
           TEST-VALUE-000 "' is not a valid case option")
          (CL:ERROR
           (NEW-STELLA-EXCEPTION (THE-STRING-READER STREAM-000)))))))
      (CL:SETQ ITER-001 (%%REST (%%REST ITER-001)))))
    (CL:RETURN-FROM COMPOSE-NAMESTRING
     (COMPOSE-NAMESTRING-FULL NAME-COMPONENTS PREFIX SUFFIX OUTPUTCASE
      OUTPUTSEPARATOR TRANSLATION-TABLE USE-ACRONYM-HEURISTICS?)))))

;;; (DEFUN (MAKE-MATCHING-NAME-FULL STRING) ...)

(CL:DECLAIM
 (CL:FTYPE
  (CL:FUNCTION
   (CL:SIMPLE-STRING CL:T CL:T CL:SIMPLE-STRING CL:SIMPLE-STRING
    CL:SIMPLE-STRING CL:SIMPLE-STRING CL:SIMPLE-STRING CL:T
    CL:SIMPLE-STRING)
   CL:SIMPLE-STRING)
  MAKE-MATCHING-NAME-FULL))
(CL:DEFUN MAKE-MATCHING-NAME-FULL (ORIGINALNAME BREAKONCAP BREAKONNUMBER BREAKONSEPARATORS REMOVEPREFIX REMOVESUFFIX ADDPREFIX ADDSUFFIX OUTPUTCASE OUTPUTSEPARATOR)
  "Non-keyword version of `make-matching-name', which will probably be
easier to use when called from non-Lisp languages."
  (CL:DECLARE
   (CL:TYPE CL:SIMPLE-STRING ORIGINALNAME BREAKONSEPARATORS
    REMOVEPREFIX REMOVESUFFIX ADDPREFIX ADDSUFFIX OUTPUTSEPARATOR))
  #+MCL
  (CL:CHECK-TYPE ORIGINALNAME CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE BREAKONSEPARATORS CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE REMOVEPREFIX CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE REMOVESUFFIX CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE ADDPREFIX CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE ADDSUFFIX CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE OUTPUTSEPARATOR CL:SIMPLE-STRING)
  (CL:LET*
   ((PREFIXLENGTH (CL:THE CL:FIXNUM (CL:LENGTH REMOVEPREFIX)))
    (SUFFIXLENGTH (CL:THE CL:FIXNUM (CL:LENGTH REMOVESUFFIX)))
    (RESULT-STRING ORIGINALNAME) (RESULT-LENGTH 0))
   (CL:DECLARE
    (CL:TYPE CL:FIXNUM PREFIXLENGTH SUFFIXLENGTH RESULT-LENGTH)
    (CL:TYPE CL:SIMPLE-STRING RESULT-STRING))
   (CL:WHEN
    (CL:AND (CL:> PREFIXLENGTH 0)
     (CL:<= PREFIXLENGTH (CL:THE CL:FIXNUM (CL:LENGTH ORIGINALNAME)))
     (STRING-EQL? REMOVEPREFIX
      (SUBSEQUENCE ORIGINALNAME 0 PREFIXLENGTH)))
    (CL:SETQ RESULT-STRING
     (SUBSEQUENCE ORIGINALNAME PREFIXLENGTH NULL-INTEGER)))
   (CL:SETQ RESULT-LENGTH (CL:THE CL:FIXNUM (CL:LENGTH RESULT-STRING)))
   (CL:WHEN
    (CL:AND (CL:> SUFFIXLENGTH 0) (CL:<= SUFFIXLENGTH RESULT-LENGTH)
     (STRING-EQL? REMOVESUFFIX
      (SUBSEQUENCE RESULT-STRING (CL:- RESULT-LENGTH SUFFIXLENGTH)
       RESULT-LENGTH)))
    (CL:SETQ RESULT-STRING
     (SUBSEQUENCE RESULT-STRING 0 (CL:- RESULT-LENGTH SUFFIXLENGTH))))
   (CL:WHEN (STRING-EQL? RESULT-STRING "")
    (CL:SETQ RESULT-STRING ORIGINALNAME))
   (CL:SETQ RESULT-STRING
    (COMPOSE-NAMESTRING-FULL
     (DECOMPOSE-NAMESTRING-FULL RESULT-STRING BREAKONCAP BREAKONNUMBER
      BREAKONSEPARATORS)
     ADDPREFIX ADDSUFFIX OUTPUTCASE OUTPUTSEPARATOR NULL CL:NIL))
   (CL:IF (STRING-EQL? RESULT-STRING "")
    (CL:RETURN-FROM MAKE-MATCHING-NAME-FULL ORIGINALNAME)
    (CL:RETURN-FROM MAKE-MATCHING-NAME-FULL RESULT-STRING))))

;;; (DEFUN (DECOMPOSE-NAMESTRING-FULL (CONS OF STRING-WRAPPER)) ...)

(CL:DEFUN DECOMPOSE-NAMESTRING-FULL (NAMESTRING BREAK-ON-CAP BREAK-ON-NUMBER BREAK-ON-SEPARATORS)
  "Non-keyword version of `decompose-namestring', which will probably be
easier to use when called from non-Lisp languages."
  (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING NAMESTRING BREAK-ON-SEPARATORS))
  #+MCL
  (CL:CHECK-TYPE NAMESTRING CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE BREAK-ON-SEPARATORS CL:SIMPLE-STRING)
  (CL:LET*
   ((LEN (CL:THE CL:FIXNUM (CL:LENGTH NAMESTRING))) (RESULT NIL)
    (LAG 0) (LEAD 0) (INCAPRUN? CL:NIL) (INNUMBER? CL:NIL))
   (CL:DECLARE (CL:TYPE CL:FIXNUM LEN LAG LEAD))
   (CL:LET*
    ((C NULL-CHARACTER) (VECTOR-000 NAMESTRING) (INDEX-000 0)
     (LENGTH-000 (CL:THE CL:FIXNUM (CL:LENGTH VECTOR-000))))
    (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING VECTOR-000)
     (CL:TYPE CL:FIXNUM INDEX-000 LENGTH-000))
    (CL:LOOP WHILE (CL:< INDEX-000 LENGTH-000) DO
     (CL:SETQ C
      (CL:LET ((SELF VECTOR-000) (POSITION INDEX-000))
       (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING SELF)
        (CL:TYPE CL:FIXNUM POSITION))
       (CL:SCHAR (CL:THE CL:SIMPLE-STRING SELF)
        (CL:THE CL:FIXNUM POSITION))))
     (CL:LET* ((FOUND?-000 CL:NIL))
      (CL:LET*
       ((SEP NULL-CHARACTER) (VECTOR-001 BREAK-ON-SEPARATORS)
        (INDEX-001 0)
        (LENGTH-001 (CL:THE CL:FIXNUM (CL:LENGTH VECTOR-001))))
       (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING VECTOR-001)
        (CL:TYPE CL:FIXNUM INDEX-001 LENGTH-001))
       (CL:LOOP WHILE (CL:< INDEX-001 LENGTH-001) DO
        (CL:SETQ SEP
         (CL:LET ((SELF VECTOR-001) (POSITION INDEX-001))
          (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING SELF)
           (CL:TYPE CL:FIXNUM POSITION))
          (CL:SCHAR (CL:THE CL:SIMPLE-STRING SELF)
           (CL:THE CL:FIXNUM POSITION))))
        (CL:WHEN (CL:EQL SEP C) (CL:SETQ FOUND?-000 CL:T) (CL:RETURN))
        (CL:SETQ INDEX-001 (CL:1+ INDEX-001))))
      (CL:IF FOUND?-000
       (CL:PROGN
        (CL:SETQ RESULT
         (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG LEAD)) RESULT))
        (CL:SETQ LAG (CL:1+ LEAD)) (CL:SETQ INNUMBER? CL:NIL)
        (CL:SETQ INCAPRUN? CL:NIL))
       (CL:IF (CL:> LAG LEAD) (CL:PROGN)
        (CL:IF
         (CL:EQ
          (CL:AREF *CHARACTER-TYPE-TABLE*
           (CL:THE CL:FIXNUM (CL:CHAR-CODE C)))
          KWD-NAME-UTILITY-DIGIT)
         (CL:PROGN
          (CL:COND
           ((CL:AND (CL:NOT INNUMBER?)
             (CL:NOT (CL:EQ BREAK-ON-NUMBER KWD-NAME-UTILITY-NO)))
            (CL:WHEN (CL:NOT (CL:= LEAD LAG))
             (CL:SETQ RESULT
              (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG LEAD))
               RESULT))
             (CL:SETQ LAG LEAD)))
           (CL:T))
          (CL:SETQ INCAPRUN? CL:NIL) (CL:SETQ INNUMBER? CL:T))
         (CL:IF (LOWER-CASE-CHARACTER? C)
          (CL:PROGN
           (CL:WHEN
            (CL:AND INNUMBER?
             (CL:NOT (CL:EQ BREAK-ON-NUMBER KWD-NAME-UTILITY-NO)))
            (CL:COND ((CL:= LEAD LAG))
             ((CL:NOT (CL:EQ BREAK-ON-NUMBER KWD-NAME-UTILITY-CLEVER))
              (CL:SETQ RESULT
               (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG LEAD))
                RESULT))
              (CL:SETQ LAG LEAD))
             ((CL:AND (CL:< LEAD (CL:1- LEN))
               (ORDINAL-NUMBER-STRING?
                (SUBSEQUENCE NAMESTRING LAG (CL:+ LEAD 2))))
              (CL:SETQ RESULT
               (CONS
                (WRAP-STRING
                 (SUBSEQUENCE NAMESTRING LAG (CL:+ LEAD 2)))
                RESULT))
              (CL:SETQ LAG (CL:+ LEAD 2)))
             (CL:T
              (CL:SETQ RESULT
               (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG LEAD))
                RESULT))
              (CL:SETQ LAG LEAD))))
           (CL:COND ((CL:> LAG LEAD))
            ((CL:EQ BREAK-ON-CAP KWD-NAME-UTILITY-NO))
            ((CL:NOT (CL:EQ BREAK-ON-CAP KWD-NAME-UTILITY-CLEVER)))
            (INCAPRUN?
             (CL:WHEN (CL:NOT (CL:= LEAD (CL:1+ LAG)))
              (CL:SETQ RESULT
               (CONS
                (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG (CL:1- LEAD)))
                RESULT))
              (CL:SETQ LAG (CL:1- LEAD)))))
           (CL:SETQ INNUMBER? CL:NIL) (CL:SETQ INCAPRUN? CL:NIL))
          (CL:WHEN (UPPER-CASE-CHARACTER? C)
           (CL:WHEN
            (CL:AND INNUMBER?
             (CL:NOT (CL:EQ BREAK-ON-NUMBER KWD-NAME-UTILITY-NO)))
            (CL:COND ((CL:= LEAD LAG))
             ((CL:NOT (CL:EQ BREAK-ON-NUMBER KWD-NAME-UTILITY-CLEVER))
              (CL:SETQ RESULT
               (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG LEAD))
                RESULT))
              (CL:SETQ LAG LEAD))
             ((CL:AND (CL:< LEAD (CL:1- LEN))
               (ORDINAL-NUMBER-STRING?
                (SUBSEQUENCE NAMESTRING LAG (CL:+ LEAD 2))))
              (CL:SETQ RESULT
               (CONS
                (WRAP-STRING
                 (SUBSEQUENCE NAMESTRING LAG (CL:+ LEAD 2)))
                RESULT))
              (CL:SETQ LAG (CL:+ LEAD 2)))
             (CL:T
              (CL:SETQ RESULT
               (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG LEAD))
                RESULT))
              (CL:SETQ LAG LEAD))))
           (CL:COND ((CL:> LAG LEAD))
            ((CL:EQ BREAK-ON-CAP KWD-NAME-UTILITY-NO))
            ((CL:NOT (CL:EQ BREAK-ON-CAP KWD-NAME-UTILITY-CLEVER))
             (CL:WHEN (CL:NOT (CL:= LEAD LAG))
              (CL:SETQ RESULT
               (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG LEAD))
                RESULT))
              (CL:SETQ LAG LEAD)))
            (INCAPRUN?)
            (CL:T
             (CL:WHEN (CL:NOT (CL:= LEAD LAG))
              (CL:SETQ RESULT
               (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG LEAD))
                RESULT))
              (CL:SETQ LAG LEAD))
             (CL:SETQ INCAPRUN? CL:T)))
           (CL:SETQ INNUMBER? CL:NIL)))))))
     (CL:SETQ LEAD (CL:1+ LEAD))
     (CL:SETQ INDEX-000 (CL:1+ INDEX-000))))
   (CL:WHEN (CL:>= LEAD LAG)
    (CL:SETQ RESULT
     (CONS (WRAP-STRING (SUBSEQUENCE NAMESTRING LAG NULL-INTEGER))
      RESULT)))
   (CL:RETURN-FROM DECOMPOSE-NAMESTRING-FULL (REVERSE RESULT))))

;;; (DEFUN (SUFFIX-MATCHES? BOOLEAN) ...)

(CL:DEFUN SUFFIX-MATCHES? (TESTSTRING SUFFIX)
  (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING TESTSTRING SUFFIX))
  #+MCL
  (CL:CHECK-TYPE TESTSTRING CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE SUFFIX CL:SIMPLE-STRING)
  (CL:LET*
   ((STRINGLENGTH (CL:THE CL:FIXNUM (CL:LENGTH TESTSTRING)))
    (SUFFIXLENGTH (CL:THE CL:FIXNUM (CL:LENGTH SUFFIX))))
   (CL:DECLARE (CL:TYPE CL:FIXNUM STRINGLENGTH SUFFIXLENGTH))
   (CL:RETURN-FROM SUFFIX-MATCHES?
    (CL:AND (CL:<= SUFFIXLENGTH STRINGLENGTH)
     (STRING-EQL? SUFFIX
      (SUBSEQUENCE TESTSTRING (CL:- STRINGLENGTH SUFFIXLENGTH)
       NULL-INTEGER))))))

;;; (DEFUN (ORDINAL-NUMBER-STRING? BOOLEAN) ...)

(CL:DEFUN ORDINAL-NUMBER-STRING? (TESTSTRING)
  (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING TESTSTRING))
  #+MCL
  (CL:CHECK-TYPE TESTSTRING CL:SIMPLE-STRING)
  (CL:LET*
   ((LEN (CL:THE CL:FIXNUM (CL:LENGTH TESTSTRING)))
    (TEEN?
     (CL:AND (CL:> LEN 3)
      (CL:EQL #\1
       (CL:LET ((SELF TESTSTRING) (POSITION (CL:- LEN 4)))
        (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING SELF)
         (CL:TYPE CL:FIXNUM POSITION))
        (CL:SCHAR (CL:THE CL:SIMPLE-STRING SELF)
         (CL:THE CL:FIXNUM POSITION))))))
    (SUFFIX "th"))
   (CL:DECLARE (CL:TYPE CL:FIXNUM LEN)
    (CL:TYPE CL:SIMPLE-STRING SUFFIX))
   (CL:WHEN (CL:< LEN 3)
    (CL:RETURN-FROM ORDINAL-NUMBER-STRING? CL:NIL))
   (CL:LET*
    ((C NULL-CHARACTER) (VECTOR-000 TESTSTRING) (INDEX-000 0)
     (LENGTH-000 (CL:THE CL:FIXNUM (CL:LENGTH VECTOR-000)))
     (I NULL-INTEGER) (ITER-000 0) (UPPER-BOUND-000 (CL:- LEN 3)))
    (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING VECTOR-000)
     (CL:TYPE CL:FIXNUM INDEX-000 LENGTH-000 I ITER-000
      UPPER-BOUND-000))
    (CL:LOOP WHILE
     (CL:AND (CL:< INDEX-000 LENGTH-000)
      (CL:<= ITER-000 UPPER-BOUND-000))
     DO
     (CL:SETQ C
      (CL:LET ((SELF VECTOR-000) (POSITION INDEX-000))
       (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING SELF)
        (CL:TYPE CL:FIXNUM POSITION))
       (CL:SCHAR (CL:THE CL:SIMPLE-STRING SELF)
        (CL:THE CL:FIXNUM POSITION))))
     (CL:SETQ I ITER-000) (CL:SETQ I I)
     (CL:WHEN
      (CL:NOT
       (CL:EQ
        (CL:AREF *CHARACTER-TYPE-TABLE*
         (CL:THE CL:FIXNUM (CL:CHAR-CODE C)))
        KWD-NAME-UTILITY-DIGIT))
      (CL:RETURN-FROM ORDINAL-NUMBER-STRING? CL:NIL))
     (CL:SETQ INDEX-000 (CL:1+ INDEX-000))
     (CL:SETQ ITER-000 (CL:1+ ITER-000))))
   (CL:WHEN (CL:NOT TEEN?)
    (CL:CASE
     (CL:LET ((SELF TESTSTRING) (POSITION (CL:- LEN 3)))
      (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING SELF)
       (CL:TYPE CL:FIXNUM POSITION))
      (CL:SCHAR (CL:THE CL:SIMPLE-STRING SELF)
       (CL:THE CL:FIXNUM POSITION)))
     (#\1 (CL:SETQ SUFFIX "st")) (#\2 (CL:SETQ SUFFIX "nd"))
     (#\3 (CL:SETQ SUFFIX "rd")) (CL:OTHERWISE)))
   (CL:RETURN-FROM ORDINAL-NUMBER-STRING?
    (SUFFIX-MATCHES? TESTSTRING SUFFIX))))

;;; (DEFUN (HEURISTIC-ACRONYM? BOOLEAN) ...)

(CL:DEFUN HEURISTIC-ACRONYM? (ITEMSTRING)
  (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING ITEMSTRING))
  #+MCL
  (CL:CHECK-TYPE ITEMSTRING CL:SIMPLE-STRING)
  (CL:LET* ((LETTERFOUND? CL:NIL) (NUMBERFOUND? CL:NIL))
   (CL:LET*
    ((C NULL-CHARACTER) (VECTOR-000 ITEMSTRING) (INDEX-000 0)
     (LENGTH-000 (CL:THE CL:FIXNUM (CL:LENGTH VECTOR-000))))
    (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING VECTOR-000)
     (CL:TYPE CL:FIXNUM INDEX-000 LENGTH-000))
    (CL:LOOP WHILE (CL:< INDEX-000 LENGTH-000) DO
     (CL:SETQ C
      (CL:LET ((SELF VECTOR-000) (POSITION INDEX-000))
       (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING SELF)
        (CL:TYPE CL:FIXNUM POSITION))
       (CL:SCHAR (CL:THE CL:SIMPLE-STRING SELF)
        (CL:THE CL:FIXNUM POSITION))))
     (CL:COND
      ((CL:EQ
        (CL:AREF *CHARACTER-TYPE-TABLE*
         (CL:THE CL:FIXNUM (CL:CHAR-CODE C)))
        KWD-NAME-UTILITY-DIGIT)
       (CL:SETQ NUMBERFOUND? CL:T))
      ((CL:OR (LOWER-CASE-CHARACTER? C) (UPPER-CASE-CHARACTER? C))
       (CL:SETQ LETTERFOUND? CL:T))
      ((MEMBER?
        (GET-QUOTED-TREE "((#\\. #\\- #\\/) \"/STELLA\")" "/STELLA")
        (WRAP-CHARACTER C))
       (CL:SETQ NUMBERFOUND? CL:T))
      (CL:T (CL:RETURN-FROM HEURISTIC-ACRONYM? CL:NIL)))
     (CL:SETQ INDEX-000 (CL:1+ INDEX-000))))
   (CL:RETURN-FROM HEURISTIC-ACRONYM?
    (CL:AND NUMBERFOUND? LETTERFOUND?
     (CL:NOT (ORDINAL-NUMBER-STRING? ITEMSTRING))))))

;;; (DEFUN (COMPOSE-NAMESTRING-FULL STRING) ...)

(CL:DECLAIM
 (CL:FTYPE
  (CL:FUNCTION
   (CL:T CL:SIMPLE-STRING CL:SIMPLE-STRING CL:T CL:SIMPLE-STRING CL:T
    CL:T)
   CL:SIMPLE-STRING)
  COMPOSE-NAMESTRING-FULL))
(CL:DEFUN COMPOSE-NAMESTRING-FULL (STRINGS PREFIX SUFFIX OUTPUTCASE OUTPUTSEPARATOR TRANSLATIONTABLE USEACRONYMHEURISTICS?)
  "Non-keyword version of `compose-namestring', which will probably be
easier to use when called from non-Lisp languages."
  (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING PREFIX SUFFIX OUTPUTSEPARATOR))
  #+MCL
  (CL:CHECK-TYPE PREFIX CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE SUFFIX CL:SIMPLE-STRING)
  #+MCL
  (CL:CHECK-TYPE OUTPUTSEPARATOR CL:SIMPLE-STRING)
  (CL:LET*
   ((N 0) (I 0) (OUT STELLA::NULL-STRING)
    (SEPARATOR-LENGTH
     (CL:IF (CL:NOT (CL:EQ OUTPUTSEPARATOR STELLA::NULL-STRING))
      (CL:THE CL:FIXNUM (CL:LENGTH OUTPUTSEPARATOR)) 0))
    (FIRSTTIME? CL:T) (S STELLA::NULL-STRING) (S-LEN 0))
   (CL:DECLARE (CL:TYPE CL:FIXNUM N I SEPARATOR-LENGTH S-LEN)
    (CL:TYPE CL:SIMPLE-STRING OUT S))
   (CL:WHEN (CL:NOT (CL:EQ TRANSLATIONTABLE NULL))
    (CL:LET* ((TEMP STRINGS)) (CL:SETQ STRINGS NIL)
     (CL:LET* ((SW NULL) (ITER-000 TEMP) (COLLECT-000 NULL))
      (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-000 NIL)) DO
       (CL:SETQ SW (%%VALUE ITER-000))
       (CL:WHEN
        (CL:NOT
         (CL:EQ (LOOKUP TRANSLATIONTABLE (%WRAPPER-VALUE SW)) NULL))
        (CL:IF (CL:EQ COLLECT-000 NULL)
         (CL:PROGN
          (CL:SETQ COLLECT-000
           (CONS (LOOKUP TRANSLATIONTABLE (%WRAPPER-VALUE SW)) NIL))
          (CL:IF (CL:EQ STRINGS NIL) (CL:SETQ STRINGS COLLECT-000)
           (ADD-CONS-TO-END-OF-CONS-LIST STRINGS COLLECT-000)))
         (CL:PROGN
          (CL:SETF (%%REST COLLECT-000)
           (CONS (LOOKUP TRANSLATIONTABLE (%WRAPPER-VALUE SW)) NIL))
          (CL:SETQ COLLECT-000 (%%REST COLLECT-000)))))
       (CL:SETQ ITER-000 (%%REST ITER-000))))))
   (CL:WHEN (CL:NOT (CL:EQ PREFIX STELLA::NULL-STRING))
    (CL:SETQ N (CL:+ N (CL:THE CL:FIXNUM (CL:LENGTH PREFIX)))))
   (CL:WHEN (CL:NOT (CL:EQ SUFFIX STELLA::NULL-STRING))
    (CL:SETQ N (CL:+ N (CL:THE CL:FIXNUM (CL:LENGTH SUFFIX)))))
   (CL:LET* ((SW NULL) (ITER-001 STRINGS))
    (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-001 NIL)) DO
     (CL:SETQ SW (%%VALUE ITER-001))
     (CL:SETQ N
      (CL:+ N
       (CL:THE CL:FIXNUM
        (CL:LENGTH (CL:THE CL:SIMPLE-STRING (%WRAPPER-VALUE SW))))))
     (CL:SETQ ITER-001 (%%REST ITER-001))))
   (CL:SETQ N
    (CL:+ N (CL:* (CL:1- (LENGTH STRINGS)) SEPARATOR-LENGTH)))
   (CL:SETQ OUT (MAKE-RAW-MUTABLE-STRING N))
   (CL:WHEN (CL:NOT (CL:EQ PREFIX STELLA::NULL-STRING))
    (CL:SETQ I
     (INSERT-STRING PREFIX 0 NULL-INTEGER OUT I
      KWD-NAME-UTILITY-PRESERVE)))
   (CL:LET* ((SW NULL) (ITER-002 STRINGS))
    (CL:LOOP WHILE (CL:NOT (CL:EQ ITER-002 NIL)) DO
     (CL:SETQ SW (%%VALUE ITER-002)) (CL:SETQ S (%WRAPPER-VALUE SW))
     (CL:SETQ S-LEN (CL:THE CL:FIXNUM (CL:LENGTH S)))
     (CL:WHEN (CL:NOT FIRSTTIME?)
      (CL:WHEN (CL:> SEPARATOR-LENGTH 0)
       (CL:SETQ I
        (INSERT-STRING OUTPUTSEPARATOR 0 (CL:1- SEPARATOR-LENGTH) OUT I
         KWD-NAME-UTILITY-PRESERVE))))
     (CL:COND ((CL:= S-LEN 0))
      ((CL:AND USEACRONYMHEURISTICS? (HEURISTIC-ACRONYM? S))
       (CL:SETQ I
        (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
         KWD-NAME-UTILITY-PRESERVE)))
      (CL:T
       (CL:COND
        ((CL:OR (CL:EQ OUTPUTCASE KWD-NAME-UTILITY-ALLCAPS)
          (CL:EQ OUTPUTCASE KWD-NAME-UTILITY-UPCASE))
         (CL:SETQ I
          (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
           KWD-NAME-UTILITY-UPCASE)))
        ((CL:EQ OUTPUTCASE KWD-NAME-UTILITY-DOWNCASE)
         (CL:SETQ I
          (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
           KWD-NAME-UTILITY-DOWNCASE)))
        ((CL:EQ OUTPUTCASE KWD-NAME-UTILITY-TITLECASE)
         (CL:SETQ I
          (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
           KWD-NAME-UTILITY-CAPITALIZE)))
        ((CL:EQ OUTPUTCASE KWD-NAME-UTILITY-TITLECASEX)
         (CL:IF FIRSTTIME?
          (CL:SETQ I
           (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
            KWD-NAME-UTILITY-DOWNCASE))
          (CL:SETQ I
           (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
            KWD-NAME-UTILITY-CAPITALIZE))))
        ((CL:EQ OUTPUTCASE KWD-NAME-UTILITY-CAPITALIZE)
         (CL:IF FIRSTTIME?
          (CL:SETQ I
           (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
            KWD-NAME-UTILITY-CAPITALIZE))
          (CL:SETQ I
           (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
            KWD-NAME-UTILITY-DOWNCASE))))
        ((CL:EQ OUTPUTCASE KWD-NAME-UTILITY-PRESERVE)
         (CL:SETQ I
          (INSERT-STRING S 0 (CL:1- S-LEN) OUT I
           KWD-NAME-UTILITY-PRESERVE)))
        (CL:T
         (CL:LET* ((STREAM-000 (NEW-OUTPUT-STRING-STREAM)))
          (%%PRINT-STREAM (%NATIVE-STREAM STREAM-000) "`" OUTPUTCASE
           "' is not a valid case option")
          (CL:ERROR
           (NEW-STELLA-EXCEPTION (THE-STRING-READER STREAM-000))))))))
     (CL:SETQ FIRSTTIME? CL:NIL) (CL:SETQ ITER-002 (%%REST ITER-002))))
   (CL:WHEN (CL:NOT (CL:EQ SUFFIX STELLA::NULL-STRING))
    (CL:SETQ I
     (INSERT-STRING SUFFIX 0 NULL-INTEGER OUT I
      KWD-NAME-UTILITY-PRESERVE)))
   (CL:RETURN-FROM COMPOSE-NAMESTRING-FULL
    (CL:LET ((S OUT)) (CL:DECLARE (CL:TYPE CL:SIMPLE-STRING S))
     (CL:THE CL:SIMPLE-STRING S)))))

(CL:DEFUN STARTUP-NAME-UTILITY ()
  (CL:LET* ((*MODULE* *STELLA-MODULE*) (*CONTEXT* *MODULE*))
   (CL:DECLARE (CL:SPECIAL *MODULE* *CONTEXT*))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 2)
    (CL:SETQ KWD-NAME-UTILITY-CLEVER
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CLEVER" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-TITLECASE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "TITLECASE" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-BREAK-ON-CAP
     (INTERN-RIGID-SYMBOL-WRT-MODULE "BREAK-ON-CAP" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-NO
     (INTERN-RIGID-SYMBOL-WRT-MODULE "NO" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-BREAK-ON-NUMBER
     (INTERN-RIGID-SYMBOL-WRT-MODULE "BREAK-ON-NUMBER" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-BREAK-ON-SEPARATORS
     (INTERN-RIGID-SYMBOL-WRT-MODULE "BREAK-ON-SEPARATORS" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-REMOVE-PREFIX
     (INTERN-RIGID-SYMBOL-WRT-MODULE "REMOVE-PREFIX" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-REMOVE-SUFFIX
     (INTERN-RIGID-SYMBOL-WRT-MODULE "REMOVE-SUFFIX" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-ADD-PREFIX
     (INTERN-RIGID-SYMBOL-WRT-MODULE "ADD-PREFIX" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-ADD-SUFFIX
     (INTERN-RIGID-SYMBOL-WRT-MODULE "ADD-SUFFIX" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-CASE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CASE" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-SEPARATOR
     (INTERN-RIGID-SYMBOL-WRT-MODULE "SEPARATOR" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-PREFIX
     (INTERN-RIGID-SYMBOL-WRT-MODULE "PREFIX" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-SUFFIX
     (INTERN-RIGID-SYMBOL-WRT-MODULE "SUFFIX" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-TRANSLATION-TABLE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "TRANSLATION-TABLE" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-USE-ACRONYM-HEURISTICS?
     (INTERN-RIGID-SYMBOL-WRT-MODULE "USE-ACRONYM-HEURISTICS?" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-DIGIT
     (INTERN-RIGID-SYMBOL-WRT-MODULE "DIGIT" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-PRESERVE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "PRESERVE" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-ALLCAPS
     (INTERN-RIGID-SYMBOL-WRT-MODULE "ALLCAPS" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-UPCASE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "UPCASE" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-DOWNCASE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "DOWNCASE" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-CAPITALIZE
     (INTERN-RIGID-SYMBOL-WRT-MODULE "CAPITALIZE" NULL 2))
    (CL:SETQ KWD-NAME-UTILITY-TITLECASEX
     (INTERN-RIGID-SYMBOL-WRT-MODULE "TITLECASEX" NULL 2))
    (CL:SETQ SYM-NAME-UTILITY-STELLA-STARTUP-NAME-UTILITY
     (INTERN-RIGID-SYMBOL-WRT-MODULE "STARTUP-NAME-UTILITY" NULL 0))
    (CL:SETQ SYM-NAME-UTILITY-STELLA-METHOD-STARTUP-CLASSNAME
     (INTERN-RIGID-SYMBOL-WRT-MODULE "METHOD-STARTUP-CLASSNAME" NULL
      0)))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 6) (FINALIZE-CLASSES))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 7)
    (DEFINE-FUNCTION-OBJECT "MAKE-MATCHING-NAME"
     "(DEFUN (MAKE-MATCHING-NAME STRING) ((ORIGINAL STRING) |&REST| (OPTIONS OBJECT)) :PUBLIC? TRUE :DOCUMENTATION \"Keyword options:
  :break-on-cap    one of  :YES :NO :CLEVER         default is :CLEVER
  :break-on-number one of  :YES :NO :CLEVER         default is :CLEVER
  :break-on-separators string                       default is \\\"-_ \\\"
  :remove-prefix   string
  :remove-suffix   string
  
  :case            one of  :UPCASE :TitleCase :titleCaseX :downcase :Capitalize :preserve
                                                     default is :TitleCase
  :separator       string                            default is \\\"\\\"
  :add-prefix      string
  :add-suffix      string

  MAKE-MATCHING-NAME returns a matching name (a string) for the input name (a string).
A matching name is constructed by breaking the input into 'words' and then applying
appropriate transforms.  The arguments are used as follows:
  `original'         is the input name.  It is a string.
  :break-on-cap    is a keyword controlling whether changes in capitalization is used
                   to indicate word boundaries.  If :YES, then all capitalization
                   changes delineate words.  If :CLEVER, then unbroken runs of
                   capitalized letters are treated as acronyms and remain grouped.
                   If :NO or NULL, there is no breaking of words based on capitalization.
  :break-on-number is a flag controlling whether encountering a number indicates
                   a word boundary.  If :YES, then each run of numbers is treated as
		   a word separate from surrounding words.  If :CLEVER, then an 
		   attempt is made to recognize ordinal numbers (ie, 101st) and
		   treat them as separate words.  If :NO or NULL, there is no breaking
                   of words when numbers are encountered.
  :break-on-separators   A string of characters which constitute word delimiters in
                         the input word.  This is used to determine how to break
                   the name into individual words.  Defaults are space, '-' and '_'.
  :remove-prefix   Specifies a prefix or suffix that is stripped from the input
  :remove-suffix   name before any other processing.  This allows the removal of
                   any naming convention dictated prefixes or suffixes.
  :add-prefix      Specifies a prefix or suffix that is added to the output name
  :add-suffix      after all other processing.  This allows the addition of any
                   naming convention dictated prefixes or suffixes.
  :case            The case of the resulting name.  This is applied to the name 
                   before adding prefixes or suffixes.  The two title case options 
                   differ only in how the first word of the name is treated.
                   :TitleCase capitalizes the first letter of the first word and
                       also the first letter of all other words.
                   :TitleCaseX does not capitalizes the first letter of the first
		       word but capitalizes the first letter of all subsequent words.
		   :preserve results in no change in case.
  :separator       This is a string specifying the word separator to use in the
                   returned name.  An empty string (the default) means that the
                   resulting words are concatenated without any separation.  This
                   normally only makes sense when using one of the title case values
                   for the case keyword.\")"
     (CL:FUNCTION MAKE-MATCHING-NAME) NULL)
    (DEFINE-FUNCTION-OBJECT "DECOMPOSE-NAMESTRING"
     "(DEFUN (DECOMPOSE-NAMESTRING (CONS OF STRING-WRAPPER)) ((NAMESTRING STRING) |&REST| (OPTIONS OBJECT)) :DOCUMENTATION \"Keyword options:
  :break-on-cap    one of  :YES :NO :CLEVER         default is :CLEVER
  :break-on-number one of  :YES :NO :CLEVER         default is :CLEVER
  :break-on-separators string                       default is \\\"-_ \\\"

  DECOMPOSE-NAMESTRING returns a cons of STRING-WRAPPERS that are the decomposition of the
input STRING.  The arguments are used as follows:
  `namestring'       is the input string.
  :break-on-cap    is a keyword controlling whether changes in capitalization is used
                   to indicate word boundaries.  If :YES, then all capitalization
                   changes delineate words.  If :CLEVER, then unbroken runs of
                   capitalized letters are treated as acronyms and remain grouped.
                   If :NO or NULL, there is no breaking of words based on capitalization.
  :break-on-number is a flag controlling whether encountering a number indicates
                   a word boundary.  If :YES, then each run of numbers is treated as
		   a word separate from surrounding words.  If :CLEVER, then an 
		   attempt is made to recognize ordinal numbers (ie, 101st) and
		   treat them as separate words.  If :NO or NULL, there is no breaking
                   of words when numbers are encountered.
  :break-on-separators   A string of characters which constitute word delimiters in
                         the input word.  This is used to determine how to break
                   the name into individual words.  Defaults are space, '-' and '_'.\")"
     (CL:FUNCTION DECOMPOSE-NAMESTRING) NULL)
    (DEFINE-FUNCTION-OBJECT "COMPOSE-NAMESTRING"
     "(DEFUN (COMPOSE-NAMESTRING STRING) ((NAME-COMPONENTS (CONS OF STRING-WRAPPER)) |&REST| (OPTIONS OBJECT)) :PUBLIC? TRUE :DOCUMENTATION \"`name-components' is a cons to be processed into a namestring.
':prefix' and ':suffix' are strings that will NOT be case-converted.
':case' is one of :UPCASE :TitleCase :titleCaseX :downcase :Capitalize
        default is :TitleCase
':separator' is a string that should separate word elements.  It does not
       separate the prefix or suffix.  Default is \\\"\\\"
':translation-table' should be a STRING-HASH-TABLE hash table that strings into their
       desired printed representation as a string.  In general the argument
       will be strings, but that is not strictly necessary.
\")" (CL:FUNCTION COMPOSE-NAMESTRING) NULL)
    (DEFINE-FUNCTION-OBJECT "MAKE-MATCHING-NAME-FULL"
     "(DEFUN (MAKE-MATCHING-NAME-FULL STRING) ((ORIGINALNAME STRING) (BREAKONCAP KEYWORD) (BREAKONNUMBER KEYWORD) (BREAKONSEPARATORS STRING) (REMOVEPREFIX STRING) (REMOVESUFFIX STRING) (ADDPREFIX STRING) (ADDSUFFIX STRING) (OUTPUTCASE KEYWORD) (OUTPUTSEPARATOR STRING)) :PUBLIC? TRUE :DOCUMENTATION \"Non-keyword version of `make-matching-name', which will probably be
easier to use when called from non-Lisp languages.\")"
     (CL:FUNCTION MAKE-MATCHING-NAME-FULL) NULL)
    (DEFINE-FUNCTION-OBJECT "DECOMPOSE-NAMESTRING-FULL"
     "(DEFUN (DECOMPOSE-NAMESTRING-FULL (CONS OF STRING-WRAPPER)) ((NAMESTRING STRING) (BREAK-ON-CAP KEYWORD) (BREAK-ON-NUMBER KEYWORD) (BREAK-ON-SEPARATORS STRING)) :PUBLIC? TRUE :DOCUMENTATION \"Non-keyword version of `decompose-namestring', which will probably be
easier to use when called from non-Lisp languages.\")"
     (CL:FUNCTION DECOMPOSE-NAMESTRING-FULL) NULL)
    (DEFINE-FUNCTION-OBJECT "SUFFIX-MATCHES?"
     "(DEFUN (SUFFIX-MATCHES? BOOLEAN) ((TESTSTRING STRING) (SUFFIX STRING)))"
     (CL:FUNCTION SUFFIX-MATCHES?) NULL)
    (DEFINE-FUNCTION-OBJECT "ORDINAL-NUMBER-STRING?"
     "(DEFUN (ORDINAL-NUMBER-STRING? BOOLEAN) ((TESTSTRING STRING)))"
     (CL:FUNCTION ORDINAL-NUMBER-STRING?) NULL)
    (DEFINE-FUNCTION-OBJECT "HEURISTIC-ACRONYM?"
     "(DEFUN (HEURISTIC-ACRONYM? BOOLEAN) ((ITEMSTRING STRING)))"
     (CL:FUNCTION HEURISTIC-ACRONYM?) NULL)
    (DEFINE-FUNCTION-OBJECT "COMPOSE-NAMESTRING-FULL"
     "(DEFUN (COMPOSE-NAMESTRING-FULL STRING) ((STRINGS (CONS OF STRING-WRAPPER)) (PREFIX STRING) (SUFFIX STRING) (OUTPUTCASE KEYWORD) (OUTPUTSEPARATOR STRING) (TRANSLATIONTABLE STRING-HASH-TABLE) (USEACRONYMHEURISTICS? BOOLEAN)) :PUBLIC? TRUE :DOCUMENTATION \"Non-keyword version of `compose-namestring', which will probably be
easier to use when called from non-Lisp languages.\")"
     (CL:FUNCTION COMPOSE-NAMESTRING-FULL) NULL)
    (DEFINE-FUNCTION-OBJECT "STARTUP-NAME-UTILITY"
     "(DEFUN STARTUP-NAME-UTILITY () :PUBLIC? TRUE)"
     (CL:FUNCTION STARTUP-NAME-UTILITY) NULL)
    (CL:LET*
     ((FUNCTION
       (LOOKUP-FUNCTION SYM-NAME-UTILITY-STELLA-STARTUP-NAME-UTILITY)))
     (SET-DYNAMIC-SLOT-VALUE (%DYNAMIC-SLOTS FUNCTION)
      SYM-NAME-UTILITY-STELLA-METHOD-STARTUP-CLASSNAME
      (WRAP-STRING "_StartupNameUtility") NULL-STRING-WRAPPER)))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 8) (FINALIZE-SLOTS)
    (CLEANUP-UNFINALIZED-CLASSES))
   (CL:WHEN (CURRENT-STARTUP-TIME-PHASE? 9)
    (%IN-MODULE (COPY-CONS-TREE (WRAP-STRING "STELLA")))))
  :VOID)
