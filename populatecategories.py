from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Category, Base, CatalogItem
 
engine = create_engine('sqlite:///catalogapp.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


category1 = Category(name = "Soccer")

session.add(category1)
session.commit()


item1 = CatalogItem(name = "Jersey", description = "Nike Jersey for your favorite team. Choose from different leagues", category = category1)

session.add(item1)
session.commit()

item2 = CatalogItem(name = "Chin Guards", description = "Protection from chin injuries while playing", category = category1)
session.add(item2)
session.commit()

item3 = CatalogItem(name = "Cleats", description = "Ideal shoes for traction on the field", category = category1)
session.add(item3)
session.commit()

category2 = Category(name = "Cricket")

session.add(category2)
session.commit()

item4 = CatalogItem(name = "Bat", description = "Made from english willow for awesome stroke play", category = category2)
session.add(item4)
session.commit()

item5 = CatalogItem(name = "Ball", description = "Leather ball with durable stitching", category = category2)
session.add(item5)
session.commit()

item6 = CatalogItem(name = "Wickets", description = "Wickets with in build mic functionality", category = category2)
session.add(item6)
session.commit()

category3 = Category(name = "Badminton")

session.add(category3)
session.commit()

item7 = CatalogItem(name = "Racquet", description = "Yonex racquet with titanium handle", category = category3)
session.add(item7)
session.commit()
print "added items"