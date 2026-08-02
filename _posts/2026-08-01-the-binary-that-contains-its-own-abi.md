---
layout: post
title: "The Binary That Contains Its Own ABI"
date: 2026-08-01
description: "A 2010-era Linux binary that can't run on a modern libstdc++, and why the reason isn't the one everybody gives. Statically linked Boost welded a std::string layout into the executable, and a path of length one started reporting itself empty."
tags: [reverse-engineering, low-level-systems, compatibility, c-plus-plus, abi]
toc: true
---


So I ran into this back in 2022, chased it into 2023, and never properly wrote
it up... finally doing that now because I still think it's one of the more
interesting failure modes I've hit.

A 2010-era commercial Linux application, 32-bit, lands on a modern machine and
just... doesn't behave. First thing you do is look at what it asks the dynamic
linker for, and nineteen imported `std::string` symbols come back, every one of
them the old shape:

```
_ZNSsC1EjcRKSaIcE
_ZNSsD1Ev
_ZNSs4_Rep10_M_disposeERKSaIcE
...
```

`Ss` is the Itanium ABI's built-in substitution for
`std::basic_string<char, std::char_traits<char>, std::allocator<char>>`, and
`_Rep` is the reference-counted header the pre-C++11 copy-on-write string
carried. Nineteen out of nineteen, zero `__cxx11`. That `j` in there is
`unsigned int`... 32-bit `size_t`, the other thing this binary is never getting
back.

The interesting part isn't that it's old. It's WHY it can't be made new, and the
answer turns out to be a decision somebody made around 2009 that was completely
correct at the time.

## First theory, and why it's wrong

The obvious story, and the one you'll hear, is that the copy constructor
`_ZNSsC1EjcRKSaIcE` got removed from libstdc++ and replaced by
`_ZNSsC2EjcRKSaIcE`, so the binary's imports stopped resolving.

That's not it, and it's worth being precise about why, because the real
mechanism is a lot more durable than the fake one.

`C1` and `C2` aren't versions of each other. The Itanium C++ ABI, §5.1.4.3,
defines a whole family of constructor and destructor entry points:

```
<ctor-dtor-name> ::= C1   # complete object constructor
                 ::= C2   # base object constructor
                 ::= C3   # complete object allocating constructor
                 ::= D0   # deleting destructor
                 ::= D1   # complete object destructor
                 ::= D2   # base object destructor
```

They exist because virtual inheritance splits construction in two... a complete
object has to construct its virtual bases, the same class used as a base
subobject must not, because the most-derived constructor already did it. So the
compiler emits two bodies. For a class with no virtual bases, which
`std::string` is, the two bodies are identical, and the spec more or less says
so in the next line: *"Some of the symbols for constructor and destructor
variants are optional."*

I didn't want to trust that, so I checked a shipping library. Debian trixie,
`libstdc++.so.6.0.33`, which is GCC 15:

```
00000000000f8a30 W _ZNSsC1EmcRKSaIcE@@GLIBCXX_3.4
00000000000f8a30 W _ZNSsC2EmcRKSaIcE@@GLIBCXX_3.4
```

Same address, both exported, both still tagged `GLIBCXX_3.4`, which is the label
from GCC 3.4 back in 2004. Nothing was removed. 210 old copy-on-write string
symbols are still exported by a current libstdc++, including all fifteen `_Rep`
internals, the refcount machinery itself. And that's not an accident either,
libstdc++'s ABI policy lists "Deleting an exported symbol" as a prohibited
change, and promises that "program binaries linked with the initial release of a
library binary will still run correctly if the library binary is replaced by
carefully-managed subsequent library binaries."

So I built the thing to check. A 32-bit program compiled with
`-D_GLIBCXX_USE_CXX11_ABI=0`, importing `_ZNSsC1EjcRKSaIcE@GLIBCXX_3.4` plus
three other `_ZNSs*` symbols, links and runs correctly against GCC 15's
libstdc++. The old ABI is still there and still serviced.

There IS a real thing hiding under the garbled version though. The C1 and C2
aliases don't always show up together, and don't always carry the same symbol
version:

```
_ZNSsC1EOSs@@GLIBCXX_3.4.14     # GCC 4.5
_ZNSsC2EOSs@@GLIBCXX_3.4.15     # GCC 4.6
```

One function, two entry points, exported one release apart. Which variants an
explicit template instantiation emits, and whether the redundant one becomes an
alias or just gets omitted, has genuinely moved around across GCC versions...
which produces occasional link-time surprises. It does not produce a frozen
binary. Something else does that.

## Why the old string looked the way it did

The copy-on-write `std::string` is one object-sized pointer. That's the whole
struct. What it points at is character data, and immediately BEFORE the
character data sits a header:

```
        ┌──────────┬──────────┬──────────┬─────────────────────┐
_Rep →  │ length   │ capacity │ refcount │ "hello\0"           │
        └──────────┴──────────┴──────────┴─────────────────────┘
                                          ▲
                                          │
                             std::string ─┘   (one pointer, that's it)
```

Measured, because it's easy to measure... `sizeof(std::string)` in each ABI:

| | 32-bit | 64-bit |
|---|---|---|
| COW (`_GLIBCXX_USE_CXX11_ABI=0`) | 4 | 8 |
| SSO (default, GCC 5+) | 24 | 32 |

The design was pretty reasonable in 1998. Copying a string was a pointer copy
and an increment, so passing and returning by value cost basically nothing,
which mattered enormously in a language that wouldn't get move semantics for
another thirteen years. The refcount bought all of that for four bytes.

Two things killed it. Threads, first: every copy touches a shared refcount, so
every copy is an atomic operation, and by the mid-2000s that cost more than just
copying sixteen bytes of characters, most strings being short. And then the
standard: C++11 requires that operations on distinct string objects not race,
that `operator[]` and `begin()` not invalidate anything, and that `c_str()` be
O(1) and non-mutating. Copy-on-write can't deliver that, because a "read"
through a shared buffer might first have to unshare it. The old design wasn't
just slow by then, it was non-conforming.

The replacement is a ~24/32-byte struct: pointer, length, and a union of
capacity with a small inline buffer. Strings up to 15 characters live entirely
inside the object, no allocation, no refcount, no sharing. And the two layouts
can't be translated into each other at a boundary, because the difference isn't
representational, it's semantic... in one model a copy shares a buffer, in the
other it copies. No shim makes a 4-byte handle and a 24-byte value the same
thing.

GCC 5.1 shipped both. `_GLIBCXX_USE_CXX11_ABI` picks which one, and the new one
lives in an inline namespace, which is why `std::__cxx11` shows up in mangled
names. That was the clever bit honestly: the ABI break was deliberately made to
fail LOUDLY. Mixing the two gets you an unresolved symbol at link time instead
of a memory-corrupting struct mismatch at runtime. The earlier, quieter ABI
drift of the 4.x era had no such guardrail.

## Minus twelve

Here's what all that looks like from the inside. Back in 2019 an engineer was
reverse-engineering a crash in a statically-Boost-linked binary running against
a newer libstdc++, and a Boost path constructor decompiled to something starting
like this:

```c
if ( !*(_DWORD *)(*(_DWORD *)str_path2 - 12) )
    // allocate and throw a runtime_error
```

They checked the Boost source and confirmed what it meant... if the supplied
path has length zero, throw. Except it was throwing for the path `"."`, which is
length one.

Their note on the confusion is worth quoting, because it's exactly the right
confusion to have:

> "why minus 12? for some reason `str_path2` points to the inlined c-string and
> all `std::string` metadata (length, capacity, allocator) is BEFORE that
> pointer. I created some minimal examples and I always got a memory layout of
> allocator, length, inline data for strings with length < 15."

Their conclusion was that either Boost was doing something inscrutable, or
libstdc++ was just being libstdc++. Neither, as it turns out... they were
reading 2010 disassembly against a 2019 reference implementation, and those are
two different `std::string`s.

The pre-GCC-5 `libstdc++-v3/include/bits/basic_string.h` declares the header
like this, unchanged from at least GCC 4.4.2 through 4.9.0:

```cpp
struct _Rep_base
{
  size_type       _M_length;
  size_type       _M_capacity;
  _Atomic_word    _M_refcount;
};
```

and it hands out the data pointer as `_M_refdata()`, which is literally
`reinterpret_cast<_CharT*>(this + 1)`, so the address one whole `_Rep` past the
header. On a 32-bit target those three fields are 4 bytes each. Twelve. And
`_M_length` is the FIRST field, so it sits at exactly `data - 12`.

The `-12` isn't inscrutable at all. It's an ordinary, correct, fully inlined
`empty()` check that got compiled in 2010. I confirmed it on a 32-bit COW build
of `std::string s(".")`:

```
COW  len=1  sizeof=4  *(data-12)=1  *(data-8)=1  *(data-4)=-1
```

Length 1, capacity 1, refcount −1, which is the sentinel for an unshareable
string... every field exactly where the disassembly expects it. Now the same
`"."` under the modern SSO layout, and this is the crash:

```
SSO  len=1  sizeof=24  data-inside-object=1  *(data-12)=20
```

There's no header. For a short string the characters live INSIDE the object, at
offset +8 on a 32-bit target, so `data - 12` lands at offset −4... four bytes
before the string object even starts, in whatever happened to be sitting next to
it. In this run that was 20. Could be anything. When it happens to be zero, a
one-character path is empty, and something throws.

And notice what that ISN'T. Not a missing symbol, not a crash at the call site.
Every symbol resolved, control transferred correctly, arguments passed
correctly. It's a silent misread of an adjacent field, twelve bytes into memory
that stopped meaning what it used to mean. A missing symbol is loud. A
disagreement about where a field lives is not.

It also explains why hooking one function and forwarding it to a working variant
got them past one failure and no further. Every string crossing that boundary
carries the same disagreement, so there's no single call to fix.

## Where the static linking comes in

None of the above traps a binary on its own. Recompile with
`_GLIBCXX_USE_CXX11_ABI=0` and you get the old string, recompile without it and
you get the new one. It's a build flag... unless you can't recompile the thing
that made the decision.

This binary statically links Boost. Three components, and it's always the same
three: filesystem, regex, chrono. Boost is largely templates, so "linking" it
means Boost's instantiations were compiled against the libstdc++ of the day and
inlined directly into the executable. The code that constructs a `_Rep` header,
increments the refcount, and assumes a string is one pointer wide is IN the
binary, not in some library sitting next to it.

The binary doesn't use an ABI. It contains one.

There's nothing to relink against, because there's no separate Boost to rebuild.
Boost's own distribution has always encoded the toolset into library filenames,
the `-vc71` in `libboost_regex-vc71-mt-d-x86-1_34.lib`, which is kind of an
admission right there in the naming scheme that these artifacts are compiler-
and runtime-specific and portable across neither.

The fix that reportedly works for this class of binary is to ship the historical
`libstdc++.so.6.0.13` alongside the program and rewrite every mangled `_Z*` GOT
entry to point into it, a PLT-hook swap at load time. `6.0.13` is GCC 4.4.2,
symbol version `GLIBCXX_3.4.13`, exactly the vintage the rest of the story
implies. And it's correct by construction, for the only reason that actually
matters: it IS the code that implemented that ABI. Not a reimplementation, not a
shim. The original.

Which is where the `-12` comes back around. The symbols were never the problem.
The problem is that the binary's own inlined Boost code is one half of a
contract whose other half moved on. Restore the library that still keeps
`_M_length` twelve bytes before the data and both halves agree again... not
really a workaround so much as the only place agreement is still available.

## Is this rare?

The COW→SSO break isn't rare at all. It's one of the most widely documented
compatibility events in the toolchain's history, it broke an enormous amount of
software, and GCC built the `__cxx11` inline namespace specifically to make it
detectable. Anyone who's seen `undefined reference to
'foo(std::__cxx11::basic_string...)'` has met it.

Whether the SPECIFIC symbol churn of the 6.0.13 era was routine or unusual, I
couldn't determine, and I'd rather say that than guess. The version-label spread
for C1 versus C2 aliases looks like ordinary release-to-release variation rather
than a deliberate break, libstdc++ adds symbols routinely and removes none...
but that's inference from one symbol table, not from a changelog.

## The bill, and when it came due

In 2010 there was no `std::filesystem`, no `std::regex`, no `std::chrono`. All
three showed up later, regex and chrono in C++11, filesystem in C++17, and all
three arrived as more or less direct descendants of the Boost components this
binary uses. Reaching for Boost wasn't a shortcut and it wasn't a mistake. It
was the only correct answer available at the time.

A successor product dropped Boost for the standard equivalents, which ended the
problem... for new builds. Every binary already shipped stays exactly as frozen
as it was.

The easy moral is "don't statically link C++." I think the sharper one is about
time. A statically linked C++ library makes that library's ABI a permanent,
unremovable property of your binary. Every assumption its templates made about
`std::string`'s layout is now your assumption, welded in, with no seam left to
reopen.

And nothing warns you, which is the part the engineer in 2019 walked straight
into. The binary doesn't announce which ABI it froze, the symbols still resolve,
and the disassembly still looks correct, because it IS correct. What quietly
stops being true is that the current version of the library, the one you'll
naturally open when you go to check, describes your binary. Your reference
implementation drifts away from your artifact and no tool tells you. You find
out because a path of length one is empty.

So the question to ask before pulling in a dependency probably isn't "is this
library good?" It's more like: in ten years, will I still be able to rebuild
this? If the answer's no, link it dynamically, so at least the seam outlives
you.

Thoughts? Curious whether anyone's hit the quieter 4.x-era version of this,
where there's no `__cxx11` marker to tip you off.

---

*Sources: the [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html)
(§5.1.4.3, constructor and destructor variants), the libstdc++
[ABI policy and guidelines](https://gcc.gnu.org/onlinedocs/libstdc++/manual/abi.html)
(version tables, non-removal policy) and
[dual ABI documentation](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html),
the [GCC 5 release notes](https://gcc.gnu.org/gcc-5/changes.html), the
copy-on-write string header itself,
[`libstdc++-v3/include/bits/basic_string.h` at GCC 4.4.2](https://github.com/gcc-mirror/gcc/blob/releases/gcc-4.4.2/libstdc%2B%2B-v3/include/bits/basic_string.h)
(`_Rep_base`, `_M_refdata`), cross-checked against the same file at GCC 4.9.0,
and Boost's
[getting started guide](https://www.boost.org/doc/libs/1_88_0/more/getting_started/unix-variants.html)
on library naming. Symbol tables and `sizeof` figures were measured directly
against `libstdc++.so.6.0.33` on Debian trixie (GCC 15), not quoted.*
