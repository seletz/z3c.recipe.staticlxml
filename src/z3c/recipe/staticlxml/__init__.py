# -*- coding: utf-8 -*-
"""Recipe staticlxml"""

import sys
import os
import pkg_resources
import logging
import subprocess
from fnmatch import fnmatch

import distutils.core
from distutils import sysconfig
import setuptools.command.easy_install

from zc.buildout import UserError
from zc.buildout import easy_install

from zc.recipe.egg.custom import Custom
from zc.recipe.egg.custom import build_ext

import zc.recipe.cmmi


def which(fname, path=None):
    """Return first matching binary in path or os.environ["PATH"]
    """
    if path is None:
        path = os.environ.get("PATH")
    fullpath = filter(os.path.isdir,path.split(os.pathsep))

    out = []
    if '.' not in fullpath:
        fullpath = ['.'] + fullpath
    fn = fname
    for p in fullpath:
        for f in os.listdir(p):
            head, ext = os.path.splitext(f)
            if f == fn or fnmatch(head, fn):
                return os.path.join(p,f)
    return None


class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        self.logger = logging.getLogger(name)

        self.xslt_cmmi = zc.recipe.cmmi.Recipe(buildout, "libxslt", options.copy())
        self.xml2_cmmi = zc.recipe.cmmi.Recipe(buildout, "libxml2", options.copy())

        # force build option
        force = options.get("force")
        self.force = force in ("true", "True")
        options["force"] = force and "true" or "false"

        # XLST build or location option
        build_xslt = options.get("build-libxslt", "true")
        self.build_xslt = build_xslt in ("true", "True")
        options["build-libxslt"] = build_xslt and "true" or "false"

        if not self.build_xslt:
            self.xslt_location = options.get("xslt-location")
            if not self.xslt_location:
                raise UserError("You must either configure ``xslt-location`` or set"
                        " ``build-libxslt`` to ``true``")

        # XML2 build or location option
        build_xml2 = options.get("build-libxml2", "true")
        self.build_xml2 = build_xml2 in ("true", "True")
        options["build-libxml2"] = build_xml2 and "true" or "false"

        if not self.build_xml2:
            self.xml2_location = options.get("xml2-location")
            if not self.xml2_location:
                raise UserError("You must either configure ``xml2-location`` or set"
                        " ``build-libxml2`` to ``true``")

        # static build option
        static_build = options.get("static-build", "darwin" in sys.platform and "true" or None)
        self.static_build = static_build in ("true", "True")
        if self.static_build and not (self.build_xml2 and self.build_xslt):
            raise UserError("Static build is only possible if both "
                    "``build-libxml2`` and ``build-libxslt`` are ``true``.")
        if self.static_build:
            self.logger.info("Static build requested.")
        options["static-build"] = self.static_build and "true" or "false"

        # our location
        location = options.get(
            'location', buildout['buildout']['parts-directory'])
        options['location'] = os.path.join(location, name)

    def build_libxslt(self):
        self.logger.info("CMMI libxslt ...")
        self.options["libxslt-url"] = self.xslt_url = self.options.get("libxslt-url",
                "http://dist.repoze.org/lemonade/dev/cmmi/libxslt-1.1.24.tar.gz")
        self.logger.info("Using libxslt download url %s" % self.xslt_url)
        self.xslt_cmmi.options["url"] = self.xslt_url
        self.xslt_cmmi.options["extra_options"] = "--with-libxml-prefix=%s --without-python" % self.xml2_location

        if os.path.exists(os.path.join(self.xslt_cmmi.options["location"], "bin", "xslt-config")):
            self.logger.info("Skipping build of libxslt: already there")
            loc = self.xslt_cmmi.options.get("location")
        else:
            loc = self.xslt_cmmi.install()

        self.options["xslt-location"] = self.xslt_location = loc

    def build_libxml2(self):
        self.logger.info("CMMI libxml2 ...")
        self.options["libxml2-url"] = self.xml2_url = self.options.get("libxml2-url",
                "http://dist.repoze.org/lemonade/dev/cmmi/libxml2-2.6.32.tar.gz")
        self.logger.info("Using libxml2 download url %s" % self.xml2_url)

        self.xml2_cmmi.options["url"] = self.xml2_url
        self.xml2_cmmi.options["extra_options"] = "--without-python"

        if not self.force and os.path.exists(os.path.join(self.xml2_cmmi.options["location"], "bin", "xml2-config")):
            self.logger.info("Skipping build of libxml2: already there")
            loc = self.xml2_cmmi.options["location"]
        else:
            loc = self.xml2_cmmi.install()
        self.options["xml2-location"] = self.xml2_location = loc

    def install(self):

        # build dependent libs if requested
        if self.build_xml2:
            self.build_libxml2()
        else:
            self.logger.warn("Using configured libxml2 at %s" % self.xml2_location)

        if self.build_xslt:
            self.build_libxslt()
        else:
            self.logger.warn("Using configured libxslt at %s" % self.xslt_location)

        # get the config executables
        self.get_configs( os.path.join(self.xml2_location, "bin"), os.path.join(self.xslt_location, "bin"))

        if self.static_build:
            self.remove_dynamic_libs(self.xslt_location)
            self.remove_dynamic_libs(self.xml2_location)

        # build LXML
        dest = self.options.get("location")
        if not os.path.exists(dest):
            os.mkdir(dest)

        self.options["include-dirs"] = "%s %s" % (
                os.path.join(self.xml2_location, "include", "libxml2"),
                os.path.join(self.xslt_location, "include"),
                )
        self.options["library-dirs"] = "%s %s" % (
                os.path.join(self.xml2_location, "lib"),
                os.path.join(self.xslt_location, "lib"),
                )
        self.options["rpath"] = "%s %s" % (
                os.path.join(self.xml2_location, "lib"),
                os.path.join(self.xslt_location, "lib"),
                )
        self.options["libraries"] = "iconv" # missing in lxml setup.py jungle, but needed by
                                            # libxml2 and libxslt
        self.lxml_custom = Custom(self.buildout, self.name, self.options)
        self.lxml_custom.environment = self.lxml_build_env()

        self.logger.info("Building lxml ...")
        self.lxml_dest = self.lxml_custom.install()

        dest = [dest, ] # dont report libxml2 and libxslt to buildout -- BO removes them
        dest.extend(self.lxml_dest)
        return tuple(dest)

    def get_ldshared(self):
        import distutils.sysconfig
        LDSHARED = sysconfig.get_config_vars().get("LDSHARED")
        self.logger.debug("LDSHARED=%s" % LDSHARED)
        if "darwin" in sys.platform:
            self.logger.warn("OS X detected.")
            # remove macports "-L/opt/local/lib"
            if "-L/opt/local/lib" in LDSHARED:
                self.logger.warn("*** Removing '-L/opt/local/lib' from 'LDSHARED'")
                LDSHARED = LDSHARED.replace("-L/opt/local/lib", "")
            if self.static_build:
                self.logger.info("Static build -- adding '-Wl,-search_paths_first'")
                LDSHARED = LDSHARED + " -Wl,-search_paths_first "
        self.logger.debug("LDSHARED'=%s" % LDSHARED)
        return LDSHARED

    def remove_dynamic_libs(self, path):
        self.logger.info("Removing dynamic libs form path %s ..." % path)
        soext = "so"

        if "darwin" in sys.platform:
            soext = "dylib"

        path = os.path.join(path, "lib")

        for fname in os.listdir(path):
            if fname.endswith(soext):
                os.unlink(os.path.join(path, fname))
                self.logger.debug("removing %s" % fname)

    def get_configs(self, xml2_location=None, xslt_location=None):
        """Get the executables for libxml2 and libxslt configuration

        If not configured, then try to get them from a built location.
        If the location is not given, then search os.environ["PATH"] and
        warn the user about that.
        """
        self.xslt_config = self.options.get("xslt-config")
        if not self.xslt_config:
            self.xslt_config = which("xslt-config", xslt_location)
            if not self.xslt_config:
                raise UserError("No ``xslt-config`` binary coinfigured and none found in path.")
            self.logger.warn("Using xslt-config found in %s." % self.xslt_config)

        self.xml2_config = self.options.get("xml2-config")
        if not self.xml2_config:
            self.xml2_config = which("xml2-config", xml2_location)
            if not self.xml2_config:
                raise UserError("No ``xml2-config`` binary coinfigured and none found in path.")
            self.logger.warn("Using xml2-config found in %s." % self.xml2_config)

        self.logger.debug("xslt-config: %s" % self.xslt_config)
        self.logger.debug("xml2-config: %s" % self.xml2_config)

    update = install

    def lxml_build_env(self):
        return dict(
                XSLT_CONFIG=self.xslt_config,
                XML_CONFIG=self.xml2_config,
                LDSHARED=self.get_ldshared())

# vim: set ft=python ts=4 sw=4 expandtab : 
