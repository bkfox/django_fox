`thesis`
========
This module provides DSL and classes to formalize assumptions in unit tests.

Example:

    .. code-block :: python

        # where ``mod`` is the imported tested module.
        with (Thesis() & Predicate(mod.os, "path")
                       & Feign("exists", True)
                       & Feign("abspath", "/tmp/a", "/tmp/b")
                       & Predicate(mod.sys, argv=["arg1", "arg2"])
       ):
           mod.test_some_function()
           # on __exit__ all function will be checked to see if they have been
           # called.
