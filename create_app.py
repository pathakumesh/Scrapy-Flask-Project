#!/usr/bin/env python

import logging
from flask import Flask


def create_app(config_filename):
    '''Creates an app reading the config file
    '''
    global app

    app = Flask(__name__)
    app.config.from_object(config_filename)
    # _configure_logging(app)

    from views.listing import listing
    from views.frontend import frontend
    from views.execute import execute
    from views.status import status

    app.register_blueprint(frontend)
    app.register_blueprint(execute, url_prefix='/start_scraping')
    app.register_blueprint(listing, url_prefix='/list')
    app.register_blueprint(status, url_prefix='/check_status')


    return app

def _configure_logging(app):
    level = getattr(logging, 'INFO')
    logging.root.setLevel(level)
    logging.disable(level - 1)
    logging.root.addHandler(_create_console_logger())

def _create_console_logger():
    stderr_format = "%(levelname)s: %(message)s"
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(logging.Formatter(stderr_format))
    return stderr_handler
