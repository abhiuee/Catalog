from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from datetime import datetime
from flask import session as login_session
import random, string
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, User, CatalogItem
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from logic import Converter, Node

app = Flask(__name__)

#Import client id information for Google Oauth2 json
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "catalogapp"

#Connect to Database and create database session
engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
	'''Login function that renders login.html with a once generated random key'''
  	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                  for x in xrange(32))
  	login_session['state'] = state
  	return render_template('login.html', STATE=state)

@app.route('/disconnect')
def disconnect():
	'''Function to logout of the site'''
  	if 'credentials' not in login_session.keys():
  		#Check if login_session is active
	    response = make_response(json.dumps('Current user not connected.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response

	#Check if the access token is present or not
  	access_token = login_session['credentials']
  	if access_token is None:
	    response = make_response(json.dumps('Current user not connected.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response

  	#Logout by revoking the login token
  	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['credentials']
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
  	if result['status'] == '200':
	    del login_session['credentials'] 
	    del login_session['gplus_id']
	    name = login_session['username']
	    del login_session['username']
	    del login_session['email']
	    del login_session['picture']
	    flash("User %s logged out" %name)
	    return redirect(url_for('homePage'))
	else:
	    response = make_response(json.dumps('Failed to revoke token for given user.', 400))
	    response.headers['Content-Type'] = 'application/json'
	    return response

@app.route('/connect', methods = ['POST'])
def connect():
	'''Main function to connect to google oauth2 and validate the login and create connection'''
  	# Validate state token
  	if request.args.get('state') != login_session['state']:
	    response = make_response(json.dumps('Invalid state parameter.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response
  	
  	# Obtain authorization code
  	code = request.data
  	try:
	    # Upgrade the authorization code into a credentials object
	    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
	    oauth_flow.redirect_uri = 'postmessage'
	    credentials = oauth_flow.step2_exchange(code)
  	except FlowExchangeError:
	    response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response
  	
  	# Check that the access token is valid.
  	access_token = credentials.access_token
  	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
         % access_token)
  	h = httplib2.Http()
  	result = json.loads(h.request(url, 'GET')[1])
  	
  	# If there was an error in the access token info, abort.
  	if result.get('error') is not None:
	    response = make_response(json.dumps(result.get('error')), 500)
	    response.headers['Content-Type'] = 'application/json'

	#check if the Google + id is valid
  	gplus_id = credentials.id_token['sub']
  	if result['user_id'] != gplus_id:
	    response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response

  	# Verify that the access token is valid for this app.
  	if result['issued_to'] != CLIENT_ID:
  		response = make_response(json.dumps("Token's client ID doesn't match given client ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

  	stored_credentials = login_session.get('credentials')
  	stored_gplus_id = login_session.get('gplus_id')
  	if stored_credentials is not None and gplus_id == stored_gplus_id:
	    response = make_response(json.dumps('Current user is already connected.'), 200)
	    response.headers['Content-Type'] = 'application/json'
	    return response

  	# Store the access token in the session for later use.
  	login_session['credentials'] = credentials.access_token
  	login_session['gplus_id'] = gplus_id

  	# Get user info
  	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
  	params = {'access_token': credentials.access_token, 'alt': 'json'}
  	answer = requests.get(userinfo_url, params=params)

  	data = answer.json()

  	login_session['username'] = data['name']
  	login_session['picture'] = data['picture']
  	login_session['email'] = data['email']

  	#Create html string to send to login page
  	output = ''
  	output += '<h1>Welcome, '
  	output += login_session['username']
  	output += '!</h1>'
  	output += '<img src="'
  	output += login_session['picture']
  	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
  	flash("User %s logged in" % login_session['username'])
  	
  	#Add user to database
  	user = session.query(User).filter_by(name = login_session['username']).all()
  	if user == []:
	  	user = User(name = login_session['username'], email = login_session['email'])
	  	session.add(user)
	  	session.commit()
  	return output

@app.route('/')
@app.route('/catalog/')
def homePage():
	'''Home page for the app'''
	#verify that someone is logged in common for almost all functions
	logged_out = True
	if 'username' in login_session:
		logged_out = False

	categories = session.query(Category).order_by(asc(Category.name))
	items = session.query(CatalogItem).order_by(desc(CatalogItem.created)).limit(10).all()
	latest_items_category = []
	for item in items:
		category = session.query(Category).filter_by(id = item.category_id).one()
		latest_items_category += [category.name]
	return render_template('catalog.html', logged_out = logged_out, categories = categories, latest_items = items, category_list = latest_items_category)

@app.route('/catalog/<string:category_name>/<string:item_name>/')
def describeItem(category_name, item_name):
	'''Describe the item'''
	logged_out = True
	if 'username' in login_session:
		logged_out = False

	category = session.query(Category).filter_by(name = category_name).one()
	item = session.query(CatalogItem).filter_by(name = item_name, category_id = category.id).one()
	
	#Find whether particular item created by currently logged in user or not.
	display = False
	if item and not logged_out:
		user = session.query(User).filter_by(id = item.created_by, name = login_session['username']).all()
		if user != []:
			display = True

	return render_template('describeitem.html', logged_out = logged_out, item = item, category = category, display = display)

@app.route('/catalog/addcategory/', methods = ['GET', 'POST'])
def addCategory():
	'''Function to add category to the app'''
	if 'username' not in login_session:
		flash("Please login to continue")
		return redirect(url_for('showLogin'))

	user = session.query(User).filter_by(name = login_session['username']).all()
	if user == []:
		flash("Error: User not registered")
		return redirect(url_for('homePage'))

	if request.method == 'POST':
		if request.form['name']:
			newcategory = Category(name = request.form['name'], user = user[0])
			session.add(newcategory)
			session.commit()
			flash("Success: New category %s added" %newcategory.name)
		else:
			flash("Error: Supply a valid name for the category")
		return redirect(url_for('homePage'))
	else:
		categories = session.query(Category).order_by(asc(Category.name))
		return render_template('addnewcategory.html', categories = categories)

@app.route('/catalog/additem/', methods = ['GET', 'POST'])
def addItem():
	'''Function to add item to the app'''
	if 'username' not in login_session:
		flash("Login to continue")
		return redirect(url_for('showLogin'))
	user = session.query(User).filter_by(name = login_session['username']).all()
	if user == []:
		flash("Error: User not registered")
		return redirect(url_for('homePage'))
	if request.method == 'POST':
		if request.form['name']:
			if request.form['category']:
				category = session.query(Category).filter_by(name = request.form['category']).one()
				if category:
					newItem = CatalogItem(name = request.form['name'], description = request.form['description'], category = category, user = user[0])
				else:
					flash ("Error: Supply a valid category")
					return redirect(url_for('homePage'))
			else:
				flash("Error: Select a category")
				return redirect(url_for('homePage'))
			session.add(newItem)
			session.commit()
			flash("Success: New item %s added" %newItem.name)
			return redirect(url_for('homePage'))
		else:
			flash("Error: Supply a valid name for the item")
			return redirect(url_for('homePage'))
	else:
		categories = session.query(Category).order_by(asc(Category.name))
		return render_template('addnewitem.html', categories= categories)

@app.route('/catalog/<string:category_name>/items/')
def printCategory(category_name):
	'''Function to print category information'''
	logged_out = True
	if 'username' in login_session:
		logged_out = False
	category = session.query(Category).filter_by(name = category_name).one()
	categories = session.query(Category).order_by(asc(Category.name))
	if category != []:
		items = session.query(CatalogItem).filter_by(category_id = category.id).all()
		if items != []:
			return render_template('describecategory.html', logged_out = logged_out, categories = categories, category_name = category_name, items = items, count = len(items))
		else:
			return render_template('describecategory.html', logged_out = logged_out, categories = categories, category_name = category_name, items = None, count = 0)
	else:
		render_template('describecategory.html', logged_out = logged_out, categories = categories, category_name = None, items = None, count = 0)

@app.route('/catalog/<string:category_name>/<string:item_name>/delete/', methods = ['GET', 'POST'])
def deleteItem(category_name, item_name):
	'''Function to delete item from app'''
	if 'username' not in login_session:
		flash("Login to continue")
		return redirect(url_for('showLogin'))
	user = session.query(User).filter_by(name = login_session['username']).all()
	if user == []:
		flash("Error: User not registered")
		return redirect(url_for('homePage'))
	category = session.query(Category).filter_by(name = category_name).one()
	itemtodelete = session.query(CatalogItem).filter_by(name = item_name, category_id = category.id, created_by = user[0].id).all()
	if itemtodelete == []:
		flash("Item can only be deleted by the user that created it")
		return redirect(url_for('homePage'))
	if request.method == 'POST':
		if itemtodelete != []:
			session.delete(itemtodelete[0])
			session.commit()
			flash("Success: Item %s deleted" %itemtodelete[0].name)			
		return redirect(url_for('homePage'))
	else:
		return render_template('deleteitem.html', category = category, item = itemtodelete[0])
	

@app.route('/catalog/<string:category_name>/<string:item_name>/edit/', methods = ['GET', 'POST'])
def editItem(category_name, item_name):
	'''Function to edit item in the app'''
	if 'username' not in login_session:
		flash("Login to continue")
		return redirect(url_for('showLogin'))
	user = session.query(User).filter_by(name = login_session['username']).all()
	if user == []:
		flash("Error: User not registered")
		return redirect(url_for('homePage'))
	category = session.query(Category).filter_by(name = category_name).one()
	itemtoedit = session.query(CatalogItem).filter_by(name = item_name, category_id = category.id, created_by = user[0].id).all()
	categories = session.query(Category).order_by(asc(Category.name))
	if itemtoedit == []:
		flash("Item can be edited only by the user that created it")
		return redirect(url_for('homePage'))
	if request.method == 'POST':
		if itemtoedit != []:
			if request.form['name']:
				itemtoedit[0].name = request.form['name']
			if request.form['description']:
				itemtoedit[0].description = request.form['description']
			if request.form['category']:
				category = session.query(Category).filter_by(name = request.form["category"]).one()
				if category:
					itemtoedit[0].category_id = category.id
			session.add(itemtoedit[0])
			session.commit()
			flash("Success: Item %s edited" %itemtoedit[0].name)
		return redirect(url_for('homePage'))
	else:
		return render_template('edititem.html', category = category, item = itemtoedit[0], categories = categories)

@app.route('/catalog/xml/')
def dumpCatalogXML():
	'''Function to dump XML'''
	categories = session.query(Category).order_by(asc(Category.name))
	serialized_list = []
	catalog = {}
	for category in categories:
		items = session.query(CatalogItem).filter_by(category_id = category.id).all()
		cat_dict = category.serialize
		if items:
			cat_dict['items'] = [item.serialize for item in items]
		serialized_list += [cat_dict]
	catalog['category'] = serialized_list
	xml_str =  Converter(wrap="catalog", indent = "    ").build(catalog)
	response = make_response(xml_str) 
	response.headers['Content-Type'] = 'text/xml; charset=utf-8'            
	return response

@app.route('/catalog/json/')
def dumpCatalogJSON():
	'''Function to dump JSON'''
	categories = session.query(Category).order_by(asc(Category.name))
	serialized_list = []
	for category in categories:
		items = session.query(CatalogItem).filter_by(category_id = category.id).all()
		cat_dict = category.serialize
		if items:
			cat_dict['items'] = [item.serialize for item in items]
		serialized_list += [cat_dict]
	return jsonify(catalog = serialized_list)

if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)
