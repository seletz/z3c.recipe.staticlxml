Supported options
=================

The recipe supports the following options:

egg
    Set to the desired lxml egg, e.g. ``lxml`` or ``lxml==2.1.2``

build-libxslt, build-libxml2
    Set to ``true`` if these should be build.  Needed for a static build.

static-build
    ``true``or ``false``

xml2-loction
    Needed if ``libxml2`` is not built.

xslt-loction
    Needed if ``libxml2`` is not built.

xslt-config
    Path to the ``xslt-config`` binary.  Not needed if ``build-libxslt`` is
    set to true.

xml2-config
    Path to the ``xml2-config`` binary.  Not needed if ``build-libxml2`` is
    set to true.

force
    Set to ``true`` to force rebuilding libraries every time.


Example usage
=============

We'll start by creating a buildout that uses the recipe::

    >>> xsltconfig = "foo"
    >>> xml2config = "bar"
    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = test1
    ... log-level = INFO
    ... index = http://dist.repoze.org/lemonade/dev/simple
    ...
    ... [test1]
    ... recipe = z3c.recipe.staticlxml
    ... xslt-config = %(xsltconfig)s
    ... xml2-config = %(xml2config)s
    ... """ % locals())

Running the buildout gives us::

    >>> system(buildout) 
    Installing test1.
    xslt-config: foo
    xml2-config: bar
    <BLANKLINE>


