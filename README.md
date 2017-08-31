# ACME Trading Item Catalog
A quirky Full-Stack CRUD application using both OAuth2 authentication (via Google) and server-side management of credentials. It uses Python 3 (Flask microframework), SQLAlchemy, D3.js and Bootstrap, also providing a RESTful API.

# Running the app
## Requirements
You will need to ensure that Python 3 is available on your system and that the required dependencies are installed for the backend to function. Refer to the module imports in `views.py` and `models.py` for details. Consider using a [Virtual Environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/) if you do not wish to taint your existing Python environment.

## Initialization
Before first run, it is best to initialize the database with some starter data. This is performed by running the following commands from the app's root directory:

  1. `python models.py`
  2. `python populate_db.py`

## Starting the back-end server
The application can then be launched by running `python views.py` which will start the HTTP server. The user interface can then be accessed by navigating your browser to `http://localhost:5050`.

# Using the API
## Endpoints
The app provides two API endpoints for querying information about categories and items, and additional restricted endpoints to perform create, update and delete operations on the catalog database. All API calls return [JSON](http://www.json.org/).

Required parameters are shown in **bold**.

API Endpoint | Method | Parameters | Accepted vals
-- | -- | -- | --
localhost:5050/api/items/json | GET | id | An integer category ID
|| | name | A string representing the category name
|| | mode | `list` or `search`
|| | query | A string representing a search query
||
localhost:5050/api/categories/json | GET | id | An integer item ID
|| | name | A string representing the item name
|| | mode | `list` or `search`
|| | query | A string representing a search query
||
localhost:5050/api/add/item | POST | **token** | A string representing a valid access token
|| | **name** | A string representing the name of the new item
|| | category_id | An integer representing the ID of the category into which the item will be added
|| | price | A string representing the cost of the item
|| | stock | An integer representing the initial stock level of the item
|| | description | A string comprising the item's description
||
localhost:5050/api/add/category | POST | **token** | A string representing a valid access token
|| | **name** | A string representing the name of the new category
||
localhost:5050/api/update/item | PUT | **token** | A string representing a valid access token
|| | **id** | An integer item ID
|| | name | A string representing the item's updated name
|| | price | A string representing the item's updated price ($)
|| | stock | An integer representing the item's updated stock level
|| | description | A string representing the item's updated description
||
localhost:5050/api/update/category | PUT | **token** | A string representing a valid access token
|| | **id** | An integer category ID
|| | name | A string representing the category's updated name
||
localhost:5050/api/delete/item | DELETE | **token** | A string representing a valid access token
|| | **id** | An integer ID representing the item to be deleted
||
localhost:5050/api/delete/category | DELETE | **token** | A string representing a valid access token
|| | **id** | An integer ID representing the category to be deleted

### Notes
- For `GET` routes, if `mode=search`, *query* must be provided. If `mode=list`, request will return a list of all items or categories depending on the endpoint used.
- For `GET` routes, `id` and `name` are mutually exclusive parameters.
 - Item/Category images cannot be added or updated via the API. For this functionality, users must log in via the website UI.

## User registration and access tokens
API requests that alter data can only be performed by users with registered accounts and using a valid access token. An new account can be created via a request to `localhost:5050/api/registration` and passing a valid email address as the `username`, along with a `password`:

```
POST http://localhost:5050/api/registration?username=bilbobaggins@hobbits.com&password=FrodoBaggins
```

Registered users can then request access tokens by authenticating with credentials. Access tokens are valid for 15 minutes.

```
POST http://localhost:5050/api/tokens?username=bilbobaggins@hobbits.com&password=FrodoBaggins
```

## Examples

Example Call 1:

`http://localhost:5050/api/items/json?category_id=9`

Example Response 1:

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
Example Call 2:

`http://localhost:5050/api/items/json?mode=search&query=tea`

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
Example Call 3:
`http://localhost:5050/api/add/category?token=ACCESS_TOKEN&name=Jewelry`

Example Response 3:
```
{
    "message": "Successfully added category 'Jewelry' to database.",
    "status": 200
}
```

# Note
This project has been prepared in fulfillment of the Udacity FSND Item Catalog project requirements.
