# ACME Trading Item Catalog
A quirky Full-Stack CRUD application leveraging OAuth2 authentication via Google in fulfillment of the Udacity FSND Item Catalog project. It uses Python 3 (Flask microframework), SQLAlchemy, D3.js and Bootstrap, also providing a RESTful API.

# Requirements
You will need to ensure that Python 3 is available on your system and that the required dependencies are installed for the backend to function. Refer to the module imports in `views.py` and `models.py` for details. Consider using a [Virtual Environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) if you do not wish to taint your existing Python environment.

# How to run the app
Before first run, it is best to initialize the database with some starter data. This is performed by running the following commands from the app's root directory:

  1. `python models.py`
  2. `python populate_db.py`

The application can then be launched by running `python views.py` which will start the HTTP server. The user interface can then be accessed by navigating your browser to `http://localhost:5050`.

# How to use the API
The app provides two API endpoints for querying information about categories and items, which return JSON.

API Endpoint | Method | Parameters | Accepted vals
-- | -- | -- | --
localhost:5050/api/items/json | GET | id | An integer category ID
|| | name | A string representing the category name
|| | mode | *list*, *search*
|| | query | A string representing a search query
||
localhost:5050/api/categories/json | GET | id | An integer item ID
|| | name | A string representing the item name
|| | mode | *list*, *search*
|| | query | A string representing a search query

Note: If *mode* is 'search', *query* must be provided. Passing 'list' as the *mode* will return a list of all items or categories depending on the endpoint used.

Example Call 1: `http://localhost:5050/api/items/json?category_id=9`

Examples Response 1:
```
{
    "Items": [
        {
            "category_id": 9,
            "description": "Canned food perfect for a nuclear winter. Also great for keeping pythons happy.",
            "id": 27,
            "name": "Spam & Eggs",
            "price": "$5",
            "stock": 8
        },
        {
            "category_id": 9,
            "description": "Poured into a goblet, the beer offers some amazing head retention and rings of white lace sticking to the glass after each sip. Good clarity, with a dull golden color.",
            "id": 28,
            "name": "Bayern Bier",
            "price": "$7",
            "stock": 48
        }
    ]
}
```
Example Call 2: `http://localhost:5050/api/items/json?mode=search&query=tea`

Example Response 2:
```
{
    "QueryItems": [
        {
            "category_id": 2,
            "description": "An oversized teaspoon perfect for those who hate small teaspoons.",
            "id": 4,
            "name": "Large Teaspoon",
            "price": "$4",
            "stock": 30
        },
        {
            "category_id": 2,
            "description": "For lovers of large meat slabs.",
            "id": 6,
            "name": "Steak Knife",
            "price": "$25",
            "stock": 9
        },
        {
            "category_id": 2,
            "description": "Previously owned by a very angry prince.",
            "id": 7,
            "name": "Chipped Teapot Set",
            "price": "$5",
            "stock": 1
        }
    ]
}
```
