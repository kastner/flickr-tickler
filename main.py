#!/usr/bin/env python

import wsgiref.handlers
import re
import urllib

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
        user = self.request.get("user")
        group = self.request.get("group")
        tags = self.request.get("tags")
        if re.search("flickr.com", user) or re.search("flickr.com", group):
            url = user + group
            if re.search("in/pool-", url):
                group = re.search("in/pool-(.*)/", url).group(1)
            elif re.search("/groups/", url):
                group = re.search("/groups/([^/]*)/", url).group(1)
            elif re.search("/photos/", url):
                user = re.search("/photos/([^/]*)", url).group(1)
        if tags:
            self.redirect("/tag/%s" % urllib.quote(tags))
        if user:
            self.redirect("/user/%s" % user)
        elif group:
            self.redirect("/group/%s" % group)
        

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
                                        extras="owner_name",
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
                                        extras="owner_name",
                                        user_id=user_object["id"],
                                        page=page,
                                        per_page=self.per_page)
            self.photo_render(photos=photos["photos"]["photo"], offset=(page - 1) * self.per_page)


class TagsHandler(PhotoHandler):
    def get(self):
        tags, page = self.parse()
        if tags:
            # memcache here later
            photos = self.flickr.call("flickr.photos.search", 
                                        extras="owner_name",
                                        sort="interestingness-desc",
                                        text=tags,
                                        page=page,
                                        per_page=self.per_page)
            # self.response.out.write(photos["photos"]["photo"][0])
            self.photo_render(photos=photos["photos"]["photo"], offset=(page - 1) * self.per_page)

        
def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/tickle', TickleHandler),
                                          ('/user/.*', UserHandler),
                                          ('/tag/.*', TagsHandler),
                                          ('/group/.*', GroupHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
