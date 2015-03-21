#!/usr/bin/python
# encoding: utf-8
#
# Copyright © 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-12-26
#

"""info.py [options] [<query>]

Usage:
    info.py [<query>]
    info.py (-h|--help)
    info.py --openhelp
    info.py --openunits
    info.py --currencies [<query>]
    info.py --places <query>
    info.py --defaultcurrency <query>

Options:
    -h, --help    Show this message
    --openhelp    Open help file in default browser
    --openunits   Open custom units file in default editor
    --currencies  View/search supported currencies
    --places      Set decimal places
    --defaultcurrency    Set default currency

"""

from __future__ import print_function, unicode_literals, absolute_import

from datetime import timedelta
import os
import shutil
import subprocess
import sys

from workflow import (Workflow,
                      ICON_HELP, ICON_WARNING, ICON_INFO, ICON_SETTINGS,
                      MATCH_ALL, MATCH_ALLCHARS)

from config import (ICON_CURRENCY,
                    CURRENCY_CACHE_NAME,
                    CUSTOM_DEFINITIONS_FILENAME,
                    CURRENCIES,
                    DECIMAL_PLACES_DEFAULT,
                    DEFAULT_SETTINGS)

log = None

DELIMITER = '⟩'

ALFRED_AS = 'tell application "Alfred 2" to search "convinfo"'


def human_timedelta(td):
    """Return relative time (past) in human-readable format

    :param td: :class:`datetime.timedelta`
    :returns: Human-readable Unicode string

    """

    output = []
    d = {'day': td.days}
    d['hour'], rem = divmod(td.seconds, 3600)
    d['minute'], d['second'] = divmod(rem, 60)

    for unit in ('day', 'hour', 'minute', 'second'):
        i = d[unit]

        if unit == 'second' and len(output):
            # no seconds unless last update was < 1m ago
            break

        if i == 1:
            output.append('1 %s' % unit)

        elif i > 1:
            output.append('%d %ss' % (i, unit))

    output.append('ago')
    return ' '.join(output)


def main(wf):

    from docopt import docopt

    args = docopt(__doc__, wf.args)

    log.debug('args : {!r}'.format(args))

    query = args.get('<query>')

    if args.get('--openhelp'):
        subprocess.call(['open', wf.workflowfile('README.html')])
        return 0

    if args.get('--openunits'):
        path = wf.datafile(CUSTOM_DEFINITIONS_FILENAME)
        if not os.path.exists(path):
            shutil.copy(
                wf.workflowfile('{}.sample'.format(
                                CUSTOM_DEFINITIONS_FILENAME)),
                path)

        subprocess.call(['open', path])
        return 0

    if args.get('--places'):
        value = int(query)
        log.debug('Setting `decimal_places` to {!r}'.format(value))
        wf.settings['decimal_places'] = value
        print('Set decimal places to {}'.format(value))
        # subprocess.call(['osascript', '-e', ALFRED_AS])
        return 0

    if args.get('--defaultcurrency'):
        value = query.upper()
        if value == "NONE":
            value = None
        log.debug('Setting `default_currency` to {!r}'.format(value))
        wf.settings['default_currency'] = value
        print('Set default currency to {}'.format(value))
        return 0

    if not query or not query.strip():
        wf.add_item('View Help File',
                    'Open help file in your browser',
                    valid=True,
                    arg='--openhelp',
                    icon=ICON_HELP)

        wf.add_item('View Supported Currencies',
                    'View and search list of supported currencies',
                    autocomplete=' currencies {} '.format(DELIMITER),
                    icon=ICON_CURRENCY)

        wf.add_item(('Decimal Places in Results '
                    '(current : {})'.format(wf.settings.get(
                                            'decimal_places',
                                            DECIMAL_PLACES_DEFAULT))),
                    'Set the precision of conversion results',
                    autocomplete=' places {} '.format(DELIMITER),
                    icon=ICON_SETTINGS)

        wf.add_item(('Default Currency '
                    '(current : {})'.format(wf.settings.get(
                        'default_currency', None))),
                    'If no target currency is given, default to this',
                    autocomplete=' currency {} '.format(DELIMITER),
                    icon=ICON_SETTINGS)

        wf.add_item('Edit Custom Units',
                    'Add and edit your own custom units',
                    valid=True,
                    arg='--openunits',
                    icon='icon.png')

        wf.send_feedback()
        return 0

    else:  # Currencies or decimal places
        if query.endswith(DELIMITER):  # User deleted trailing space
            subprocess.call(['osascript', '-e', ALFRED_AS])
            return 0

        mode, query = [s.strip() for s in query.split(DELIMITER)]

        if mode == 'currencies':

            currencies = sorted([(name, symbol) for (symbol, name)
                                in CURRENCIES.items()])

            if query:
                currencies = wf.filter(query, currencies,
                                       key=lambda t: ' '.join(t),
                                       match_on=MATCH_ALL ^ MATCH_ALLCHARS,
                                       min_score=30)

            else:  # Show last update time
                age = wf.cached_data_age(CURRENCY_CACHE_NAME)
                if age > 0:  # Exchange rates in cache
                    td = timedelta(seconds=age)
                    wf.add_item('Exchange rates updated {}'.format(
                                human_timedelta(td)),
                                icon=ICON_INFO)

            if not currencies:
                wf.add_item('No matching currencies',
                            'Try a different query',
                            icon=ICON_WARNING)

            for name, symbol in currencies:
                wf.add_item('{} // {}'.format(name, symbol),
                            'Use `{}` in conversions'.format(symbol),
                            icon=ICON_CURRENCY)

            wf.send_feedback()

        elif mode == 'places':

            if query:
                if not query.isdigit():
                    wf.add_item('Invalid number : {}'.format(query),
                                'Please enter a number',
                                icon=ICON_WARNING)
                else:
                    wf.add_item('Set decimal places to : {}'.format(query),
                                'Hit `ENTER` to save',
                                valid=True,
                                arg='--places {}'.format(query),
                                icon=ICON_SETTINGS)
            else:
                wf.add_item('Enter a number of decimal places',
                            'Current number is {}'.format(
                                wf.settings.get('decimal_places',
                                                DECIMAL_PLACES_DEFAULT)),
                            icon=ICON_INFO)

            wf.send_feedback()

        elif mode == 'currency':

            if query:
                query = query.upper()
                if query == "NONE":
                    wf.add_item('Remove default currency',
                                'Hit `ENTER` to save',
                                valid=True,
                                arg='--defaultcurrency {}'.format(query),
                                icon=ICON_SETTINGS)
                elif query in CURRENCIES:
                    wf.add_item('Set default currency to : {}'.format(query),
                                'Hit `ENTER` to save',
                                valid=True,
                                arg='--defaultcurrency {}'.format(query),
                                icon=ICON_SETTINGS)
                else:
                    wf.add_item('Currency not found : {}'.format(query),
                                'Please enter a known currency',
                                icon=ICON_WARNING)
            else:
                current_default = wf.settings.get(
                    'default_currency',
                    DEFAULT_SETTINGS['default_currency'])
                wf.add_item('Enter a currency (or "none") for conversions to default to',
                            'Current  is {}'.format(current_default)
                            if current_default
                            else "No current default currency",
                            icon=ICON_INFO)

            wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    sys.exit(wf.run(main))
