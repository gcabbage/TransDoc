# TLisp

Transcendence uses a [Lisp](https://en.wikipedia.org/wiki/Lisp_(programming_language))
variant known as TLisp for scripting. In Lisp both code and data are written using
symbolic expressions (sexps) in the form of lists of data, code (and other lists). As
a result Lisp code will contain a lot of parentheses, so it is highly recommended you
use an editor which highlights matching brackets.

TLisp scripts are formed of two basic components: atoms and lists. The atoms represent
numbers, strings, and functions; while lists are sequences of atoms and/or other lists
separated by spaces. For example, `(1 "two" 3)` is a list comprising three atoms: `1`,
`"two"`, and `3`.

Expressions are written as lists using prefix notation - where the first element in the
list is the name of a function. So to add three numbers together you would write:
```lisp
(+ 1 2 3)
```
which returns `6`

## Expressions and quoting

TLisp will evaluate every expression you give it, this means that typing `(+ 1 2 3)`
as above will immediately evaluate to `6`. Basic atoms (strings and numbers) will
evaluate to themselves e.g. `3.0`, `"string"`. However, the expression `(1 2 3)` is
not valid as TLisp will attempt to call a function named `1`. In order to create a
list you should use the `list` function for example:
```lisp
(list 1 2 3)
```
Alternatively you can use the special function `quote` which returns its argument
without evaluating it. You can also a single quotation mark as an abbreviation `'`:
```lisp
; The following both return a three element list (1 2 3):
(list 1 2 3)
(quote (1 2 3))
'(1 2 3)

; But note the difference between the following:
(+ 1 2 (+ 2 3))         ; 8
(list + 1 2 (+ 2 3))    ; ([function: +] 1 2 5)
'(+ 2 3 (+ 3 3))        ; (+ 1 2 (+ 2 3))
```

## Nil

In TLisp `Nil` is a special atom equivalent to an empty list `()`. These represent
the "false" state in any logical tests, with any other atom or non-empty list being
"true". This means all integers (including 0) and strings (including empty string)
are equivalent to "true".

`Nil` and empty list `()` are interchangeable and can be considered identical except
one specific case - if you perform an in-place list modification operation on a `Nil`
value it will return a new actual list, while in-place modification of an empty list
does not need to generate a new list

**NOTE** if you need to generate an empty list then use the `(list)` function as the
quote forms will return a Nil value

```lisp
; Evaluating an empty list is equivalent to function call.
()                      ; Returns Nil
Nil                     ; Returns Nil
(list)                  ; Returns ()

; quote forms return Nil
'()                     ; Returns Nil
(quote ())              ; Returns Nil
```

## Data types

* Atoms
  * Nil
  * True
  * Numeral
    * Integer
    * Real
  * String
  * Function
    * Primitive
    * Lambda
* Lists
