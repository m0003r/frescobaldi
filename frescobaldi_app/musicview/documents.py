# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Code to load and manage PDF documents to view.
"""

from __future__ import unicode_literals


import os
import weakref

from PyQt4.QtCore import QByteArray

try:
    import popplerqt4
except ImportError:
    popplerqt4 = None

import app
import plugin
import resultfiles
import signals
import popplertools


_cache = weakref.WeakValueDictionary()


# This signal gets emitted when a finished Job has created new PDF document(s).
documentUpdated = signals.Signal() # Document


@app.jobFinished.connect
def _on_job_finished(document, job):
    if group(document).update():
        documentUpdated(document, job)


def group(document):
    """Returns a DocumentGroup instance for the given text document."""
    return DocumentGroup.instance(document)


def load(filename):
    """Returns a Poppler.Document for the given filename, caching it (weakly).
    
    Returns None if the document failed to load.
    
    """
    mtime = os.path.getmtime(filename)
    key = (mtime, filename)
    
    try:
        return _cache[key]
    except KeyError:
        with open(filename, 'rb') as f:
            data = QByteArray(f.read())
        doc = popplerqt4.Poppler.Document.loadFromData(data)
        if doc:
            _cache[key] = doc
        return doc or None


def filename(poppler_document):
    """Returns the filename for the document if it was loaded via our cache."""
    for (mtime, filename), doc in _cache.items():
        if doc == poppler_document:
            return filename


class Document(popplertools.Document):
    """Represents a (lazily) loaded PDF document."""
    def load(self):
        return load(self.filename())
        
    if popplerqt4 is None:
        def document(self):
            """Returns None because popplerqt4 is not available."""
            return None


class DocumentGroup(plugin.DocumentPlugin):
    """Represents a group of PDF documents, created by the text document it belongs to.
    
    Multiple MusicView instances can use this group, they can store the positions
    of the Documents in the viewer themselves via a weak-key dictionary on the Document
    instances returned by documents(). On update() these Document instances will be reused.
    
    The global documentUpdated(Document) signal will be emitted when the global
    app.jobFinished() signal causes a reload of documents in a group.
    
    """
    def __init__(self, document):
        self._documents = None
        document.loaded.connect(self.update, -100)
        
    def documents(self):
        """Returns the list of PDF Document objects created by our text document."""
        # If the list is asked for the very first time, update
        if self._documents is None:
            self._documents = []
            self.update()
        return self._documents[:]
    
    def update(self):
        """Queries the resultfiles of this text document for PDF files and loads them.
        
        Returns True if new documents were loaded.
        
        """
        files = resultfiles.results(self.document()).files(".pdf")
        if files:
            # reuse the older Document objects, they will probably be displaying
            # (about) the same documents, and so the viewer will remember their position.
            def docs():
                # yield existing docs and then new ones
                for d in self._documents:
                    yield d
                while True:
                    yield Document()
            documents = []
            for filename, doc in zip(files, docs()):
                doc.setFilename(filename)
                documents.append(doc)
            self._documents = documents
            return True


