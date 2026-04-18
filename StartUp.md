# Running STELLA under SBCL — Step-by-Step

All paths in this document are relative to this directory (the STELLA project root — the directory containing this file, `load-stella.lisp`, `sources/`, `native/`, etc.).

Prerequisites:
- **SBCL** installed and on `PATH` (tested with 2.6.3, any recent version should work).
- Pre-translated Lisp sources (`.lisp` and `.slisp`) ship in `native/lisp/stella/`, so **no C++/Java toolchain is required** — SBCL compiles them on first load and caches the fasls.

This document is for running STELLA *by itself* (language + translator + REPL). If you only want PowerLoom, use the sibling `PowerLoom/` tree and its own `StartUp.md`; PowerLoom bundles its own copy of STELLA and does not need this directory.

---

## 1. Verify SBCL
```bash
sbcl --version        # any recent SBCL; 2.6.x confirmed working
```

## 2. Change to this directory
The loader uses `*load-truename*` to resolve its own pathnames, so start SBCL from the project root (or pass a full path to `load`).
```bash
cd <path-to>/Stella
```

## 3. Launch SBCL and load STELLA
```bash
sbcl --load load-stella.lisp
```

What happens on first load:
- `load-stella.lisp` sets `*load-cl-struct-stella?* = t` (faster struct-based STELLA, recommended) and applies SBCL-specific optimization settings (`speed 3 safety 1`).
- It `load`s `native/lisp/stella/load-stella.slisp`, which compiles the pre-translated STELLA sources into fasls under `native/lisp/bin/<sbcl-version>/…`. **First run takes a minute or two; subsequent runs load the cached fasls in seconds.**
- It registers the `ST` logical host pointing back at this directory (used for `ST:…` pathnames inside STELLA).

When loading finishes you will see:
```
STELLA <version> loaded.
Type `(in-package "STELLA")' to execute STELLA commands.
```

## 4. Enter the STELLA package
```lisp
(in-package "STELLA")
```
You're now driving STELLA from the SBCL REPL. The `STELLA` package does **not** inherit from `COMMON-LISP`; prefix CL symbols with `CL:` (e.g. `CL:*` for the previous result, `CL:load` for Lisp's `load`).

## 5. Try something
```lisp
(make-system "hello-world" :common-lisp)   ; translate + compile + load the hello-world example
(describe 'cons)                           ; STELLA introspection
```

## 6. (Optional) Regenerate the translation from `.ste` sources
STELLA is self-hosting; once it's loaded you can re-translate the entire language from `sources/stella/*.ste`:
```lisp
(translate-system "stella" :common-lisp
                  :force-translation? t
                  :recursive? t
                  :production-settings? t)
```
Other targets follow the same pattern with `:cpp`, `:java`, or `:idl` in place of `:common-lisp`, though those require the respective toolchains.

## 7. Exit
From the `STELLA(…):` prompt:
```lisp
(CL:exit)           ; or Ctrl-D
```
If you switched back to `CL-USER` (`(CL:in-package "CL-USER")`), use `(sb-ext:exit)` or Ctrl-D.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `File not found: …native/lisp/stella/load-stella.slisp` | You launched SBCL from the wrong directory. `cd` into this project directory first (the loader resolves paths from `*load-truename*`). |
| Compile warnings / style-warnings during first load | Expected — the translated code is aggressive. Non-fatal; loading continues. |
| Slow startup every time | You are recompiling. Confirm `native/lisp/bin/<sbcl-version>/` is being populated and is writable. |
| Class redefinition errors after editing `.ste` files | Set `*load-cl-struct-stella?*` to `nil` in `load-stella.lisp` to use the CLOS backend (slower but tolerant of redefinition). |
| Want verbose compile output | Remove or comment out the `(setq *compile-verbose* nil *compile-print* nil)` block in `load-stella.lisp`. |

---

## Quick reference — minimal cold-start

```bash
cd <path-to>/Stella
sbcl --load load-stella.lisp
```
then at the `*` prompt:
```lisp
(in-package "STELLA")
```
