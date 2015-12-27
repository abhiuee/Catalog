Introduction:

The app allows you to login using G+ id and then edit, add or update items and add categories accordingly

Configuration:

Application configured to run on localhost:8000. Requires packages namely flask, sqlalchemy, oath2client, httplib2, json, requests, dict2xml (Please see note at the end of the README). Google client credentials need to be created if the app needs to be developed by a developer.

Installation Instructions:

Install the dict2xml package
Run python database_setup.py to start the database
To run the application just type python application.py 

Note: I have copied logic.py from dict2xml package because I didn't have permissions to setup the package and therefore used the package code directly from the application.py

Operating Instructions:

App displays the Categories and 10 Latest items added on the home page. If the user is logged in, links to add new category and new item are also provided. If user clicks on a category, information about the items available in that category is provided. If the user clicks on an item, item's description is provided alongwith edit and delete buttons if the user is the one who created the item.

APIs:

The app also provides public access to JSON (/catalog/json/) and XML (/catalog/xml/) Please see the links described above to test these APIs and start working on your own app.


