"""WSGI entry point for deployment on PythonAnywhere."""

from dashboard_simulator import app

# Dash exposes a Flask server via the ``server`` attribute which can be used
# by WSGI servers such as the one provided by PythonAnywhere.
application = app.server
