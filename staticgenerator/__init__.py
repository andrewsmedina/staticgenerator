#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""Static file generator for Django."""
from django.utils.functional import Promise
from django.db.models.base import ModelBase
from django.db.models.manager import Manager
from django.db.models import Model
from django.db.models.query import QuerySet
from django.conf import settings
from django.test.client import RequestFactory
from handlers import DummyHandler

import stat
import os
import tempfile


class StaticGeneratorException(Exception):
    pass


class StaticGenerator(object):
    """
    The StaticGenerator class is created for Django applications, like a blog,
    that are not updated per request.

    Usage is simple::

        from staticgenerator import quick_publish
        quick_publish('/', Post.objects.live(), FlatPage)

    The class accepts a list of 'resources' which can be any of the
    following: URL path (string), Model (class or instance), Manager, or
    QuerySet.

    As of v1.1, StaticGenerator includes file and path deletion::

        from staticgenerator import quick_delete
        quick_delete('/page-to-delete/')

    The most effective usage is to associate a StaticGenerator with a model's
    post_save and post_delete signal.

    The reason for having all the optional parameters is to reduce coupling
    with django in order for more effectively unit testing.
    """

    def __init__(self, *resources, **kw):
        self.parse_dependencies(kw)

        self.resources = self.extract_resources(resources)
        self.server_name = self.get_server_name(kw)
        self.web_root = self.get_web_root(kw)

    def parse_dependencies(self, kw):
        site = kw.get('site', None)
        self.site = site

    def get_web_root(self, kw):
        try:
            return getattr(settings, 'WEB_ROOT')
        except AttributeError:
            web_root = kw['settings'].WEB_ROOT if kw.has_key('settings') and \
                hasattr(kw['settings'], 'WEB_ROOT') else None

            if not web_root:
                raise StaticGeneratorException('You must specify WEB_ROOT in settings.py')

            return web_root

    def extract_resources(self, resources):
        """Takes a list of resources, and gets paths by type"""
        extracted = []

        for resource in resources:

            # A URL string
            if isinstance(resource, (str, unicode, Promise)):
                extracted.append(str(resource))
                continue

            # A model instance; requires get_absolute_url method
            if isinstance(resource, Model):
                extracted.append(resource.get_absolute_url())
                continue

            # If it's a Model, we get the base Manager
            if isinstance(resource, ModelBase):
                resource = resource._default_manager

            # If it's a Manager, we get the QuerySet
            if isinstance(resource, Manager):
                resource = resource.all()

            # Append all paths from obj.get_absolute_url() to list
            if isinstance(resource, QuerySet):
                extracted += [obj.get_absolute_url() for obj in resource]

        return extracted

    def get_server_name(self, kw={}):
        '''Tries to get the server name.
        First we look in the django settings.
        If it's not found we try to get it from the current Site.
        Otherwise, return "localhost".
        '''
        try:
            return getattr(settings, 'SERVER_NAME')
        except:
            pass

        try:
            if not self.site:
                from django.contrib.sites.models import Site
                self.site = Site
            return self.site.objects.get_current().domain
        except:
            server_name = kw['settings'].SERVER_NAME if kw.has_key('settings') and \
                hasattr(kw['settings'], 'SERVER_NAME') else None

            if not server_name:
                print '*** Warning ***: Using "localhost" for domain name. Use django.contrib.sites or set settings.SERVER_NAME to disable this warning.'
                return 'localhost'

            return server_name

    def get_content_from_path(self, path):
        """
        Imitates a basic http request using DummyHandler to retrieve
        resulting output (HTML, XML, whatever)
        """
        request = RequestFactory().get(path)
        request.path_info = path
        request.META.setdefault('SERVER_PORT', 80)
        request.META.setdefault('SERVER_NAME', self.server_name)

        handler = DummyHandler()
        try:
            response = handler(request)
        except Exception, err:
            raise StaticGeneratorException("The requested page(\"%s\") raised an exception. Static Generation failed. Error: %s" % (path, str(err)))

        if int(response.status_code) != 200:
            raise StaticGeneratorException("The requested page(\"%s\") returned http code %d. Static Generation failed." % (path, int(response.status_code)))

        return response.content

    def get_filename_from_path(self, path):
        """
        Returns (filename, directory)
        Creates index.html for path if necessary
        """
        if path.endswith('/'):
            path = '%sindex.html' % path

        filename = os.path.join(self.web_root, path.lstrip('/')).encode('utf-8')
        return filename, os.path.dirname(filename)

    def publish_from_path(self, path, content=None):
        """
        Gets filename and content for a path, attempts to create directory if
        necessary, writes to file.
        """
        filename, directory = self.get_filename_from_path(path)
        if not content:
            content = self.get_content_from_path(path)

        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except:
                raise StaticGeneratorException('Could not create the directory: %s' % directory)

        try:
            f, tmpname = tempfile.mkstemp(dir=directory)
            os.write(f, content)
            os.close(f)
            os.chmod(tmpname, stat.S_IREAD | stat.S_IWRITE | stat.S_IWUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            os.rename(tmpname, filename)
        except:
            raise StaticGeneratorException('Could not create the file: %s' % filename)

    def delete_from_path(self, path):
        """Deletes file, attempts to delete directory"""
        filename, directory = self.get_filename_from_path(path)
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except:
            raise StaticGeneratorException('Could not delete file: %s' % filename)

        try:
            os.rmdir(directory)
        except OSError:
            # Will fail if a directory is not empty, in which case we don't
            # want to delete it anyway
            pass

    def do_all(self, func):
        return [func(path) for path in self.resources]

    def delete(self):
        return self.do_all(self.delete_from_path)

    def publish(self):
        return self.do_all(self.publish_from_path)


def quick_publish(*resources):
    return StaticGenerator(*resources).publish()


def quick_delete(*resources):
    return StaticGenerator(*resources).delete()
