#!/usr/bin/env python3

##################
# MODULE IMPORTS #
##################

from flask import Flask, abort, url_for, jsonify, flash, make_response, \
                  redirect, render_template, request, session
from werkzeug import secure_filename

from models import Base, Item, Category, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

import os
import uuid
import json
from httplib2 import Http
import requests

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError, \
                                OAuth2Credentials
from flask_bcrypt import Bcrypt
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, \
                         SignatureExpired
import bleach


##################
# INITIALIZATION #
##################

# Init Flask app
app = Flask(__name__)
app.config["IMG_DIR"] = os.path.join("static", "images")
app.config["SECRET_KEY"] = str(uuid.uuid4()).replace("-", "")
bcrypt = Bcrypt(app)

# Init database and SQLAlchemy database session instance
engine = create_engine("sqlite:///item_catalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


#############
# CONSTANTS #
#############

# Sets the title for the app
TITLE = "ACME Trading"

# Sets the value for session access token timeout
TOKEN_TIMEOUT = 900

# Google OAuth2 URLs
G_TOKEN_CHK_BASE_URL = \
"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}"
G_TOKEN_REVOKE_BASE_URL = \
"https://accounts.google.com/o/oauth2/revoke?token={}"
G_USER_INFO_URL = \
"https://www.googleapis.com/oauth2/v1/userinfo"

# Google Auth2 Client secret
with open("data/client_secret.json", "r") as gcs:
    G_CLIENT_SECRET = json.loads(gcs.read())["web"]["client_id"]


####################
# HELPER FUNCTIONS #
####################

def jsonRespObj(status_code, message):
    """ Returns a jsonified response object to be sent to the client """
    resp_data = {
        "status": status_code,
        "message": message
    }
    response = jsonify(resp_data)
    response.status_code = status_code
    return response


def generateToken():
    """ Returns a string representing a token """
    uuid_1 = str(uuid.uuid4())
    uuid_2 = str(uuid.uuid4())
    return (uuid_1 + uuid_2).replace("-", "")


def checkPassword(user, password):
    """ Returns True if password is correct for the user """
    return bcrypt.check_password_hash(user.password_hash, password)


def generateTimedAccessToken(seconds):
    """ Returns a signed token to the user with specified TTL """
    token_signer = TimedJSONWebSignatureSerializer(
                       app.config["SECRET_KEY"],
                       expires_in=seconds
                   )
    token = generateToken()
    return token_signer.dumps({"token": token})


def checkToken(token):
    """ Returns True if provided token is current and valid """
    token_signer = TimedJSONWebSignatureSerializer(
                       app.config["SECRET_KEY"]
                   )
    try:
        challenge = token_signer.loads(token.encode())
    except SignatureExpired:
        # Token is valid but has an expired signature
        return False
    except BadSignature:
        # Token is invalid
        return False
    return True


def refreshSessionAccessToken(seconds):
    """
    Refreshes a server-side authenticated user's login session

    Refreshes a server-side authenticated user's login session token and
    returns True if successful
    """
    # Only refresh access token if a valid one already exists
    if session.get("access_token") is None:
        return False
    session["access_token"] = generateTimedAccessToken(seconds).decode()
    return True


def setSessionAccessToken(seconds):
    """ Sets a server-side authenticated user's login session access token """
    session["access_token"] = generateTimedAccessToken(seconds).decode()


def requireLogin():
    """ Function that returns True if user is not logged in """
    # Session must have an authenticated username (email) assigned
    if session.get("email") is None:
        flash("You must log in to continue.")
        return True
    # Google OAuth2 sessions are exempt from server-side expiry
    if session.get("google_id") is not None:
        return False
    # Login session cannot be stale
    if (session.get("access_token") is None) or \
            (not checkToken(session["access_token"])):
        if session.get("email") is not None:
            del session["email"]
        flash("Session expired.")
        return True
    # Login session must be able to refresh correctly
    if not refreshSessionAccessToken(TOKEN_TIMEOUT):
        if session.get("email") is not None:
            del session["email"]
        flash("Could not confirm valid user access.")
        return True
    return False


def validEmailInput(email):
    """ Function that performs (very) simple email validation """
    if "@" and "." not in email:
        return False
    return True


def validPasswordInput(password):
    """ Function that performs password validation """
    if len(password) < 8:
        # Password need to be at least 8 charcters long
        return False
    elif " " in password:
        # No spaces are allowed in password
        return False
    return True


###############
# AUTH ROUTES #
###############

@app.route("/login", methods=["POST", "GET"])
def login():

    if request.method == "POST":
        # Attempt to validate state token
        if session.get("state") != request.form.get("state"):
            flash("Invalid login session.")
            return redirect(url_for("login"))
        # Do some basic input sanitization and validation
        username = bleach.clean(request.form["username"])
        username = username.lower()
        if not validEmailInput(username):
            flash("Incorrect username or password.")
            return redirect(url_for("login"))
        password = bleach.clean(request.form["password"])
        # Try to load the user attempting login
        try:
            user = db_session.query(User).filter_by(username=username).one()
        except NoResultFound:
            flash("Incorrect username or password.")
            return redirect(url_for("login"))
        # Log user in if supplied password is correct and store a
        # timed access token...
        if checkPassword(user, password):
            session["email"] = username
            setSessionAccessToken(TOKEN_TIMEOUT)
            flash("You are now logged in as '{}'."
                  .format(session["email"]))
            return redirect(url_for("home"))
        else:
            # ...otherwise redirect to login screen with feedback
            flash("Incorrect username or password.")
            return redirect(url_for("login"))

    if request.method == "GET":
        # Set a new state for the login session
        session["state"] = generateToken()
        return render_template("login.html",
                               title=TITLE,
                               STATE=session["state"])


@app.route("/logout", methods=["POST", "GET"])
def logout():
    # Redirect to appropriate URL if login is via  OAuth2
    if session.get("google_id"):
        return redirect(url_for("googleLogout"))
    else:
        # Reset session
        if session.get("email") is not None:
            del session["email"]
        # Let the user know they logged in successfully upon redirect
        flash("Logged out successfully.")
        return redirect(url_for("home"))


# Route for handling Google OAuth2 signin
@app.route("/oauth2/google/signin", methods=["POST"])
def googleLogin():
    # Validate state token
    if session.get("state") != request.args.get("state"):
        return jsonRespObj(401, "Invalid state parameter.")

    # Attempt upgrade of auth code into a credentials object
    auth_code = request.data
    try:
        oauth_flow = flow_from_clientsecrets("data/client_secret.json",
                                             scope="",
                                             redirect_uri="postmessage")
        credentials = oauth_flow.step2_exchange(auth_code)
    except FlowExchangeError:
        return jsonRespObj(401, "Failed to upgrade auth code.")

    # Check validity of access token
    access_token = credentials.access_token
    chk_url = G_TOKEN_CHK_BASE_URL.format(access_token)
    chk_result = json.loads(Http().request(chk_url, "GET")[1])
    # Abort if access token not valid
    if chk_result.get("error") is not None:
        return jsonRespObj(500, chk_result.get("error"))

    # Verify that the access token is being used by the intended user
    google_id = credentials.id_token["sub"]
    if chk_result["user_id"] != google_id:
        return jsonRespObj(401, "Mismatched token and user IDs.")

    # Verify that access token is valid for this application
    if chk_result["issued_to"] != G_CLIENT_SECRET:
        return jsonRespObj(401, "Mismatched token and application IDs.")

    # Verify that the user is not already logged in so session variables do
    # not get unnecessarily reset
    saved_credentials = session.get("credentials")
    saved_google_id = session.get("google_id")
    if (saved_credentials is not None) and (google_id == saved_google_id):
        return jsonRespObj(200, "Current user is already logged in.")

    # Store access token in session object
    session["credentials"] = credentials.access_token
    session["google_id"] = google_id

    # Obtain user information
    params = {
        "access_token": session["credentials"],
        "alt": "json"
    }
    response = requests.get(G_USER_INFO_URL, params=params)
    user_data = json.loads(response.text)

    # Store user information in session
    session["email"] = user_data["email"]
    return redirect(url_for("home"))


# Route for handling Google OAuth2 signout
@app.route("/oauth2/google/signout")
def googleLogout():
    # Only attempt logout if a user is connected
    access_token = session.get("credentials")
    if access_token is None:
        return jsonRespObj(401, "Current user is not logged in.")

    revoke_url = G_TOKEN_REVOKE_BASE_URL.format(access_token)
    revoke_result = Http().request(revoke_url, "GET")[0]
    # Revoke access token
    if revoke_result["status"] == "200":
        # Reset the user session
        del session["credentials"]
        del session["google_id"]
        del session["email"]
        flash("Logged out successfully.")
        # Let the user know that their logout was successful on redirect
        return redirect(url_for("home"))
    else:
        # Respond that the token was invalid
        return jsonRespObj("Failed to revoke token for given user.", 400)


###############
# HTML ROUTES #
###############

@app.route("/")
@app.route("/index")
def home():
    subheading = "Browse Catalog"
    categories = db_session.query(Category).all()
    return render_template("index.html",
                           title=TITLE,
                           subheading=subheading,
                           categories=categories)


@app.route("/category/<int:category_id>")
def displayCategory(category_id):
    category = db_session.query(Category).filter_by(id=category_id).one()
    items = db_session.query(Item).filter_by(category=category).all()
    subheading = "Displaying items for category '" + category.name + "'"
    return render_template("category.html",
                           title=TITLE,
                           subheading=subheading,
                           category=category,
                           items=items)


# Route for adding items
@app.route("/items/<int:category_id>/add", methods=["POST", "GET"])
def addItems(category_id):
    if requireLogin():
        return redirect(url_for("login"))
    category = db_session.query(Category).filter_by(id=category_id).one()
    subheading = "Add items for category '{category}' (id: {id})" \
                 .format(category=category.name, id=category_id)
    last_item = db_session.query(Item).order_by(Item.id.desc()).first()
    image_dir = app.config["IMG_DIR"] + "/categories/" + str(category_id) \
        + "/items/" + str(last_item.id + 1) + "/"

    if request.method == "POST":
        new_item = Item()
        new_item.category_id = category_id
        new_item.name = request.form["name"]
        new_item.price = "$" + request.form["price"]
        new_item.stock = request.form["stock"]
        new_item.description = request.form["description"]
        if not request.form["description"]:
            new_item.description = ""
        # TODO: Add item image functionality
        # if request.files["image"]:
        #     # create the image folder for the item
        #     if not os.path.exists(image_dir):
        #         os.makedirs(image_dir)
        #     uploaded_image = request.files["image"]
        #     safe_image = secure_filename(uploaded_image.filename)
        #     uploaded_image.save(os.path.join(image_dir, safe_image))
        #     new_item.image = os.path.join(image_dir, safe_image)

        db_session.add(new_item)
        db_session.commit()
        flash("Successfully added item '{}'.".format(new_item.name))
        return redirect(url_for("displayCategory", category_id=category_id))

    elif request.method == "GET":
        return render_template("add_items.html",
                               title=TITLE,
                               subheading=subheading,
                               category=category)

    else:
        return abort(400)


# Route for updating item data
@app.route("/items/update/<int:category_id>/<int:item_id>",
           methods=["POST", "GET"])
def updateItem(item_id, category_id):
    if requireLogin():
        return redirect(url_for("login"))
    category = db_session.query(Category).filter_by(id=category_id).one()
    item = db_session.query(Item).filter_by(id=item_id).one()
    subheading = """
                 Updating item '{item_name}' (id: {item_id}) in category
                 '{cat_name}' (id: {cat_id})
                 """.format(item_name=item.name, item_id=item_id,
                            cat_name=category.name, cat_id=category.id)

    if request.method == "POST":
        image_dir = app.config["IMG_DIR"] \
                    + "/categories/" \
                    + str(category_id) \
                    + "/items/" \
                    + str(item.id) + "/"

        # default the updated data to existing
        updated_name = item.name
        updated_price = item.price
        updated_stock = item.stock
        if item.description:
            updated_description = item.description
        if item.image:
            updated_image = item.image

        if request.form["name"]:
            updated_name = request.form["name"]
            item.name = updated_name
        if request.form["price"]:
            updated_price = request.form["price"]
            item.price = "$" + updated_price
        if request.form["stock"]:
            updated_stock = request.form["stock"]
            item.stock = updated_stock
        if request.form["description"]:
            updated_description = request.form["description"]
            item.description = updated_description
        # TODO: Add item image functionality
        # if request.files["image"]:
        #     # creates a directory for the item images if this was not
        #     # done during creation of item
        #     if not os.path.exists(image_dir):
        #         os.makedirs(image_dir)
        #     uploaded_image = request.files["image"]
        #     safe_image = secure_filename(uploaded_image.filename)
        #     uploaded_image.save(os.path.join(image_dir, safe_image))
        #     item.image = os.path.join(image_dir, safe_image)

        db_session.add(item)
        db_session.commit()
        flash("Successfully updated item '{}'.".format(item.name))
        return redirect(url_for("displayCategory", category_id=category_id))

    elif request.method == "GET":
        return render_template("update_item.html",
                               title=TITLE,
                               subheading=subheading,
                               category=category,
                               item=item)

    else:
        return abort(400)


# Route for deleting items
@app.route("/items/delete/<int:category_id>/<int:item_id>",
           methods=["POST", "GET"])
def deleteItem(item_id, category_id):
    if requireLogin():
        return redirect(url_for("login"))
    category = db_session.query(Category).filter_by(id=category_id).one()
    item = db_session.query(Item).filter_by(id=item_id).one()
    subheading = """
                 Deleting '{item_name}' (id: {item_id}") from category
                 '{cat_name}' (id: {cat_id}).
                 """.format(item_name=item.name, item_id=item_id,
                            cat_name=category.name, cat_id=category_id)

    if request.method == "POST":
        # delete the item
        db_session.delete(item)
        db_session.commit()
        flash("Successfully deleted item '{}'.".format(item.name))
        return redirect(url_for("displayCategory", category_id=category_id))

    elif request.method == "GET":
        flash("Warning: This operation cannot be undone!")
        return render_template("delete_item.html",
                               title=TITLE,
                               subheading=subheading,
                               category=category,
                               item=item)

    else:
        return abort(400)


# Route for adding categories
@app.route("/categories/add", methods=["POST", "GET"])
def addCategories():
    if requireLogin():
        return redirect(url_for("login"))
    subheading = "Add categories"
    last_category = db_session.query(Category).order_by(
                        Category.id.desc()
                    ).first()
    image_dir = app.config["IMG_DIR"] + "/categories/" \
        + str(last_category.id + 1) + "/"

    if request.method == "POST":
        new_category = Category()
        new_category.name = request.form["name"]
        if request.files["image"]:
            # create the image folder for the category
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
                os.makedirs(os.path.join(image_dir, 'items'))
            uploaded_image = request.files["image"]
            safe_image = secure_filename(uploaded_image.filename)
            uploaded_image.save(os.path.join(image_dir, safe_image))
            new_category.image = os.path.join(image_dir, safe_image)

        db_session.add(new_category)
        db_session.commit()
        flash("Successfully added category '{}'.".format(new_category.name))
        return redirect(url_for("home"))

    elif request.method == "GET":
        return render_template("add_categories.html",
                               title=TITLE,
                               subheading=subheading)

    else:
        return abort(400)


# Route for updating category data
@app.route("/categories/update/<int:category_id>", methods=["POST", "GET"])
def updateCategory(category_id):
    if requireLogin():
        return redirect(url_for("login"))
    category = db_session.query(Category).filter_by(id=category_id).one()
    subheading = "Updating category '{name}' (id: {id})" \
                 .format(name=category.name, id=category_id)

    if request.method == "POST":
        image_dir = app.config["IMG_DIR"] + "/categories/" + str(category_id) \
            + "/"

        # default the updated data to existing
        updated_name = category.name
        updated_image = category.image

        if request.form["name"]:
            updated_name = request.form["name"]
            category.name = updated_name
        if request.files["image"]:
            # creates a directory for the category images if this was not
            # done during creation of category
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
                os.makedirs(os.path.join(image_dir, 'items'))
            uploaded_image = request.files["image"]
            safe_image = secure_filename(uploaded_image.filename)
            uploaded_image.save(os.path.join(image_dir, safe_image))
            category.image = os.path.join(image_dir, safe_image)

        db_session.add(category)
        db_session.commit()
        flash("Successfully updated category '{}'.".format(category.name))
        return redirect(url_for("home"))

    elif request.method == "GET":
        return render_template("update_category.html",
                               title=TITLE,
                               subheading=subheading,
                               category=category)

    else:
        return abort(400)


@app.route("/categories/delete/<int:category_id>", methods=["POST", "GET"])
def deleteCategory(category_id):
    if requireLogin():
        return redirect(url_for("login"))
    category = db_session.query(Category).filter_by(id=category_id).one()
    category_items = db_session.query(Item).filter_by(
                         category_id=category_id
                     ).all()
    subheading = "Deleting category '{name}' (id: {id})" \
                 .format(name=category.name, id=category_id)

    if request.method == "POST":

        # delete the category...
        db_session.delete(category)
        # ...followed by all items in the category
        for item in category_items:
            db_session.delete(item)

        db_session.commit()
        flash("Successfully deleted category '{}'.".format(category.name))
        return redirect(url_for("home"))

    elif request.method == "GET":
        flash(
            """
            Warning: This operation cannot be undone and will also delete all
            items associated within this category!
            """
        )
        return render_template("delete_category.html",
                               title=TITLE,
                               subheading=subheading,
                               category=category)
    else:
        return abort(400)


##############
# API ROUTES #
##############

# ERROR HANDLERS #

@app.errorhandler(400)
def badRequestError():
    resp_data = {
        "status": 400,
        "message": "Bad route on '{}' API endpoint."
                   .format(request.url.split("?")[0])
    }
    response = jsonify(resp_data)
    response.status_code = 400
    return response


@app.errorhandler(401)
def unauthenticatedError():
    resp_data = {
        "status": 401,
        "message": "Invalid or expired access token."
    }
    response = jsonify(resp_data)
    response.status_code = 401
    return response


# AUTH ROUTES #

@app.route("/api/registration", methods=["POST"])
def APIRegisterUser():
    # Reject registration attempt if user and password are missing
    if "username" and "password" not in request.args:
        return jsonRespObj(
                   422,
                   "Registrant must provide both an email and password."
               )
    # Validate email input
    if not validEmailInput(request.args["username"]):
        return jsonRespObj(
                   400,
                   "Registration requires a valid email address."
               )
    # Validate password input
    if not validPasswordInput(request.args["password"]):
        return jsonRespObj(
                   400,
                   "Registrant's password must contain at least 8 " +
                   "symbols but no spaces."
               )
    # Only register a new user if the email address (username) does
    # not exist already in DB
    try:
        pw_hash = bcrypt.generate_password_hash(request.args["password"])
        new_user = User(
                       username=request.args["username"].lower(),
                       password_hash=pw_hash
                   )
        db_session.add(new_user)
        db_session.commit()
    except:
        db_session.rollback()
        return jsonRespObj(500, "Email address already exists in DB.")
    # Return a 200 for successful registration of a new user
    return jsonRespObj(
               200,
               "Successfully registered new user '{}'"
               .format(request.args["username"])
           )


@app.route("/api/tokens", methods=["POST"])
def APIRegisterToken():
    # Reject token request if user and password are missing
    if "username" and "password" not in request.args:
        return jsonRespObj(
                   422,
                   "Credentials must be provided to obtain an access token."
               )
    try:
        user = db_session.query(User).filter_by(
                   username=request.args["username"]
               ).one()
    except NoResultFound:
        # If no DB record for this user, return an error
        return jsonRespObj(400, "Incorrect username or password.")
    # If password is correct, generate a timed token for the user
    # and send back with a 200
    if checkPassword(user, request.args["password"]):
        token = generateTimedAccessToken(TOKEN_TIMEOUT)
        resp_data = {
            "status": 200,
            "token": token.decode(),
            "TTL": TOKEN_TIMEOUT
        }
        response = jsonify(resp_data)
        response.status_code = 200
        return response
    else:
        # Return 400 for bad username or password
        return jsonRespObj(400, "Incorrect username or password.")


# GET ROUTES #

@app.route("/api/categories/json")
def getCategoriesJSON():
    if "mode" in request.args:
        if request.args["mode"] == "list":
            # Return a list of categories
            categories = db_session.query(Category).all()
            response = jsonify(Categories=[category.serialize
                                           for category in categories])
            response.status_code = 200
            return response
        elif request.args["mode"] == "search":
            # Return a 422 if mode is 'search' but no query provided
            if "query" not in request.args:
                return jsonRespObj(
                           422,
                           "Must supply a value for 'query' parameter" +
                           " if using 'mode=search'"
                       )
            # Attempt to return a list of categories corresponding with
            # the search term
            try:
                categories = db_session.query(Category).filter(
                                 Category.name.like("%{}%".format(
                                     request.args["query"]
                                 ))
                             )
                response = jsonify(QueryCategories=[
                               category.serialize for category in categories
                           ])
                response.status_code = 200
                return response
            except NoResultFound:
                # Return a 404 if search query returned no categories
                return jsonRespObj(
                           404,
                           "No categories found under this search term."
                       )
        else:
            # Return a 422 if request did not provide acceptable option
            # for the mode
            return jsonRespObj(
                       422,
                       "Incorrect option for 'mode' parameter."
                   )
    elif "id" in request.args:
        # Return a 422 if mutually exclusive parameters supplied
        if "name" in request.args:
            return jsonRespObj(
                       422,
                       "Parameter 'name' cannot be used with 'id'."
                   )
        # Attempt successful return of a category by ID
        try:
            category = db_session.query(Category).filter_by(
                           id=request.args["id"]
                       ).one()
            response = jsonify(Category=[category.serialize])
            response.status_code = 200
            return response
        except NoResultFound:
            # Return a 404 if no category found under this ID
            return jsonRespObj(404, "No category corresponding to this ID.")
    elif "name" in request.args:
        # Return a 422 if mutually exclusive parameters supplied
        if "id" in request.args:
            return jsonRespObj(
                       422,
                       "Parameter 'name' cannot be used with 'id'."
                   )
        # Attempt to return a category by supplied name
        try:
            category = db_session.query(Category).filter(
                           name=request.args["category_name"]
                       ).one()
            response = jsonify(Categories=[category.serialize
                                           for category in categories])
            response.status_code = 200
            return response
        except NoResultFound:
            # Return a 404 if no categories go by the provided name
            return jsonRespObj(404, "No category found under this name.")
    else:
        return badRequestError()


@app.route("/api/items/json")
def getItemsJSON():
    if "mode" in request.args:
        if request.args["mode"] == "list":
            # Return a list of item names
            items = db_session.query(Item).all()
            response = jsonify(Items=[{
                           "name": item.serialize["name"],
                           "id": item.serialize["id"]
                       } for item in items])
            response.status_code = 200
            return response
        elif request.args["mode"] == "search":
            # Return a 422 if mode is 'search' but no query provided
            if "query" not in request.args:
                return jsonRespObj(
                           422,
                           "Must supply a value for 'query' parameter" +
                           " if using 'mode=search'."
                       )
            # Attempt to return a list of items corresponding with the
            # search term
            try:
                items = db_session.query(Item).filter(
                            Item.name.like("%{}%".format(
                                request.args["query"]
                            ))
                        )
                response = jsonify(QueryItems=[item.serialize
                                               for item in items])
                response.status_code = 200
                return response
            except NoResultFound:
                # Return a 404 if search query returned no items
                return jsonRespObj(
                           404,
                           "No items found under this search term."
                       )
        else:
            # Return a 422 if request did not provide acceptable option for
            # the mode
            return jsonRespObj(
                       422,
                       "Incorrect option for 'mode' parameter."
                   )
    elif "category_id" in request.args:
        # Attempt to return all items based on a category ID
        items = db_session.query(Item).filter_by(
                    category_id=request.args["category_id"]
                ).all()
        response = jsonify(Items=[item.serialize for item in items])
        response.status_code = 200
        return response
    elif "id" in request.args:
        # Return a 422 if mutually exclusive parameters supplied
        if "name" in request.args:
            return jsonRespObj(
                       422,
                       "Parameter 'name' cannot be used with 'id'."
                   )
        # Attempt to return item information based on ID
        try:
            item = db_session.query(Item).filter_by(
                       name=request.args["id"]
                   ).one()
            response = jsonify(Item=[item.serialze])
            response.status_code = 200
            return response
        except NoResultFound:
            # Return a 404 if no items correspond with the provided ID
            return jsonRespObj(404, "No item found under this ID.")
    elif "name" in request.args:
        # Return a 422 if mutually exclusive parameters supplied
        if "id" in request.args:
            return jsonRespObj(
                       422,
                       "Parameter 'id' cannot be used with 'name'."
                   )
        # Attempt to return item information based on name
        try:
            item = db_session.query(Item).filter_by(
                       name=request.args["name"]
                   ).one()
            response = jsonify(Item=[item.serialze])
            response.status_code = 200
            return response
        except NoResultFound:
            # Return a 404 if no items go by the provided name
            return jsonRespObj(404, "No item found under this name.")
    else:
        return badRequestError()


# POST ROUTES #

@app.route("/api/add/category", methods=["POST"])
def APIAddCategory():
    # Reject with a 422 if token parameter not provided
    if "token" not in request.args:
        return jsonRespObj(
                   422,
                   "An access token is required to perform this request."
               )
    # Check whether API user has supplied a valid access token
    if not checkToken(request.args["token"]):
        return unauthenticatedError()
    # A name must be provided for the category
    if "name" not in request.args:
        return jsonRespObj(
                   422,
                   "Name must be provided for category to be added."
               )
    # Create a new category object and commit to DB
    try:
        new_category = Category(name=request.args["name"])
        db_session.add(new_category)
        db_session.commit()
    except:
        # If category could not be created, return a 500
        return jsonRespObj(
                   500,
                   "Server-side error occurred during category creation."
               )
    # Return a 200 to user on successful creation of category
    return jsonRespObj(
               200,
               "Successfully added category '{}' to database."
               .format(request.args["name"])
           )
    response = jsonify(resp_data)
    response.status_code = 200
    return response


@app.route("/api/add/item", methods=["POST"])
def APIAddItem():
    # Reject with a 422 if token parameter not provided
    if "token" not in request.args:
        return jsonRespObj(
                   422,
                   "An access token is required to perform this request."
               )
    # Check whether API user has supplied a valid access token
    if not checkToken(request.args["token"]):
        return unauthenticatedError()
    # Item name, category ID, and price must be provided
    # to add an item (stock will default to 0)
    if "name" not in request.args:
        return jsonRespObj(
                   422,
                   "Item name must be provided for item to be added."
               )
    elif "category_id" not in request.args:
        return jsonRespObj(
                   422,
                   "Category ID must be provided for item to be added."
               )
    elif "price" not in request.args:
        return jsonRespObj(
                   422,
                   "Price must be provided for item to be added."
               )

    # Create a new item object
    new_item = Item()

    # Default stock level to 0 parameter/value not provided
    if "stock" not in request.args:
        new_item.stock = 0
    else:
        new_item.stock = request.args["stock"]

    if "description" in request.args:
        new_item.description = request.args["description"]

    # Attempt to add the new item to DB
    try:
        new_item.name = request.args["name"]
        # Make sure that the price is registered in currency
        if request.args["price"][0] != "$":
            new_item.price = "$" + request.args["price"]
        else:
            new_item.price = request.args["price"]
        new_item.category_id = request.args["category_id"]
        db_session.add(new_item)
        db_session.commit()
    except:
        # If item could not be created, return a 500
        return jsonRespObj(
                   500,
                   "Server-side error occurred during item creation."
               )
    # Return a 200 to user on successful creation of item
    return jsonRespObj(
               200,
               "Successfully added item '{}' to database."
               .format(request.args["name"])
            )


# PUT ROUTES #

@app.route("/api/update/category", methods=["PUT"])
def APIUpdateCategory():
    # Reject with a 422 if token parameter not provided
    if "token" not in request.args:
        return jsonRespObj(
                   422,
                   "An access token is required to perform this request."
               )
    # Check whether API user has supplied a valid access token
    if not checkToken(request.args["token"]):
        return unauthenticatedError()
    # Reject request with a 422 if no category ID s provided
    if "id" not in request.args:
        return jsonRespObj(
                   422,
                   "Category ID must be provided to execute request."
               )

    # Load the category to update if ID is valid, otherwise return a 404
    try:
        category = db_session.query(Category).filter_by(
                       id=request.args["id"]
                   ).one()
    except NoResultFound:
        return jsonRespObj(404, "No category to update found under this ID.")
    if "name" not in request.args:
        return jsonRespObj(
                   422,
                   "Nothing to update if a new name not provided."
               )
    # Attempt category update
    try:
        category.name = request.args["name"]
        db_session.commit()
    except:
        # If category could not be updated, return a 500
        return jsonRespObj(
                   500,
                   "Server-side error occurred during category update."
               )
    # Return a 200 to user for successful update of category
    return jsonRespObj(
               200,
               "Successfully updated category '{}'".format(category.name)
           )


@app.route("/api/update/item", methods=["PUT"])
def APIUpdateItem():
    # Reject with a 422 if token parameter not provided
    if "token" not in request.args:
        return jsonRespObj(
                   422,
                   "An access token is required to perform this request."
               )
    # Check whether API user has supplied a valid access token
    if not checkToken(request.args["token"]):
        return unauthenticatedError()
    if "id" not in request.args:
        return jsonRespObj(
                   422,
                   "Item ID must be provided to execute request."
               )

    # Load the item to update if ID is valid, otherwise return a 404
    try:
        item = db_session.query(Item).filter_by(
                       id=request.args["id"]
                   ).one()
    except NoResultFound:
        return jsonRespObj(404, "No item to update found under this ID.")
    if ("name" or "price" or "stock" or "description") not in request.args:
        return jsonRespObj(
                   422,
                   "Nothing to update if no new data is provided."
               )

    old_name = item.name

    if "name" in request.args:
        item.name = request.args["name"]
    if "price" in request.args:
        if request.args["price"][0] != "$":
            item.price = "$" + request.args["price"]
        else:
            item.price = request.args["price"]
    if "stock" in request.args:
        item.stock = request.args["stock"]
    if "description" in request.args:
        item.description = request.args["description"]

    # Attempt item update
    try:
        db_session.commit()
    except:
        # If item could not be updated, return a 500
        return jsonRespObj(
                   500,
                   "Server-side error occurred during item update."
               )
    # Return a 200 to user for successful update of item
    return jsonRespObj(
               200,
               "Successfully updated item '{}'".format(old_name)
           )


# DELETE ROUTES #

@app.route("/api/delete/category", methods=["DELETE"])
def APIDeleteCategory():
    # Reject with a 422 if token parameter not provided
    if "token" not in request.args:
        return jsonRespObj(
                   422,
                   "An access token is required to perform this request."
               )
    # Check whether API user has supplied a valid access token
    if not checkToken(request.args["token"]):
        return unauthenticatedError()
    # Reject with a 422 if ID parameter/value not present
    if "id" not in request.args:
        return jsonRespObj(
                   422,
                   "Category ID must be provided to execute request."
               )

    # Load the category delete if ID is valid, otherwise return a 404
    try:
        category = db_session.query(Category).filter_by(
                       id=request.args["id"]
                   ).one()
    except NoResultFound:
        return jsonRespObj(404, "No category to delete found under this ID.")

    old_name = category.name

    # Attempt to delete the category and all associated items
    try:
        items = db_session.query(Item).filter_by(
                    category_id=request.args["id"]
                )
        for item in items:
            db_session.delete(item)
        db_session.delete(category)
        db_session.commit()
    except:
        # Return a 500 if category could not be deleted
        return jsonRespObj(
                   500,
                   "Server-side error occurred during category deletion."
               )
    # Return a 200 for successful deletion
    return jsonRespObj(
               200,
               "Successfully deleted category '{}' and all associated items"
               .format(old_name)
           )


@app.route("/api/delete/item", methods=["DELETE"])
def APIDeleteItem():
    # Reject with a 422 if token parameter not provided
    if "token" not in request.args:
        return jsonRespObj(
                   422,
                   "An access token is required to perform this request."
               )
    # Check whether API user has supplied a valid access token
    if not checkToken(request.args["token"]):
        return unauthenticatedError()
    # Reject with a 422 if ID parameter/value not present
    if "id" not in request.args:
        return jsonRespObj(
                   422,
                   "Item ID must be provided to execute request."
               )
    # Load the item to delete if ID is valid, otherwise return a 404
    try:
        item = db_session.query(Item).filter_by(
                       id=request.args["id"]
                   ).one()
    except NoResultFound:
        return jsonRespObj(404, "No item to delete found under this ID.")

    old_name = item.name
    # Attempt to delete the item
    try:
        item.delete()
        db_session.commit()
    except:
        # Return a 500 if item could not be deleted
        return jsonRespObj(
                   500,
                   "Server-side error occurred during item deletion."
               )
    # Return a 200 for successful deletion
    return jsonRespObj(
               200,
               "Successfully deleted item '{}'".format(old_name)
           )

###############################################################################

if __name__ == "__main__":
    app.debug = True
    app.run("127.0.0.1", port=5050)
