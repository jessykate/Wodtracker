#!/usr/bin/python

# A template for a Tornado project using forms and MongoDB as the
# backend: takes a form submission and stores it as a record in a
# Mongo DB. Don't forget to start Mongo first with the "mongod"
# command.
#
# To run:
# ./main.py
# and visit localhost:8888

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.escape
import urllib, urllib2
import os, datetime
try:
    import json
except:
    import simplejson as json
import pymongo

# settings
DATABASE_NAME = 'wodtracker'
# eg: "Monday, December 25 2009 13:30:00 EST"
DATETIME_FORMAT_STRING = "%A, %B %d %Y %H:%M:%S EST"


class NewWODHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/index.html')

class WODSubmitHandler(tornado.web.RequestHandler):
    def get(self):
        # arguments is a dict of key:value pairs where each value is a
        # list (even if there is only one item). 
        name = self.get_argument("name", None)
        wod = self.get_argument("wod", None)
        date = self.get_argument("date", datetime.datetime.now())
        tags = self.get_argument("tags", None)
        equipment_required = bool(self.get_argument("equipment", True))

        if not wod and name:
            print 'missing fields'
            return

        # the date object is automagically converted to the proper
        # bson datetime format, so we can still do things like sort by
        # time.
	# XXX need to ensure slug is unique
        new_record = {'date': date, 'name': name, 'wod': wod, 'tags': tags, 
                      'equipment_required': equipment_required}

        try:
            record_id = wod_save(new_record)
        except BaseException, e:
            message = "There was a problem with your form submission:<br>%s" % e
            self.render('templates/thanks.html', message=message)
            return

	# define a slug for this WOD as either the WOD name or its unique ID in
	# the database. 
	slug = (name and tornado.escape.url_escape(name)) or str(record_id)
	#print slug
	#print type(slug)
	db = pymongo.Connection()[DATABASE_NAME]
	table = db.wods
	table.update({'_id': record_id}, {"$set": {'slug': slug}})

        # go to this workout's page.  
        print 'slug = %s' % slug 
        self.redirect("/wod/%s" % slug)

class UserPageHandler(tornado.web.RequestHandler):
    def get(self, username):
        workouts = get_workouts_by_user(username)
        self.render("templates/user.html", workouts=workouts, user=username)

class WODDisplayHandler(tornado.web.RequestHandler):
    def get(self, slug):
	wodinfo = wod_retrieve('slug', slug)
	# XXX should do some error handling here if wod DNE etc. 
	self.render("templates/wod.html", wodinfo = wodinfo)

class WODScoreHandler(tornado.web.RequestHandler):
    def get(self, slug):
	wodinfo = wod_retrieve('slug', slug)
	self.render("templates/score.html", wodinfo=wodinfo)

class WODScoreSubmitHandler(tornado.web.RequestHandler):
    def post(self):
	pass

def wod_retrieve(k,v):
    ''' retrive a single WOD record based on the key 'k' and value 'v' '''
    db = pymongo.Connection()[DATABASE_NAME]
    table = db.wods
    return table.find_one({k : v}) 	

def wod_save(record):
    db = pymongo.Connection()[DATABASE_NAME]
    table = db.wods
    record_id = table.insert(record, safe=True)
    db.connection.disconnect()
    return record_id

def get_name_from_id(record_id):
    db = pymongo.Connection()[DATABASE_NAME]
    table = db.wods
    record = table.find_one(record_id)
    return record['name']

def get_workouts_by_user(name):
    db = pymongo.Connection()[DATABASE_NAME]
    table = db.wods
    records = table.find({'name':name}).sort('date')
    # records is just a cursor; need to iterate over it to get the
    # actual record objects.
    return [record for record in records]

def frequency_graph(workouts):
    pass

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}

application = tornado.web.Application([
        (r'/new', NewWODHandler),
        (r'/wod_submit', WODSubmitHandler),
	(r'/wod/(\w+)/score', WODScoreHandler),
	(r'/wod/(\w+)', WODDisplayHandler),
        (r'/(\w*)', UserPageHandler),
        ], **settings)

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8123)
    tornado.ioloop.IOLoop.instance().start()
