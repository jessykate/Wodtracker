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


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('templates/index.html')

class FormHandler(tornado.web.RequestHandler):
    def get(self):
        # arguments is a dict of key:value pairs where each value is a
        # list (even if there is only one item). 
        name = self.get_argument("name", None)
        wod = self.get_argument("wod", None)
        score = self.get_argument("score", None)
        comments = self.get_argument("comments", None)
        equipment_required = bool(self.get_argument("equipment", True))
        date = datetime.datetime.now()

        if not wod or not name or not score:
            print 'missing fields'
            return

        # the date object is automagically converted to the proper
        # bson datetime format, so we can still do things like sort by
        # time.
        new_record = {'date': date, 'name': name, 'wod': wod, 'score': score, 
                      'comments': comments, 'equipment_required': equipment_required}

        try:
            record_id = wod_save(new_record)
        except BaseException, e:
            message = "There was a problem with your form submission:<br>%s" % e
            self.render('templates/thanks.html', message=message)
            return

        # get all the workouts for the person with this name
        username = get_name_from_id(record_id)
        print 'retrieving user info:'
        print 'name = %s' % username 
        self.redirect("/%s" % username)

class UserPageHandler(tornado.web.RequestHandler):
    def get(self, username):
        workouts = get_workouts_by_user(username)
        self.render("templates/user.html", workouts=workouts, user=username)

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
        (r'/', MainHandler),
        (r'/submit', FormHandler),
        (r'/(\w*)', UserPageHandler),
        ], **settings)

if __name__ == '__main__':
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
