#!/usr/bin/env python3

from flask import Flask, abort, url_for, jsonify, flash, json, redirect, \
                  render_template, request
from werkzeug import secure_filename

app = Flask(__name__)

from models import Base, Item, Category
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine("sqlite:///item_catalog.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

import os
import uuid

# APP_ROOT = os.path.dirname(os.path.abspath(__file__))
app.config["IMG_DIR"] = "static/images"

USER = { "username": "evblance", "password": "admin" }
TITLE = "ACME Trading"

logged_in = False

@app.route("/")
@app.route("/index")
def home():
    subheading = "Browse Catalog"
    categories = session.query(Category).all()
    return render_template("index.html",
                           title=TITLE,
                           subheading=subheading,
                           categories=categories,
                           logged_in=logged_in)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if (username == USER["username"]) and (password == USER["password"]):
            logged_in = True
            return redirect(url_for("home"))
        flash("Incorrect username or password.")
        return render_template("login.html", title=TITLE)
    if request.method == "GET":
        return render_template("login.html", title=TITLE)

@app.route("/logout", methods=["POST", "GET"])
def logout():
    return render_template("login.html")


@app.route("/category/<int:category_id>")
def displayCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category=category).all()
    subheading = "Displaying items for category '" + category.name + "'"
    return render_template("category.html",
                           title=TITLE,
                           subheading=subheading,
                           category=category,
                           items=items)

# Route for adding items
@app.route("/items/<int:category_id>/add", methods=["POST", "GET"])
def addItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    subheading = "Add items for category '{category}' (id: {id})" \
                     .format(category=category.name, id=category_id)
    last_item = session.query(Item).order_by(Item.id.desc()).first()
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

        session.add(new_item)
        session.commit()
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
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
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

        session.add(item)
        session.commit()
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
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    subheading = """
                 Deleting '{item_name}' (id: {item_id}") from category
                 '{cat_name}' (id: {cat_id}).
                 """.format(item_name=item.name, item_id=item_id,
                            cat_name=category.name, cat_id=category_id)

    if request.method == "POST":
        # delete the item
        session.delete(item)
        session.commit()
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

    category = session.query(Category).filter_by(id=category_id).one()
    category_items = session.query(Item).filter_by(category_id=category_id).all()
    subheading = "Deleting category '{name}' (id: {id})" \
                     .format(name=category.name, id=category_id)

    if request.method == "POST":

        # delete the category...
        session.delete(category)
        # ...followed by all items in the category
        for item in category_items:
            session.delete(item)

        session.commit()
        flash("Successfully deleted category '{}'.".format(category.name))
        return redirect(url_for("home"));

    elif request.method == "GET":
        flash(
            """
            Warning: This operation cannot be undone and will also delete all
            items associated with this category!
            """
        )
        return render_template("delete_category.html",
                               title=TITLE,
                               subheading=subheading,
                               category=category)
    else:
        return abort(400)

# Route for adding categories
@app.route("/categories/add", methods=["POST", "GET"])
def addCategories():
    subheading = "Add categories"
    last_category = session.query(Category).order_by(Category.id.desc()).first()
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

        session.add(new_category)
        session.commit()
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
    category = session.query(Category).filter_by(id=category_id).one()
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

        session.add(category)
        session.commit()
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
    category = session.query(Category).filter_by(id=category_id).one()
    category_items = session.query(Item).filter_by(category_id=category_id).all()
    subheading = "Deleting category '{name}' (id: {id})" \
                     .format(name=category.name, id=category_id)

    if request.method == "POST":

        # delete the category...
        session.delete(category)
        # ...followed by all items in the category
        for item in category_items:
            session.delete(item)

        session.commit()
        flash("Successfully deleted category '{}'.".format(category.name))
        return redirect(url_for("home"));

    elif request.method == "GET":
        flash(
            """
            Warning: This operation cannot be undone and will also delete all
            items associated with this category!
            """
        )
        return render_template("delete_category.html",
                               title=TITLE,
                               subheading=subheading,
                               category=category)
    else:
        return abort(400)



if __name__ == "__main__":
    app.secret_key = str(uuid.uuid4());
    app.debug = True
    app.run("127.0.0.1", port=5050)
