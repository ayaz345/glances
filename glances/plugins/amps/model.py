# -*- coding: utf-8 -*-
#
# This file is part of Glances.
#
# SPDX-FileCopyrightText: 2023 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

"""Monitor plugin."""

from glances.globals import iteritems
from glances.amps_list import AmpsList as glancesAmpsList
from glances.plugins.plugin.model import GlancesPluginModel


class PluginModel(GlancesPluginModel):
    """Glances AMPs plugin."""

    def __init__(self, args=None, config=None):
        """Init the plugin."""
        super(PluginModel, self).__init__(args=args, config=config, stats_init_value=[])
        self.args = args
        self.config = config

        # We want to display the stat in the curse interface
        self.display_curse = True

        # Init the list of AMP (classes define in the glances/amps_list.py script)
        self.glances_amps = glancesAmpsList(self.args, self.config)

    def get_key(self):
        """Return the key of the list."""
        return 'name'

    @GlancesPluginModel._check_decorator
    @GlancesPluginModel._log_result_decorator
    def update(self):
        """Update the AMP list."""
        # Init new stats
        stats = self.get_init_value()

        if self.input_method == 'local':
            for k, v in iteritems(self.glances_amps.update()):
                stats.append(
                    {
                        'key': self.get_key(),
                        'name': v.NAME,
                        'result': v.result(),
                        'refresh': v.refresh(),
                        'timer': v.time_until_refresh(),
                        'count': v.count(),
                        'countmin': v.count_min(),
                        'countmax': v.count_max(),
                        'regex': v.regex() is not None,
                    },
                )
        # Update the stats
        self.stats = stats

        return self.stats

    def get_alert(self, nbprocess=0, countmin=None, countmax=None, header="", log=False):
        """Return the alert status relative to the process number."""
        if nbprocess is None:
            return 'OK'
        if countmin is None:
            countmin = nbprocess
        if countmax is None:
            countmax = nbprocess
        if nbprocess > 0:
            return 'OK' if int(countmin) <= int(nbprocess) <= int(countmax) else 'WARNING'
        else:
            return 'OK' if int(countmin) == 0 else 'CRITICAL'

    def msg_curse(self, args=None, max_width=None):
        """Return the dict to display in the curse interface."""
        # Init the return message
        # Only process if stats exist and display plugin enable...
        ret = []

        if not self.stats or args.disable_process or self.is_disabled():
            return ret

        # Build the string message
        for m in self.stats:
            # Only display AMP if a result exist
            if m['result'] is None:
                continue
            # Display AMP
            first_column = f"{m['name']}"
            first_column_style = self.get_alert(m['count'], m['countmin'], m['countmax'])
            second_column = f"{m['count'] if m['regex'] else ''}"
            for line in m['result'].split('\n'):
                # Display first column with the process name...
                msg = '{:<16} '.format(first_column)
                ret.append(self.curse_add_line(msg, first_column_style))
                # ... and second column with the number of matching processes...
                msg = '{:<4} '.format(second_column)
                ret.append(self.curse_add_line(msg))
                # ... only on the first line
                first_column = second_column = ''
                ret.extend((self.curse_add_line(line, splittable=True), self.curse_new_line()))
        # Delete the last empty line
        try:
            ret.pop()
        except IndexError:
            pass

        return ret
