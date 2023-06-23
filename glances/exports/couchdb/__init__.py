# -*- coding: utf-8 -*-
#
# This file is part of Glances.
#
# SPDX-FileCopyrightText: 2022 Nicolas Hennion <nicolas@nicolargo.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

"""CouchDB interface class."""

import sys
from datetime import datetime

from glances.logger import logger
from glances.exports.export import GlancesExport

import couchdb
import couchdb.mapping


class Export(GlancesExport):

    """This class manages the CouchDB export module."""

    def __init__(self, config=None, args=None):
        """Init the CouchDB export IF."""
        super(Export, self).__init__(config=config, args=args)

        # Mandatory configuration keys (additional to host and port)
        self.db = None

        # Optional configuration keys
        self.user = None
        self.password = None

        # Load the Cassandra configuration file section
        self.export_enable = self.load_conf('couchdb', mandatories=['host', 'port', 'db'], options=['user', 'password'])
        if not self.export_enable:
            sys.exit(2)

        # Init the CouchDB client
        self.client = self.init()

    def init(self):
        """Init the connection to the CouchDB server."""
        if not self.export_enable:
            return None

        if self.user is None:
            server_uri = f'http://{self.host}:{self.port}/'
        else:
            # Force https if a login/password is provided
            # Related to https://github.com/nicolargo/glances/issues/2124
            server_uri = f'https://{self.user}:{self.password}@{self.host}:{self.port}/'

        try:
            s = couchdb.Server(server_uri)
        except Exception as e:
            logger.critical(f"Cannot connect to CouchDB server {server_uri} ({e})")
            sys.exit(2)
        else:
            logger.info("Connected to the CouchDB server")

        try:
            s[self.db]
        except Exception:
            # Database did not exist
            # Create it...
            s.create(self.db)
        else:
            logger.info(f"There is already a {self.db} database")

        return s

    def database(self):
        """Return the CouchDB database object"""
        return self.client[self.db]

    def export(self, name, columns, points):
        """Write the points to the CouchDB server."""
        logger.debug(f"Export {name} stats to CouchDB")

        # Create DB input
        data = dict(zip(columns, points))

        # Set the type to the current stat name
        data['type'] = name
        data['time'] = couchdb.mapping.DateTimeField()._to_json(datetime.now())

        # Write data to the CouchDB database
        # Result can be seen at: http://127.0.0.1:5984/_utils
        try:
            self.client[self.db].save(data)
        except Exception as e:
            logger.error(f"Cannot export {name} stats to CouchDB ({e})")
