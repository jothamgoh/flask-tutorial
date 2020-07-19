import os

from flask import Flask


def create_app(test_config=None): # application factory function. Any configuration, registration, and other setup the application needs will happen inside the function, then the application will be returned.
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True) # this line creates the Flask instance. __name__ is current python module name.
    app.config.from_mapping( # sets some default configuration that the app will use
        SECRET_KEY='dev', # used by Flask and extensions to keep data safe, set to 'dev' to provide a convenient value during development. should be overridden with a random value when deploying.
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'), # path where the SQLite database file will be saved. app.instance_path is the path Flask has chosen for the instance folder
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True) # overrides the default configuration with values taken from the config.py file in the instance folder if it exists
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config) # test_config can also be passed to the factory, and will be used instead of the instance configuration. This is so the tests you’ll write later in the tutorial can be configured independently of any development values you have configured.

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path) # ensures that app.instance_path exists
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello') # a simple route so you can see the application working before getting into the rest of the tutorial
    def hello():
        return 'Hello, World!'

    from . import db, auth
    db.init_app(app) # close_db and init_db_command functions need to be registered with the application instance; otherwise, they won’t be used by the application
    app.register_blueprint(auth.bp) # Import and register the auth blueprint


    return app