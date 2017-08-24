#!/usr/bin/env python3

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Category(Base):
    """ Table storing item category information """
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    items = relationship(Item)

    @property
    def serialize(self):
        """ Returns a dict that can easily be converted to JSON representation """
        return {
            "id": self.id,
            "name": self.name
        }


class Item(Base):
    """ Table storing item information """
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category_id = Column(ForeignKey, categories.id)

    @property
    def serialize(self):
        """ Returns a dict that can easily be converted to JSON representation """
        return {
            "id": self.id,
            "name": self.name,
            "category_id": self.category_id
        }





###################################################

engine = create_engine("sqlite:///item_catalog.db")
Base.metadata.create_all(engine)
