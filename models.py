#!/usr/bin/env python3

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Category(Base):
    """ Table storing item category information """
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    image = Column(String)

    @property
    def serialize(self):
        """ Returns a dict of object data easily convertible to JSON  """
        return {
            "id": self.id,
            "name": self.name
        }

class Item(Base):
    """ Table storing item information """
    __tablename__ = "item"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(String, nullable=False)
    stock = Column(Integer, nullable=False)
    image = Column(String)
    category = relationship(Category)
    category_id = Column(ForeignKey("category.id"))

    @property
    def serialize(self):
        """ Returns a dict of object data easily convertible to JSON  """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stock": self.stock,
            "category_id": self.category_id
        }





###################################################

engine = create_engine("sqlite:///item_catalog.db")
Base.metadata.create_all(engine)
