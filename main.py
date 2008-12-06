#!/usr/bin/env python

import wsgiref.handlers
import re


import sys
sys.path.append("myflickr")


from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from myflickr import MyFlickr


class RequestHandler(webapp.RequestHandler):
    def render(self, template_name, **kwargs):
        self.response.out.write(template.render(template_name, kwargs))


class MainHandler(RequestHandler):
    def get(self):
        self.render("index.html")


class TickleHandler(RequestHandler):
    def get(self):
        group, user, tags = "", "", ""
        url = self.request.get("url")
        if not re.search("flickr.com", url):
            tags = url
        elif re.search("in/pool-", url):
            group = re.search("in/pool-(.*)/", url).group(1)
            # url = "http://flickr.com/groups/%s" % group
        elif re.search("/groups/", url):
            group = re.search("/groups/([^/]*)/", url).group(1)
        elif re.search("/photos/", url):
            user = re.search("/photos/([^/]*)", url).group(1)
        
        
        if group:
            self.redirect("/group/%s" % group)
            # group = f.call("flickr.urls.lookupGroup", url = url)
            # self.render("tickle.html", group = group)
        elif user:
            self.redirect("/user/%s" % user)
            # user = f.call("flickr.urls.lookupUser", url = url)
            # self.render("tickle.html", group=user)
        

class PhotoHandler(RequestHandler):
    per_page = 15
    
    def __init__(self):
        self.flickr = MyFlickr("bf1a023e68d6ce32412b9988a3c5cdcb")
        
    def parse(self):
        page = 1
        item = self.request.url.split("/")[-1]
        if re.search("\?page=", item):
            item, page = item.split("?page=")
            page = int(page)
        return (item, page)
        
    def photo_render(self, **kwargs):
        photos_block = template.render("photos.html", kwargs)
        if (str(self.request.accept).startswith("text/javascript")):
            self.response.out.write(photos_block)
        else:
            kwargs.update({"photos_block": photos_block})
            self.render("photo_page.html", **kwargs)
        
        
class GroupHandler(PhotoHandler):
    def get(self):
        group, page = self.parse()
        if group:
            # memcache here later
            url = "http://flickr.com/groups/%s" % group
            api_group = self.flickr.call("flickr.urls.lookupGroup", url=url)
            if not api_group:
                return
            group_object = api_group["group"]
            photos = self.flickr.call("flickr.groups.pools.getPhotos", 
                                        group_id=group_object["id"],
                                        page=page,
                                        per_page=self.per_page)
            self.photo_render(photos=photos["photos"]["photo"], offset=(page - 1) * self.per_page)
        
        
class UserHandler(PhotoHandler):
    def get(self):
        user, page = self.parse()
        if user:
            # memcache here later
            url = "http://flickr.com/photos/%s" % user
            api_user = self.flickr.call("flickr.urls.lookupUser", url=url)
            if not api_user:
                return
            user_object = api_user["user"]
            photos = self.flickr.call("flickr.people.getPublicPhotos", 
                                        user_id=user_object["id"],
                                        page=page,
                                        per_page=self.per_page)
            self.photo_render(photos=photos["photos"]["photo"], offset=(page - 1) * self.per_page)
        
def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/tickle', TickleHandler),
                                          ('/user/.*', UserHandler),
                                          ('/group/.*', GroupHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
