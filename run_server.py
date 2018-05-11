

from gevent import monkey
monkey.patch_all()

import logging
from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple

from create_app import create_app



def main():
    """
    runs the flask app
    """
    app = create_app('etc.settings')
    logging.root.setLevel(logging.DEBUG)
    logging.disable(0)

    app = DispatcherMiddleware(app, {'/main': app})

    run_simple('0.0.0.0', 5000, app, True, True)



if __name__ == '__main__':
    main()
