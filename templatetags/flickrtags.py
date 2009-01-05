#!/usr/bin/env python


from google.appengine.ext.webapp import template


# Get the template Library
register = template.create_template_register()


@register.inclusion_tag('media.html')


def flickr_media(photo):
    print photo
    is_photo = (photo["media"] == "photo")
    return {'is_photo': is_photo, 'photo': photo}