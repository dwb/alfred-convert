#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2014 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-02-15
#

"""
A Python helper library for `Alfred 2 <http://www.alfredapp.com/>`_ Workflow
authors.

Alfred Workflows typically take user input, fetch data from the Web or
elsewhere, filter them and display results to the user. **Alfred-Workflow**
helps you do these things.

There are convenience methods for:

- Parsing script arguments.
- Text decoding/normalisation.
- Caching data and settings.
- Secure storage (and sync) of passwords (using OS X Keychain).
- Generating XML output for Alfred.
- Including external libraries (adding directories to ``sys.path``).
- Filtering results using an Alfred-like algorithm.
- Generating log output for debugging.
- Capturing errors, so the workflow doesn't fail silently.

Quick Example
=============

Here's how to show recent `Pinboard.in <https://pinboard.in/>`_ posts in Alfred.

Create a new Workflow in Alfred's preferences. Add a **Script Filter** with
Language ``/usr/bin/python`` and paste the following into the **Script** field
(changing ``API_KEY``):

.. code-block:: python
   :emphasize-lines: 4

    import sys
    from workflow import Workflow, ICON_WEB, web

    API_KEY = 'your-pinboard-api-key'

    def main(wf):
        url = 'https://api.pinboard.in/v1/posts/recent'
        params = dict(auth_token=API_KEY, count=20, format='json')
        r = web.get(url, params)
        r.raise_for_status()
        for post in r.json()['posts']:
            wf.add_item(post['description'], post['href'], arg=post['href'],
                        uid=post['hash'], valid=True, icon=ICON_WEB)
        wf.send_feedback()


    if __name__ == u"__main__":
        wf = Workflow()
        sys.exit(wf.run(main))


Add an **Open URL** action to your Workflow with ``{query}`` as the **URL**,
connect your **Script Filter** to it, and you can now hit **ENTER** on a
Pinboard item in Alfred to open it in your browser.

Installation
============

Download the ``alfred-workflow-X.X.zip`` file from the
`GitHub releases page <https://github.com/deanishe/alfred-workflow/releases>`_
and either extract the ZIP to the root directory of your workflow (where
``info.plist`` is) or place the ZIP in the root directory and add
``sys.path.insert(0, 'alfred-workflow-X.X.zip')`` to the top of your
Python scripts.

Alternatively, you can download
`the source code <https://github.com/deanishe/alfred-workflow/archive/master.zip>`_
from the `GitHub repository <https://github.com/deanishe/alfred-workflow>`_ and
copy the ``workflow`` subfolder to the root directory of your Workflow.

Your Workflow directory should look something like this (where
``yourscript.py`` contains your Workflow code and ``info.plist`` is
the Workflow information file generated by Alfred)::

    Your Workflow/
        info.plist
        icon.png
        workflow/
            __init__.py
            background.py
            workflow.py
            web.py
        yourscript.py
        etc.


Or like this::

    Your Workflow/
        info.plist
        icon.png
        workflow-1.4.zip
        yourscript.py
        etc.


"""

__version__ = '1.8'


from .workflow import Workflow, PasswordNotFound, KeychainError
from .workflow import (ICON_ERROR, ICON_WARNING, ICON_NOTE, ICON_INFO,
                       ICON_FAVORITE, ICON_FAVOURITE, ICON_USER, ICON_GROUP,
                       ICON_HELP, ICON_NETWORK, ICON_WEB, ICON_COLOR,
                       ICON_COLOUR, ICON_SYNC, ICON_SETTINGS, ICON_TRASH,
                       ICON_MUSIC, ICON_BURN, ICON_ACCOUNT, ICON_ERROR)
from .workflow import (MATCH_ALL, MATCH_ALLCHARS, MATCH_ATOM,
                       MATCH_CAPITALS, MATCH_INITIALS,
                       MATCH_INITIALS_CONTAIN, MATCH_INITIALS_STARTSWITH,
                       MATCH_STARTSWITH, MATCH_SUBSTRING)
