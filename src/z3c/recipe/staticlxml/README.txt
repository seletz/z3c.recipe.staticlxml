Supported options
=================

The recipe supports the following options:

**egg**
    Set to the desired lxml egg, e.g. ``lxml`` or ``lxml==2.1.2``

**libxslt-url, libxml2-url**
    The URL to download the source tarball of these libraries from.  Currently
    defaults to::

      http://dist.repoze.org/lemonade/dev/cmmi/libxslt-1.1.24.tar.gz
      http://dist.repoze.org/lemonade/dev/cmmi/libxml2-2.6.32.tar.gz

**build-libxslt, build-libxml2**
    Set to ``true`` if these should be build.  Needed for a static build.

**static-build**
    ``true`` or ``false``

**xml2-loction**
    Needed if ``libxml2`` is not built.

**xslt-loction**
    Needed if ``libxslt`` is not built.

**xslt-config**
    Path to the ``xslt-config`` binary.  Not needed if ``build-libxslt`` is
    set to true.

**xml2-config**
    Path to the ``xml2-config`` binary.  Not needed if ``build-libxml2`` is
    set to true.

**force**
    Set to ``true`` to force rebuilding libraries every time.


Example usage
=============

This is an example buildout::

    [buildout]
    parts =
       lxml
       pylxml
    develop = .

    log-level = DEBUG

    download-directory = downloads
    download-cache = downloads

    versions=versions

    [versions]
    lxml = 2.1.3


    [pylxml]
    recipe=zc.recipe.egg
    interpreter=pylxml
    eggs=
        lxml

    [lxml]
    recipe = z3c.recipe.staticlxml
    egg = lxml
    force = false
    build-libxml2 = true
    build-libxslt = true
    static-build = true



