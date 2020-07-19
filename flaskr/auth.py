import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from flask.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth') # the blueprint needs to know where it’s defined, so __name__ is passed as the second argument. The url_prefix will be prepended to all the URLs associated with the blueprint.


@bp.route('/register', methods=('GET', 'POST')) # @bp.route associates the URL /register with the register view function. When Flask receives a request to /auth/register, it will call the register view and use the return value as the response.
def register():
    if request.method == 'POST': # user submitted the form, request.method will be 'POST'. start validating the input.
        username = request.form(['username']) # request.form is a special type of dict mapping submitted form keys and values
        password = request.form(['password'])
        db = get_db()
        error = None

        if not username: # Validate that username and password are not empty.
            error = 'Username is required'
        elif not password:
            error = 'Password is required'
        elif not db.execute('SELECT if FROM user WHERE username = ?', (username,)).fetchone() is not None: 
        # Validate that username is not already registered by querying the database and checking if a result is returned. 
        # db.execute takes a SQL query with ? placeholders for any user input, and a tuple of values to replace the placeholders with
        # fetchone() returns one row from the query.
            error = 'User {} is already registered'.format(username)

        if error is None: # If validation succeeds, insert the new user data into the database.
            db.execute('INSERT INTO user (username, password) VALUES (?, ?)', (username, generate_password_hash(password)))
            db.commit() # Since this query modifies data, db.commit() needs to be called afterwards to save the changes.
            return redirect(url_for('auth.login')) # After storing the user, they are redirected to the login page. url_for() generates the URL for the login view based on its name. redirect() generates a redirect response to the generated URL.

        flash(error) # If validation fails, the error is shown to the user. flash() stores messages that can be retrieved when rendering the template.

    return render_template('auth/register.html') # When the user initially navigates to auth/register, or there was a validation error, an HTML page with the registration form should be shown. render_template() will render a template containing the HTML


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone() # The user is queried first and stored in a variable for later use.

        if user is None:
            error = 'Incorrect username'
        elif not check_password_hash(user['password'], password): # hashes the submitted password in the same way as the stored hash and securely compares them
            error = 'Incorrect password'

        if error is None:
            # session is a dict that stores data across requests. When validation succeeds, the user’s id is stored in a new session.
            # The data is stored in a cookie that is sent to the browser, and the browser then sends it back with subsequent requests. 
            # Flask securely signs the data so that it can’t be tampered with.
            session.clear() 
            session['user_id'] = user['id'] # key 'user_id' in session dict. 
            return redirect(url_for('index')) 

        flash(error)

        return render_template('auth/login.html')


@bp.before_app_request # registers a function that runs before the view function, no matter what URL is requested
def load_logged_in_user(): # checks if a user id is stored in the session and gets that user’s data from the database, storing it on g.user, which lasts for the length of the request
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = db.execute('SELECT * FROM user WHERE id = ?'.format(user_id,)).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view): # This decorator returns a new view function that wraps the original view it’s applied to. The new function checks if a user is loaded and redirects to the login page otherwise
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login')) # The url_for() function generates the URL to a view based on a name and arguments. The name associated with a view is also called the endpoint, and by default it’s the same as the name of the view function.
        
        return view(**kwargs)
    
    return wrapped_view