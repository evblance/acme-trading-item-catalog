#!/usr/bin/env python3

from flask import Flask, abort, url_for, jsonify, flash, make_response, \
                  redirect, render_template, request, session
from werkzeug import secure_filename

app = Flask(__name__)
# APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config["IMG_DIR"] = "static/images"

from models import Base, Item, Category, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
engine = create_engine("sqlite:///item_catalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
db_session = DBSession()

import os
import uuid
import json
from httplib2 import Http
import requests

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError, \
                                OAuth2Credentials

from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()
# from flask_login import LoginManager, login_user, logout_user, current_user, \
#                         login_required
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)



###################
#### CONSTANTS ####
###################

TITLE = "ACME Trading"
TOKEN_CHK_BASE_URL = \
    "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}"
TOKEN_REVOKE_BASE_URL = \
    "https://accounts.google.com/o/oauth2/revoke?token={}"
USER_INFO_URL = \
    "https://www.googleapis.com/oauth2/v1/userinfo"

LOGIN_VIEW = "login"

with open("data/client_secret.json", "r") as gcs:
    G_CLIENT_SECRET = json.loads(gcs.read())["web"]["client_id"]


##########################
#### HELPER FUNCTIONS ####
##########################

def makeRespObj(status_code, message):
    return {
        "status": status_code,
        "message": message
    }

def generateSessionToken():
    uuid_1 = str(uuid.uuid4())
    uuid_2 = str(uuid.uuid4())
    return (uuid_1 + uuid_2).replace("-", "")

def requireLogin():
    """ Function that returns True if user is not logged in """
    try:
        username = session["email"]
        print("requireLogin got username: {}".format(username))
        # must also check credentials here to see if token is still valid
    except KeyError:
        print("requireLogin could not find a username.")
        print("requireLogin will return: True")
        flash("You must log in to continue.")
        return True
    print("requireLogin will return: False")
    return False

#####################
#### AUTH ROUTES ####
#####################

@app.route("/login", methods=["POST", "GET"])
def login():
    # Set a new state for the login session
    session["state"] = generateSessionToken()

    # TODO: Server-side authentication
    # if request.method == "POST":
    #     username = request.form["username"]
    #     password = request.form["password"]
    #     if (username == USER["username"]) and (password == USER["password"]):
    #         return redirect(url_for("home"))
    #     flash("Incorrect username or password.")
    #     return render_template("login.html", title=TITLE)

    if request.method == "GET":
        return render_template("login.html",
                               title=TITLE,
                               STATE=session["state"])

@app.route("/logout", methods=["POST", "GET"])
def logout():
    # TODO: Add code to handle possibility of server-side authentication
    # NOTE: Needs to redirect to Google signout route if the user is logged
    #       in via OAuth2 through this provider.
    return redirect(url_for("googleLogout"))

# Route for handling Google OAuth2 signin
@app.route("/oauth2/google/signin", methods=["POST"])
def googleLogin():
    print("CHECKING STATE TOKEN \n")
    if request.args.get("state") != session["state"]:
        resp_data = makeRespObj(401, "Invalid state parameter.")
        response = jsonify(resp_data)
        response.status_code = 401
        return response
    print("Success\n")
    print("ATTEMPTING AUTH CODE UPGRADE TO CREDENTIALS...\n")
    auth_code = request.data
    try:
        # Upgrade the auth code into a credentials object
        oauth_flow = flow_from_clientsecrets("data/client_secret.json",
                                             scope="",
                                             redirect_uri="postmessage")

        credentials = oauth_flow.step2_exchange(auth_code)
    except FlowExchangeError:
        resp_data = makeRespObj(401, "Failed to upgrade auth code.")
        response = jsonify(resp_data)
        response.status_code = 401
        return response
    print("Success\n")
    # Check validity of access token
    access_token = credentials.access_token
    print("ACCESS TOKEN IS: {} \n".format(access_token))
    chk_url = TOKEN_CHK_BASE_URL.format(access_token)
    chk_result = json.loads(Http().request(chk_url, "GET")[1])
    print("CHECKING VALIDITY OF ACCESS TOKEN...\n")
    # Abort if access token not valid
    if chk_result.get("error") is not None:
        resp_data = makeRespObj(500, chk_result.get("error"))
        response = jsonify(resp_data)
        response.status_code = 500
        return response
    print("Passed\n")
    print("CHECKING TOKEN IS BEING USED BY INTENDED USER...\n")
    # Verify that the access token is being used by the intended user
    google_id = credentials.id_token["sub"]
    if chk_result["user_id"] != google_id:
        resp_data = makeRespObj(401, "Mismatched token and user IDs.")
        response = jsonify(resp_data)
        response.status_code = 401
        return response
    print("Passed\n")
    print("CHECKING THAT ACCESS TOKEN IS VALID FOR THIS APPLICATION...\n")
    # Verify that access token is valid for this application
    if chk_result["issued_to"] != G_CLIENT_SECRET:
        resp_data = makeRespObj(401, "Mismatched token and application IDs.")
        response = jsonify(resp_data)
        response.status_code = 401
        return response
    print("Passed\n")
    print("CHECKING THAT USER IS NOT ALREADY LOGGED IN...\n")
    # TODO: Check access token is till valid in database by comparing hash of credentials
    # Verify that the user is not already logged in so session variables do
    # not get unnecessarily reset
    saved_credentials = session.get("credentials")
    saved_google_id = session.get("google_id")
    if (saved_credentials is not None) and (google_id == saved_google_id):
        resp_data = makeRespObj(200, "Current user is already logged in.")
        response = jsonify(resp_data)
        response.status_code = 200
        return response
    print("Passed\n")
    print("STORING ACCESS TOKEN IN SESSION OBJECT...\n")
    # Store access token in session object
    session["credentials"] = credentials.access_token
    session["google_id"] = google_id
    print("Done\n")
    print("OBTAINING USER INFORMATION...\n")
    # Obtain user information
    params = {
        "access_token": session["credentials"],
        "alt": "json"
    }
    response = requests.get(USER_INFO_URL, params=params)
    user_data = json.loads(response.text)
    print("USER DATA IS: {}".format(user_data))
    print("STORING USER DATA IN SESSION...\n")


    # # Update user access_token if user exists in DB
    # try:
    #     print("RENEWING USER ACCESS TOKEN IN DB...\n")
    #     user = db_session.query(User).filter_by(username=user_data["email"]).one()
    #     user.g_access_token_hash = bcrypt.generate_password_hash(session["credentials"])
    #     db_session.commit()
    # except NoResultFound:
    #     # New user, so store under unique username (email) in database
    #     print("CREATING NEW USER IN DB...\n")
    #     user = User(
    #         username=user_data["email"],
    #         g_access_token_hash=bcrypt.generate_password_hash(session["credentials"]),
    #         authenticated=1)
    #     db_session.add(user)
    #     db_session.commit()

    # Store user information in session
    session["email"] = user_data["email"]
    print("User email is: {}\n".format(session["email"]))
    print("Redirecting\n")
    # flash("You are logged in via OAuth2 as: {}".format(session["email"]))
    return redirect(url_for("home"))

# Route for handling Google OAuth2 signout
@app.route("/oauth2/google/signout")
def googleLogout():
    # Only attempt logout if a user is connected
    access_token = session.get("credentials")
    if access_token is None:
        resp_data = makeRespObj(401, "Current user is not logged in.")
        response = jsonify(resp_data)
        response.status_code = 401
        return response

    revoke_url = TOKEN_REVOKE_BASE_URL.format(access_token)
    revoke_result = Http().request(revoke_url, "GET")[0]
    # Revoke access token
    if revoke_result["status"] == "200":
        # Reset the user session
        del session["credentials"]
        del session["google_id"]
        del session["email"]
        flash("Logged out was successfully.")
        # Let the user know that their logout was successful on redirect
        return redirect(url_for("home"))
    else:
        # Respond that the token was invalid
        resp_data = makeRespObj("Failed to revoke token for given user.", 400)
        response = jsonify(resp_data)
        response.status_code = 400
        return response



#####################
#### HTML ROUTES ####
#####################

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
        return redirect(url_for(LOGIN_VIEW))
    category = db_session.query(Category).filter_by(id=category_id).one()
    subheading = "Add items for category '{category}' (id: {id})" \
                     .format(category=category.name, id=category_id)
    last_item = db_session.query(Item).order_by(Item.id.desc()).first()
    image_dir = app.config["IMG_DIR"] \
                + "/categories/" \
                + str(category_id) \
                + "/items/" \
                + str(last_item.id + 1) + "/"

    if request.method == "POST":
        new_item = Item()
        new_item.category_id = category_id
        new_item.name = request.form["name"]
        new_item.price = "$" + request.form["price"]
        new_item.stock = request.form["stock"]
        new_item.description = request.form["description"]
        if not request.form["description"]:
            new_item.description = ""
        if request.files["image"]:
            # create the image folder for the item
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            uploaded_image = request.files["image"]
            safe_image = secure_filename(uploaded_image.filename)
            uploaded_image.save(os.path.join(image_dir, safe_image))
            new_item.image = os.path.join(image_dir, safe_image)

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
@app.route("/items/update/<int:category_id>/<int:item_id>", methods=["POST", "GET"])
def updateItem(item_id, category_id):
    if requireLogin():
        return redirect(url_for(LOGIN_VIEW))
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
            updated_decription = request.form["description"]
            item.description = updated_decription
        if request.files["image"]:
            # creates a directory for the item images if this was not
            # done during creation of item
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            uploaded_image = request.files["image"]
            safe_image = secure_filename(uploaded_image.filename)
            uploaded_image.save(os.path.join(image_dir, safe_image))
            item.image = os.path.join(image_dir, safe_image)

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
@app.route("/items/delete/<int:category_id>/<int:item_id>", methods=["POST", "GET"])
def deleteItem(item_id, category_id):
    if requireLogin():
        return redirect(url_for(LOGIN_VIEW))
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
        return redirect(url_for(LOGIN_VIEW))
    subheading = "Add categories"
    last_category = db_session.query(Category).order_by(Category.id.desc()).first()
    image_dir = app.config["IMG_DIR"] \
                + "/categories/" \
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
        return redirect(url_for(LOGIN_VIEW))
    category = db_session.query(Category).filter_by(id=category_id).one()
    subheading = "Updating category '{name}' (id: {id})" \
                     .format(name=category.name, id=category_id)


    if request.method == "POST":
        image_dir = app.config["IMG_DIR"] \
                    + "/categories/" \
                    + str(category_id) + "/"

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
        return redirect(url_for("home"));

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
        return redirect(url_for(LOGIN_VIEW))
    category = db_session.query(Category).filter_by(id=category_id).one()
    category_items = db_session.query(Item).filter_by(category_id=category_id).all()
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
        return redirect(url_for("home"));

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

####################
#### API ROUTES ####
####################

@app.errorhandler(400)
def badRequestError():
    resp_data = {
        "status": 400,
        "message": "Bad route on '{}' API endpoint." \
                       .format(request.url.split("?")[0])
    }
    response = jsonify(resp_data)
    response.status_code = 400
    return response


@app.route("/api/categories/json")
def getCategoriesJSON():
    if "mode" in request.args:
        if request.args["mode"] == "list":
            # Return a list of categories
            categories = db_session.query(Category).all()
            response = jsonify(Categories=[category.serialize["name"] for category in categories])
            response.status_code = 200
            return response
        elif request.args["mode"] == "search":
            # Return a 422 if mode is 'search' but no query provided
            if not "query" in request.args:
                resp_data = makeRespObj(422, "Must supply a value for 'query' parameter if using 'mode=search'")
                response = jsonify(resp_data)
                response.status_code = 422
                return response
            # Attempt to return a list of categories corresponding with the search term
            try:
                categories = db_session.query(Category).filter(
                                 Category.name.like("%{}%".format(request.args["query"]))
                             )
                response = jsonify(Categories=[category.serialize for category in categories])
                response.status_code = 200
                return response
            except NoResultFound:
                # Return a 404 if search query returned no categories
                resp_data = makeRespObj(404, "No categories found under this search term.")
                response = jsonify(resp_data)
                response.status_code = 404
                return response
        else:
            # Return a 422 if request did not provide acceptable option for the mode
            resp_data = makeRespObj(422, "Incorrect option for 'mode' parameter.")
            response = jsonify(resp_data)
            response.status_code = 422
            return response
    elif "id" in request.args:
        # Return a 422 if mutually exclusive parameters supplied
        if "name" in request.args:
            resp_data = makeRespObj(422, "Parameter 'name' cannot be used with 'id'.")
            response = jsonify(resp_data)
            response.status_code = 422
            return response
        # Attempt successful return of a category by ID
        try:
            category = db_session.query(Category).filter_by(id=request.args["id"]).one()
            response = jsonify(Categories=[category.serialize])
            response.status_code = 200
            return response
        except NoResultFound:
            # Return a 404 if no category found under this ID
            resp_data = makeRespObj(404, "No category corresponding to this ID.")
            response = jsonify(resp_data)
            response.status_code = 404
            return response
    elif "name" in request.args:
        # Return a 422 if mutually exclusive parameters supplied
        if "id" in request.args:
            resp_data = makeRespObj(422, "Parameter 'name' cannot be used with 'id'.")
            response = jsonify(resp_data)
            response.status_code = 422
            return response
        # Attempt to return a category by supplied name
        try:
            category = db_session.query(Category).filter(name=request.args["category_name"]).one()
            response = jsonify(Categories=[category.serialize for category in categories])
            response.status_code = 200
            return response
        except NoResultFound:
            # Return a 404 if no categories go by the provided name
            resp_data = makeRespObj(404, "No category found under this name.")
            response = jsonify(resp_data)
            response.status_code = 404
            return response
    else:
        return badRequestError()

@app.route("/api/items/json")
def getItemsJSON():
    if "mode" in request.args:
        if request.args["mode"] == "list":
            # Return a list of item names
            items = db_session.query(Item).all()
            response = jsonify(Items=[item.serialize["name"] for item in items])
            response.status_code = 200
            return response
        elif request.args["mode"] == "search":
            # Return a 422 if mode is 'search' but no query provided
            if not "query" in request.args:
                resp_data = makeRespObj(422, "Must supply a value for 'query' parameter if using 'mode=search'")
                response = jsonify(resp_data)
                response.status_code = 422
                return response
            # Attempt to return a list of items corresponding with the search term
            try:
                items = db_session.query(Item).filter(
                            Item.name.like("%{}%".format(request.args["query"])))
                response = jsonify(Items=[item.serialize for item in items])
                response.status_code = 200
                return response
            except NoResultFound:
                # Return a 404 if search query returned no items
                resp_data = makeRespObj(404, "No items found under this search term.")
                response = jsonify(resp_data)
                response.status_code = 404
                return response
        else:
            # Return a 422 if request did not provide acceptable option for the mode
            resp_data = makeRespObj(422, "Incorrect option for 'mode' parameter.")
            response = jsonify(resp_data)
            response.status_code = 422
            return response
    elif "category_id" in request.args:
        # Attempt to return all items based on a category ID
        items = db_session.query(Item).filter_by(category_id=request.args["category_id"]).all()
        response = jsonify(Items=[item.serialize for item in items])
        response.status_code = 200
        return response
    elif "id" in request.args:
        # Return a 422 if mutually exclusive parameters supplied
        if "name" in request.args:
            resp_data = makeRespObj(422, "Parameter 'name' cannot be used with 'id'.")
            response = jsonify(resp_data)
            response.status_code = 422
            return response
        # Attempt to return item information based on ID
        try:
            item = db_session.query(Item).filter_by(name=request.args["id"]).one()
            response = jsonify(Item=[item.serialze])
            response.status_code = 200
            return response
        except NoResultFound:
            # Return a 404 if no items correspond with the provided ID
            resp_data = makeRespObj(404, "No item found under this ID.")
            response = jsonify(resp_data)
            response.status_code = 404
            return response
    elif "name" in request.args:
        # Return a 422 if mutually exclusive parameters supplied
        if "id" in request.args:
            resp_data = makeRespObj(422, "Parameter 'id' cannot be used with 'name'.")
            response = jsonify(resp_data)
            response.status_code = 422
            return response
        # Attempt to return item information based on name
        try:
            item = db_session.query(Item).filter_by(name=request.args["name"]).one()
            response = jsonify(Item=[item.serialze])
            response.status_code = 200
            return response
        except NoResultFound:
            # Return a 404 if no items go by the provided name
            resp_data = makeRespObj(404, "No item found under this name.")
            response = jsonify(resp_data)
            response.status_code = 404
            return response
    else:
        return badRequestError()

################################################################################

if __name__ == "__main__":
    app.secret_key = str(uuid.uuid4());
    app.debug = True
    app.run("127.0.0.1", port=5050)
