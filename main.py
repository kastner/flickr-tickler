#!/usr/bin/env python

import wsgiref.handlers
import re
import urllib

import sys
sys.path.append("myflickr")

from google.appengine.api import users
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from myflickr import MyFlickr


template.register_template_library('templatetags.flickrtags')


class User(db.Model):
    user = db.UserProperty()
    token = db.StringProperty()


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
        self.flickr = MyFlickr("bf1a023e68d6ce32412b9988a3c5cdcb", "a9953877adb04b9f")
        
    def parse(self):
        page = 1
        item = self.request.url.split("/")[-1]
        if re.search("\?page=", item):
            item, page = item.split("?page=")
            page = int(page)
        return (item, page)
    
    def fetch(self, method, **kwargs):
        the_user = users.get_current_user()
        if the_user:
            user = User.get_by_key_name("foo_" + the_user.email())
        args = {'per_page': self.per_page, 'extras': "owner_name,o_dims,media"}
        args.update(kwargs)
        if the_user:
            args.update({"auth_token": user.token})
            photos = self.flickr.signed_call(method, **args)
        else:
            photos = self.flickr.call(method, **args)
        for photo in photos["photos"]["photo"]:
            sizes = self.flickr.call("flickr.photos.getSizes",
                                    photo_id=photo["id"])
            for size in sizes["sizes"]["size"]:
                photo[size["label"].replace(' ', '_')] = size
        return photos["photos"]["photo"]
    
    
    def photo_render(self, **kwargs):
        photos_block = template.render("photos.html", kwargs)
        if (str(self.request.accept).startswith("text/javascript")):
            self.response.out.write(photos_block)
        else:
            kwargs.update({"photos_block": photos_block})
            self.render("photo_page.html", **kwargs)


class FrobHandler(PhotoHandler):
    def get(self):
        frob = self.request.get("frob")
        token = self.flickr.get_token(frob)
        if token and users.get_current_user():
            the_user = users.get_current_user()
            user = User(key_name = "foo_" + the_user.email())
            user.user = the_user
            user.token = token
            user.put()
            self.redirect('/')


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
            photos = self.fetch("flickr.groups.pools.getPhotos",
                                group_id=group_object["id"], page=page)
            self.photo_render(photos=photos, offset=(page - 1) * self.per_page)
        
        
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
            photos = self.fetch("flickr.people.getPublicPhotos", 
                                user_id=user_object["id"], page=page)
            self.photo_render(photos=photos, offset=(page - 1) * self.per_page)


class TagsHandler(PhotoHandler):
    def get(self):
        tags, page = self.parse()
        if tags:
            photos = self.fetch("flickr.photos.search", 
                                sort="interestingness-desc", text=tags, page=page)
            # self.response.out.write(photos["photos"]["photo"][0])
            self.photo_render(photos=photos, offset=(page - 1) * self.per_page)


class AuthHandler(PhotoHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.response.out.write("Link: <a href='%s'>Authorize</a>" % self.flickr.login_link())
        else:
            self.redirect(users.create_login_url(self.request.uri))


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/tickle', TickleHandler),
                                          ('/user/.*', UserHandler),
                                          ('/tag/.*', TagsHandler),
                                          ('/group/.*', GroupHandler),
                                          ('/frob', FrobHandler),
                                          ('/authorize', AuthHandler)],
                                       debug=True)
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
