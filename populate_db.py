#!/usr/bin/env python3

#### This file populates the item catalog with some sample data ####

from models import Base, Item, Category

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///item_catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind = engine)
session = DBSession()

categories = ["Electronics", "Kitchenware", "Hardware",
              "Appliances", "Apparel", "Musical Instruments",
              "Furniture", "Medical Consumables", "Food"]



electronics_items = [
    {
        "name": "Used Circuit Board",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$2",
        "category": "Electronics"
    },
    {
        "name": "Stripped 44 AWG Wire",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$50",
        "category": "Electronics"
    },
    {
        "name": "CRT Monitor",
        "description": "Great value for gamers looking for zero-latency performance.",
        "price": "$10",
        "category": "Electronics"
    }
]

kitchenware_items = [
    {
        "name": "Large Teaspoon",
        "description": "An oversized teaspoon perfect for those who hate small teaspoons.",
        "price": "$4",
        "category": "Kitchenware"
    },

    {
        "name": "Bent Fork",
        "description": "Easier to use than a straight fork.",
        "price": "$3",
        "category": "Kitchenware"
    },
    {
        "name": "Steak Knife",
        "description": "For lovers of large meat portions.",
        "price": "$25",
        "category": "Kitchenware"
    },
    {
        "name": "Chipped Teapot",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$5",
        "category": "Kitchenware"
    },
    {
        "name": "Cracked Plate",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$3",
        "category": "Kitchenware"
    },
]

hardware_items = [
    {
        "name": "Rusty Hammer",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$12",
        "category": "Hardware"
    },
    {
        "name": "'Bitten Apple' Screwdriver",
        "description": "Indispensable tool for servicing a popular modern smartphone.",
        "price": "$15",
        "category": "Hardware"
    },
    {
        "name": "Screw (Random gauge)",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$1",
        "category": "Hardware"
    }
]

appliances_items = [
    {
        "name": "Unshielded Microwave",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$70",
        "category": "Appliances"
    },
    {
        "name": "Automatic Dishwasher",
        "description": "Washes the dishes for you. Disclaimer: May scratch your glasses and crockery.",
        "price": "$230",
        "category": "Appliances"
    },
    {
        "name": "Washing Machine",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$600",
        "category": "Appliances"
    },
    {
        "name": "Modded Sandwich Maker",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$20",
        "category": "Appliances"
    },
    {
        "name": "Bio-Gas Oven",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$100",
        "category": "Appliances"
    },
    {
        "name": "4K LCD TV",
        "description": "Useless 'Down Under', no matter what the marketing hype tells you.",
        "price": "$1200",
        "category": "Appliances"
    }
]

apparel_items = [
    {
        "name": "Mithril Vest",
        "description": "Enchanted prop from the LOTR movies.",
        "price": "$8000",
        "category": "Apparel"
    },
    {
        "name": "Hooded Cloak",
        "description": "May help you look like a Jedi.",
        "price": "$180",
        "category": "Apparel"
    },
    {
        "name": "Faded Jeans",
        "description": "Unisex and well used. The label says <read-error>evi's.",
        "price": "$30",
        "category": "Apparel"
    }
]

musical_instruments_items = [
    {
        "name": "Enchanted Flute",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$740",
        "category": "Musical Instruments"
    },
    {
        "name": "'Blackie' Electric Guitar",
        "description": "Eric Clapton's very own.",
        "price": "$5000",
        "category": "Musical Instruments"
    }
]

furniture_items = [
    {
        "name": "Infested Couch",
        "description": "May contain bedbugs and other nasties.",
        "price": "$320",
        "category": "Furniture"
    },
    {
        "name": "Stained Antique Armchair",
        "description": "A Victorian-era armchair.",
        "price": "$250",
        "category": "Furniture"
    }
]

medical_consumables_items = [
    {
        "name": "Sticky-Aid Kit",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$8",
        "category": "Medical Consumables"
    },
    {
        "name": "Mentats",
        "description": "Will add complementary rust marks to every object it comes into contact with.",
        "price": "$11",
        "category": "Medical Consumables"
    }
]

food_items = [
    {
        "name": "Spam & Eggs",
        "description": "Canned food perfect for a nuclear winter. Also great for keeping pythons happy.",
        "price": "$5",
        "category": "Food"
    },
    {
        "name": "Bayern Bier",
        "description": "Poured into a goblet, the beer offers some amazing head retention and rings of white lace sticking to the glass after each sip. Good clarity, with a dull golden color.",
        "price": "$7",
        "category": "Food"
    }
]

electronics = categories[0]
category = Category(name=electronics)
session.add(category)
session.commit()
for i in electronics_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()

kitchenware = categories[1]
category = Category(name=kitchenware)
session.add(category)
session.commit()
for i in kitchenware_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()

hardware = categories[2]
category = Category(name=hardware)
session.add(category)
session.commit()
for i in hardware_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()

appliances = categories[3]
category = Category(name=appliances)
session.add(category)
session.commit()
for i in appliances_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()

apparel = categories[4]
category = Category(name=apparel)
session.add(category)
session.commit()
for i in apparel_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()

musical_instruments = categories[5]
category = Category(name=musical_instruments)
session.add(category)
session.commit()
for i in musical_instruments_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()

furniuture = categories[6]
category = Category(name=furniuture)
session.add(category)
session.commit()
for i in furniture_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()

medical_consumables = categories[7]
category = Category(name=medical_consumables)
session.add(category)
session.commit()
for i in electronics_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()

food = categories[8]
category = Category(name=food)
session.add(category)
session.commit()
for i in food_items:
    item_name = i["name"]
    item_description = i["description"]
    item_price = i["price"]
    item_category = i["category"]
    item = Item(name=item_name, description=item_description, price=item_price, category=category)
    session.add(item)
    session.commit()
