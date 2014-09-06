#!/usr/bin/env python
# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of the Ansible Documentation
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

__docformat__ = 'restructuredtext'

import os
import sys
import traceback
try:
    from sphinx.application import Sphinx
except ImportError:
    print "#################################"
    print "Dependency missing: Python Sphinx"
    print "#################################"
    sys.exit(1)
import os

try:
    import rst2pdf
    HAS_RST2PDF = True
except ImportError:
    HAS_RST2PDF = False


class SphinxBuilder(object):
    """
    Creates HTML documentation using Sphinx.
    """

    def __init__(self, buildername='html'):
        """
        Run the DocCommand.
        """
        print "Creating html documentation ..."

        try:
            outdir = os.path.abspath(os.path.join(os.getcwd(), "%sout" % buildername))
            # Create the output directory if it doesn't exist
            if not os.access(outdir, os.F_OK):
                os.mkdir(outdir)

            doctreedir = os.path.join('./', '.doctrees')

            confdir = os.path.abspath('./')
            srcdir = os.path.abspath('rst')
            freshenv = True

            # Create the builder
            app = Sphinx(srcdir,
                              confdir,
                              outdir,
                              doctreedir,
                              buildername,
                              {},
                              sys.stdout,
                              sys.stderr,
                              freshenv)

            app.builder.build_all()

        except ImportError, ie:
            traceback.print_exc()
        except Exception, ex:
            print >> sys.stderr, "FAIL! exiting ... (%s)" % ex

    def build_docs(self):
        self.app.builder.build_all()


def build_rst_docs():
    docgen = SphinxBuilder()

def build_pdf_docs():
    if not HAS_RST2PDF:
        print "##################################"
        print "Dependency missing: Python rst2pdf"
        print "##################################"
        sys.exit(1)
    docgen = SphinxBuilder('pdf')

if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        print "This script builds the html documentation from rst/asciidoc sources.\n"
        print "    Run 'make docs' to build everything."
        print "    Run 'make htmldocs' to build html docs."
        print "    Run 'make pdf' to build pdf docs."
        print "    Run 'make viewdocs' to build and then preview in a web browser."
        sys.exit(0)

    # The 'htmldocs' make target will call this scrip twith the 'rst'
    # parameter' We don't need to run the 'htmlman' target then.
    if "rst" in sys.argv:
        build_rst_docs()
    elif "pdf" in sys.argv:
        build_pdf_docs()
    else:
        # By default, preform the rst->html transformation and then
        # the asciidoc->html trasnformation
        build_rst_docs()
        build_pdf_docs()

    if "view" in sys.argv:
        import webbrowser
        if not webbrowser.open('htmlout/index.html'):
            print >> sys.stderr, "Could not open on your webbrowser."
