---
layout: post
title: "Why Minus Twelve?"
date: 2026-08-01
description: "A colleague sent me a decompiled length check in 2019 asking why it read twelve bytes backwards. Four years later the answer turned out to be statically linked Boost, welding a 2010 std::string layout permanently into the binary."
tags: [reverse-engineering, low-level-systems, compatibility, c-plus-plus, abi]
toc: true
---


In 2019 a colleague sent me a note that ended with "help please =/". He'd been
picking at a crash in a 2010-era commercial Linux app, 32-bit, that wouldn't run
on anything modern, and he'd gotten deep enough to find something that made no
sense to either of us.

It sat for four years. I picked it back up in 2023 on parental leave, mostly
because it had been bugging me, and that's when it finally came apart. This is
that.

## The note

He was looking at a Boost path constructor, decompiled, and it opened with this:

```c
if ( !*(_DWORD *)(*(_DWORD *)str_path2 - 12) )
    // allocate and throw a runtime_error
```

He'd checked it against the Boost source, so he knew what it meant: if the path
you handed it is empty, throw. Fine. Except it was throwing for `"."`, which is
one character.

His note, which I've kept for six years:

> "why minus 12? for some reason `str_path2` points to the inlined c-string and
> all `std::string` metadata (length, capacity, allocator) is BEFORE that
> pointer. I created some minimal examples and I always got a memory layout of
> allocator, length, inline data for strings with length < 15."

The whole problem is sitting right there in the open and neither of us saw it.
He wrote minimal examples, compiled them, checked the layout, and got a
different answer than the disassembly showed. His conclusion was that either
Boost was doing something inscrutable or libstdc++ was being libstdc++, which,
having read that header, is not an unreasonable place to land.

## The obvious theory, which is wrong

The story you'll hear about binaries like this, assuming you attend the kind of
parties where this comes up, is that libstdc++ removed the copy constructor
`_ZNSsC1EjcRKSaIcE` and replaced it with `_ZNSsC2EjcRKSaIcE`, so the imports
stopped resolving.

That's not what happened. `C1` and `C2` aren't versions of each other. The
Itanium C++ ABI §5.1.4.3 defines a family:

```
<ctor-dtor-name> ::= C1   # complete object constructor
                 ::= C2   # base object constructor
                 ::= C3   # complete object allocating constructor
                 ::= D0   # deleting destructor
                 ::= D1   # complete object destructor
                 ::= D2   # base object destructor
```

Virtual inheritance splits construction in two... a complete object constructs
its virtual bases, the same class used as a base subobject doesn't, because the
most-derived constructor already did. Hence two bodies. For a class with no
virtual bases, which `std::string` is, they're identical, and the spec says so
in the next line: *"Some of the symbols for constructor and destructor variants
are optional."*

I checked a shipping library rather than take that on faith (LOL). Debian trixie,
`libstdc++.so.6.0.33`, GCC 15:

```
00000000000f8a30 W _ZNSsC1EmcRKSaIcE@@GLIBCXX_3.4
00000000000f8a30 W _ZNSsC2EmcRKSaIcE@@GLIBCXX_3.4
```

Same address, both exported, both still tagged `GLIBCXX_3.4`, which is the label
from GCC 3.4 in 2004. 210 old copy-on-write string symbols are still exported by
a current libstdc++, all fifteen `_Rep` internals included, the refcount
machinery itself. libstdc++'s ABI policy lists "Deleting an exported symbol" as
prohibited, and promises binaries linked against an old release keep running
against new ones.

So I built a 32-bit program with `-D_GLIBCXX_USE_CXX11_ABI=0`, importing
`_ZNSsC1EjcRKSaIcE@GLIBCXX_3.4` and three friends, and linked it against GCC
15's libstdc++. Runs fine. The old ABI is still there and still serviced.

There's a real thing buried in the folk version though. The C1 and C2 aliases
don't always ship together or carry the same version tag:

```
_ZNSsC1EOSs@@GLIBCXX_3.4.14     # GCC 4.5
_ZNSsC2EOSs@@GLIBCXX_3.4.15     # GCC 4.6
```

One function, two entry points, exported a release apart. Which variants an
explicit instantiation emits has moved around across GCC versions, and that does
produce link-time surprises. It doesn't freeze a binary.

## What the old string actually was

Copy-on-write `std::string` is one pointer. That's the entire object. It points
at character data, and the bookkeeping sits immediately BEFORE that data:

```
        ┌──────────┬──────────┬──────────┬─────────────────────┐
_Rep →  │ length   │ capacity │ refcount │ "hello\0"           │
        └──────────┴──────────┴──────────┴─────────────────────┘
                                          ▲
                                          │
                             std::string ─┘   (one pointer, that's it)
```

`sizeof(std::string)`, measured:

| | 32-bit | 64-bit |
|---|---|---|
| COW (`_GLIBCXX_USE_CXX11_ABI=0`) | 4 | 8 |
| SSO (default, GCC 5+) | 24 | 32 |

In 1998 that was a good design. Copying a string was a pointer copy and an
increment, so passing by value cost nothing, which mattered a lot in a language
that wouldn't get move semantics for another thirteen years. Four bytes of
refcount bought all of it.

Threads killed it. Every copy touches a shared refcount, so every copy is an
atomic, and by the mid-2000s that cost more than just copying the sixteen-odd
bytes most strings actually contain. Then C++11 finished it: operations on
distinct string objects mustn't race, `operator[]` and `begin()` mustn't
invalidate, `c_str()` must be O(1) and non-mutating. Copy-on-write can't do
those, because a read through a shared buffer might have to unshare first. It
wasn't just slow by then, it was non-conforming.

The replacement is a 24-or-32-byte struct: pointer, length, and a union of
capacity with a small inline buffer. Up to 15 characters live inside the object.
No allocation, no refcount, no sharing.

You can't translate between those at a boundary. It isn't a representation
difference you can shim, it's semantic... in one model a copy shares a buffer,
in the other it copies. No glue makes a 4-byte handle and a 24-byte value the
same thing.

GCC 5.1 shipped both and let `_GLIBCXX_USE_CXX11_ABI` pick. The new one lives in
an inline namespace, which is why you see `std::__cxx11` in mangled names, and
that was the smart part... the break was engineered to fail at link time. Mix
the two and you get an unresolved symbol, not a corrupted struct at runtime. The
quieter drift of the 4.x era had nothing like that.

## Minus twelve

Here's the header, from `libstdc++-v3/include/bits/basic_string.h`, unchanged
from at least GCC 4.4.2 through 4.9.0:

```cpp
struct _Rep_base
{
  size_type       _M_length;
  size_type       _M_capacity;
  _Atomic_word    _M_refcount;
};
```

and the data pointer comes from `_M_refdata()`, which is a very polite name for
`reinterpret_cast<_CharT*>(this + 1)`. One whole `_Rep` past the header. Three
4-byte fields on a 32-bit target. Twelve. `_M_length` first, so it lands at
exactly `data - 12`.

The minus twelve isn't inscrutable. It's an ordinary inlined `empty()` check,
compiled in 2010, and it's correct.

I confirmed it on a 32-bit COW build of `std::string s(".")`:

```
COW  len=1  sizeof=4  *(data-12)=1  *(data-8)=1  *(data-4)=-1
```

Length 1, capacity 1, refcount −1, the sentinel for a string that can't be
shared. Every field exactly where the disassembly reaches for it.

Same `"."` under the modern layout:

```
SSO  len=1  sizeof=24  data-inside-object=1  *(data-12)=20
```

No header. Short string, so the characters live INSIDE the object at offset +8,
which puts `data - 12` at offset −4. Four bytes before the string even begins,
in whatever happened to be sitting there. That run it was 20. Could be anything.
When it's zero, a one-character path is empty and something throws.

Every symbol resolved. Control transferred correctly, arguments passed
correctly. The program read twelve bytes back from a pointer, into memory that
had stopped meaning what it used to mean, got a number, and believed it.

That's also why hooking the one function and forwarding it got him past exactly
one failure. Every string crossing that boundary carries the same disagreement,
so there's no single call to fix... which is most of why it stayed unsolved for
four years, because it doesn't present as an ABI problem. It presents as an
unrelated bug, and then another one.

## Where the static linking comes in

None of this traps a binary on its own. `_GLIBCXX_USE_CXX11_ABI=0` gets you the
old string, leave it off and you get the new one. It's a build flag.

Unless you can't rebuild the thing that set it.

This binary statically links Boost. Three components, and it's always these
three: filesystem, regex, chrono. Boost is mostly templates, so "linking" means
Boost's instantiations were compiled against the libstdc++ of the day and
inlined straight into the executable. The code that builds a `_Rep`, bumps the
refcount, assumes a string is one pointer wide, is IN the binary.

The binary doesn't use an ABI. It contains one.

There's nothing to relink, because there's no separate Boost to rebuild. Boost's
own distribution has encoded the toolset into library filenames forever, the
`-vc71` in `libboost_regex-vc71-mt-d-x86-1_34.lib`. Nobody puts the compiler
version in a filename because things are going well.

What I ended up shipping in 2023: carry the historical `libstdc++.so.6.0.13`
next to the program and rewrite every mangled `_Z*` GOT entry to point into it.
A PLT-hook swap at load. `6.0.13` is GCC 4.4.2, symbol version
`GLIBCXX_3.4.13`, exactly the vintage the rest of the story implies.

I hated it, and spent a long time looking for something cleaner before accepting
there isn't one. But it works for a reason nothing else does: it IS the code
that implemented that ABI. Not a reimplementation. The original. Restore the
library that still keeps `_M_length` twelve bytes before the data and both
halves of the contract agree again.

## Is it rare?

The COW→SSO break, no, not remotely. One of the best-documented compatibility
events in the toolchain's history, and it broke a mountain of software. If
you've ever seen `undefined reference to
'foo(std::__cxx11::basic_string...)'`, that's this.

Whether the specific symbol churn around 6.0.13 was routine or unusual I
couldn't establish, and I'd rather say so than guess. The version spread on the
C1/C2 aliases looks like ordinary release-to-release variation, but that's me
inferring from one symbol table, not reading a changelog.

## The bill

In 2010 there was no `std::filesystem`, no `std::regex`, no `std::chrono`. All
three arrived later, regex and chrono in C++11 and filesystem in C++17, and all
three are more or less direct descendants of the Boost components this binary
uses. Reaching for Boost wasn't a shortcut, it was the only answer available.

A successor product dropped Boost for the standard equivalents and the problem
went away, for new builds. Everything already shipped stays exactly as frozen as
it was.

The easy moral is don't statically link C++. The one I actually took is about
time: a statically linked C++ library makes that library's ABI a permanent
property of your binary, and every assumption its templates made about
`std::string` is welded in with no seam left to reopen.

And nothing tells you. The binary doesn't announce which ABI it froze, the
symbols resolve, the disassembly looks right because it IS right. What quietly
stops being true is that the current version of the library, the one you'll open
when you go to check, describes your binary. Your reference drifts away from
your artifact and no tool anywhere notices. You find out because a path of
length one is empty.

Every place I've hit statically linked Boost since, I've pulled it out. Not
because Boost is bad, but because I know what it costs and roughly when the
invoice arrives. Much cheaper to decide that at the start than while you're
staring at a decompiled length check wondering why minus twelve.

Thoughts? Curious whether anyone's hit the quieter 4.x-era version of this,
where there's no `__cxx11` marker to tip you off at all.

---

*Sources: the [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html)
§5.1.4.3 on constructor and destructor variants, the libstdc++
[ABI policy](https://gcc.gnu.org/onlinedocs/libstdc++/manual/abi.html) and
[dual ABI docs](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html),
the [GCC 5 release notes](https://gcc.gnu.org/gcc-5/changes.html), and the
copy-on-write string header itself,
[`basic_string.h` at GCC 4.4.2](https://github.com/gcc-mirror/gcc/blob/releases/gcc-4.4.2/libstdc%2B%2B-v3/include/bits/basic_string.h),
cross-checked against 4.9.0. Boost library naming from their
[getting started guide](https://www.boost.org/doc/libs/1_88_0/more/getting_started/unix-variants.html).
Symbol tables and `sizeof` figures measured against `libstdc++.so.6.0.33` on
Debian trixie, not quoted.*
