#!/usr/bin/env python
# encoding: utf-8
#
# Copyright © 2014 deanishe@deanishe.net
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-02-24
#

"""
"""

from __future__ import print_function, unicode_literals

import os
import shutil
import sys

from pint import UnitRegistry, UndefinedUnitError

from workflow import Workflow, ICON_WARNING, ICON_INFO
from workflow.background import run_in_background, is_running
from config import (CURRENCY_CACHE_AGE, CURRENCY_CACHE_NAME,
                    ICON_UPDATE,
                    UPDATE_SETTINGS, DEFAULT_SETTINGS,
                    BUILTIN_UNIT_DEFINITIONS,
                    CUSTOM_DEFINITIONS_FILENAME,
                    HELP_URL)

log = None

# Pint objects
ureg = UnitRegistry()


def convert(query, decimal_places=2, exchange_rates=None,
            default_currency=None):
    """Parse query, calculate and return conversion result

    Raises a `ValueError` if the query is not understood or is invalid (e.g.
    trying to convert between incompatible units).

    :param query: the query entered into Alfred
    :type query: `unicode`
    :returns: the result of the conversion
    :rtype: `unicode`

    """

    if exchange_rates is None:
        exchange_rates = {}

    # Parse number from start of query
    qty = []
    for c in query:
        if c in '1234567890.':
            qty.append(c)
        else:
            break
    if not len(qty):
        raise ValueError('Start your query with a number')

    tail = query[len(qty):]
    qty = float(''.join(qty))
    if not len(tail):
        raise ValueError('No units specified')
    log.debug('quantity : %s tail : %s', qty, tail)

    # Try to parse rest of query into a pair of units
    atoms = tail.split()
    from_unit = to_unit = None
    # Try splitting tail at every space until we arrive at a pair
    # of units that `pint` understands
    conv = 0.0
    units = ""
    for i in xrange(len(atoms)):
        i += 1  # otherwise q1 will always be "" on i = 0
        q1 = ' '.join(atoms[:i]).strip()
        q2 = ' '.join(atoms[i:]).strip()
        log.debug('atoms : %r  i : %d  q1 : %s  q2 : %s', atoms, i, q1, q2)
        if not q1 and not q2:
            continue

        # Currency exchange
        rate = None
        c1, c2 = q1.upper(), q2.upper()
        try:
            if default_currency and not c2:
                rate = exchange_rates[(c1, default_currency)]
                units = default_currency
            elif q2:
                rate = exchange_rates[(c1, c2)]
                units = c2
        except KeyError:
            pass

        if rate:
            conv = qty * rate
            break

        # Pint unit conversion
        from_unit = to_unit = None
        try:
            from_unit = getattr(ureg, q1)
            if q2:
                to_unit = getattr(ureg, q2)
        except UndefinedUnitError:  # Didn't make sense; try again
            continue

        log.debug("from '%s' to '%s'", from_unit, to_unit)

        qty_q = qty * from_unit
        if to_unit:
            qty_q = qty_q.to(to_unit)
        conv, units = qty_q.magnitude, str(qty_q.units)

        break  # Got something!

    else:
        raise ValueError("Not enough units recognised")

    if not conv:
        raise ValueError("Conversion failed. File a bug please.")

    log.debug("converted: {!r} {!r}".format(conv, units))

    fmt = '%%0.%df %%s' % decimal_places
    return fmt % (conv, units)


def main(wf):
    # thread = None
    if not len(wf.args):
        return 1
    query = wf.args[0]  # .lower()
    log.debug('query : %s', query)

    # Notify of available update
    if wf.update_available:
        wf.add_item('A newer version is available',
                    'Use query `workflow:update` to install the new version',
                    icon=ICON_UPDATE)

    # Add custom units from workflow and user data
    ureg.load_definitions(BUILTIN_UNIT_DEFINITIONS)
    user_definitions = wf.datafile(CUSTOM_DEFINITIONS_FILENAME)

    # User's custom units
    if os.path.exists(user_definitions):
        ureg.load_definitions(user_definitions)
    else:  # Copy template to data dir
        shutil.copy(
            wf.workflowfile('{}.sample'.format(CUSTOM_DEFINITIONS_FILENAME)),
            wf.datafile(CUSTOM_DEFINITIONS_FILENAME))

    # Load cached data
    exchange_rates = wf.cached_data(CURRENCY_CACHE_NAME, max_age=0)

    if not wf.cached_data_fresh(CURRENCY_CACHE_NAME, CURRENCY_CACHE_AGE):
        # Update currency rates
        cmd = ['/usr/bin/python', wf.workflowfile('currency.py')]
        run_in_background('update', cmd)

    if is_running('update'):
        if exchange_rates is None:  # No data cached yet
            wf.add_item('Fetching exchange rates…',
                        'Currency conversions will be momentarily possible',
                        icon=ICON_INFO)
        else:
            wf.add_item('Updating exchange rates…',
                        icon=ICON_INFO)

    error = None
    conversion = None

    try:
        conversion = convert(query,
                             decimal_places=wf.settings.get(
                                 'decimal_places', 2),
                             exchange_rates=exchange_rates,
                             default_currency=wf.settings.get(
                                 'default_currency', None))
    except UndefinedUnitError as err:
        log.critical('Unknown unit : %s', err.unit_names)
        error = 'Unknown unit : {}'.format(err.unit_names)

    except ValueError as err:
        log.critical('Invalid query : %s', err)
        error = err.message

    except Exception as err:
        log.exception('%s : %s', err.__class__, err)
        error = err.message

    if not error and not conversion:
        error = 'Conversion input not understood'

    if error:  # Show error
        wf.add_item(error,
                    'For example: 2.5cm in  |  178lb kg  |  200m/s mph',
                    valid=False, icon=ICON_WARNING)
    else:  # Show result
        wf.add_item(conversion,
                    valid=True,
                    arg=conversion,
                    copytext=conversion,
                    largetext=conversion,
                    icon='icon.png')

    wf.send_feedback()
    log.debug('finished')
    return 0


if __name__ == '__main__':
    wf = Workflow(update_settings=UPDATE_SETTINGS,
                  default_settings=DEFAULT_SETTINGS,
                  help_url=HELP_URL)
    log = wf.logger
    sys.exit(wf.run(main))
