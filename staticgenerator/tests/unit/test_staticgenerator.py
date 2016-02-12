#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import tempfile

from contextlib import contextmanager
from unittest import skip

from django.db.models import Model

from staticgenerator.staticgenerator import StaticGenerator, StaticGeneratorException, DummyHandler
import staticgenerator.staticgenerator

from mox import Mox


class CustomSettings(object):

    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)


@contextmanager
def remove_web_root_from_settings():
    from django.conf import settings

    old_web_root = settings.WEB_ROOT
    del settings.WEB_ROOT

    try:
        yield
    except:
        raise
    finally:
        settings.WEB_ROOT = old_web_root


def get_mocks(mox):
    http_request_mock = mox.CreateMockAnything()
    model_base_mock = mox.CreateMockAnything()
    manager_mock = mox.CreateMockAnything()
    model_mock = mox.CreateMockAnything()
    queryset_mock = mox.CreateMockAnything()

    return http_request_mock, model_base_mock, manager_mock, model_mock, queryset_mock


def test_can_create_staticgenerator():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)
    settings = CustomSettings(WEB_ROOT="test_web_root")

    mox.ReplayAll()

    instance = StaticGenerator(http_request=http_request,
                               model_base=model_base,
                               manager=manager,
                               model=model,
                               queryset=queryset,
                               settings=settings)

    assert instance
    assert isinstance(instance, StaticGenerator)
    mox.VerifyAll()


def test_not_having_web_root_raises():
    mox = Mox()

    http_request, model_base, manager, model, queryset = get_mocks(mox)

    mox.ReplayAll()

    with remove_web_root_from_settings():
        try:
            StaticGenerator(
                http_request=http_request,
                model_base=model_base,
                manager=manager,
                model=model,
                queryset=queryset
            )
        except StaticGeneratorException, e:
            assert str(e) == 'You must specify WEB_ROOT in settings.py'
            mox.VerifyAll()
            return

        assert False, "Shouldn't have gotten this far."


def test_staticgenerator_keeps_track_of_web_root():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)

    settings = CustomSettings(WEB_ROOT="test_web_root_1294128189")

    mox.ReplayAll()

    with remove_web_root_from_settings():
        instance = StaticGenerator(
            http_request=http_request,
            model_base=model_base,
            manager=manager,
            model=model,
            queryset=queryset,
            settings=settings
        )

        assert instance.web_root == "test_web_root_1294128189"
        mox.VerifyAll()


def test_get_server_name_gets_name_from_settings():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)

    settings = CustomSettings(WEB_ROOT="test_web_root_1294128189",
                              SERVER_NAME="some_random_server")

    mox.ReplayAll()

    instance = StaticGenerator(
        http_request=http_request,
        model_base=model_base,
        manager=manager,
        model=model,
        queryset=queryset,
        settings=settings
    )

    assert instance.server_name == "some_random_server"
    mox.VerifyAll()


def test_get_server_name_gets_name_from_site():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)

    current_site = mox.CreateMockAnything()
    site_mock = mox.CreateMockAnything()
    site_mock.objects = mox.CreateMockAnything()
    site_mock.objects.get_current().AndReturn(current_site)
    current_site.domain = "custom_domain"

    settings = CustomSettings(WEB_ROOT="some_web_root")

    mox.ReplayAll()

    instance = StaticGenerator(http_request=http_request,
                               model_base=model_base,
                               manager=manager,
                               model=model,
                               queryset=queryset,
                               settings=settings,
                               site=site_mock)

    assert instance.server_name == "custom_domain"
    mox.VerifyAll()


def test_get_server_name_as_localhost_by_default():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)

    settings = CustomSettings(WEB_ROOT="some_web_root")

    mox.ReplayAll()

    instance = StaticGenerator(http_request=http_request,
                               model_base=model_base,
                               manager=manager,
                               model=model,
                               queryset=queryset,
                               settings=settings)

    assert instance.server_name == "localhost"
    mox.VerifyAll()


def test_extract_resources_when_resource_is_a_str():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)

    resources_mock = "some_str"

    settings = CustomSettings(WEB_ROOT="some_web_root")

    mox.ReplayAll()

    instance = StaticGenerator(resources_mock,
                               http_request=http_request,
                               model_base=model_base,
                               manager=manager,
                               model=model,
                               queryset=queryset,
                               settings=settings)

    assert len(instance.resources) == 1
    assert instance.resources[0] == "some_str"
    mox.VerifyAll()


def test_extract_resources_when_resource_is_a_model():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)

    class MockModel(Model):

        def get_absolute_url(self):
            return 'some_model_url'

    resources_mock = MockModel()
    model = MockModel

    settings = CustomSettings(WEB_ROOT="some_web_root")

    mox.ReplayAll()

    instance = StaticGenerator(
        resources_mock,
        http_request=http_request,
        model_base=model_base,
        manager=manager,
        model=model,
        queryset=queryset,
        settings=settings
    )

    assert len(instance.resources) == 1
    assert instance.resources[0] == 'some_model_url'
    mox.VerifyAll()


def test_get_content_from_path():
    from django.test.client import RequestFactory

    mox = Mox()
    _, model_base, manager, model, queryset = get_mocks(mox)
    settings = CustomSettings(WEB_ROOT="test_web_root")

    path_mock = 'some_path'

    request_mock = mox.CreateMockAnything()
    request_mock.META = mox.CreateMockAnything()
    request_mock.META.setdefault('SERVER_PORT', 80)
    request_mock.META.setdefault('SERVER_NAME', 'localhost')

    mox.StubOutWithMock(RequestFactory, 'get')
    RequestFactory.get.__call__(path_mock).AndReturn(request_mock)

    response_mock = mox.CreateMockAnything()
    response_mock.content = 'foo'
    response_mock.status_code = 200

    handler_mock = mox.CreateMockAnything()
    handler_mock.__call__().AndReturn(handler_mock)
    handler_mock.__call__(request_mock).AndReturn(response_mock)

    mox.ReplayAll()

    try:
        dummy_handler = staticgenerator.staticgenerator.DummyHandler
        staticgenerator.staticgenerator.DummyHandler = handler_mock

        instance = StaticGenerator(
            model_base=model_base,
            manager=manager,
            model=model,
            queryset=queryset,
            settings=settings
        )

        result = instance.get_content_from_path(path_mock)
    finally:
        staticgenerator.staticgenerator.DummyHandler = dummy_handler

    assert result == 'foo'
    mox.VerifyAll()
    mox.UnsetStubs()


@skip('This seems to be an expected functionality. Its not implemented. Im maintaining this in here so that it will later be added')
def test_get_filename_from_path():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)
    settings = CustomSettings(WEB_ROOT="test_web_root")

    path_mock = '/foo/bar'

    fs_mock = mox.CreateMockAnything()
    fs_mock.join("test_web_root", "foo/bar").AndReturn("test_web_root/foo/bar")
    fs_mock.dirname("test_web_root/foo/bar").AndReturn("test_web_root/foo")

    mox.ReplayAll()

    instance = StaticGenerator(http_request=http_request,
                               model_base=model_base,
                               manager=manager,
                               model=model,
                               queryset=queryset,
                               settings=settings,
                               fs=fs_mock)

    result = instance.get_filename_from_path(path_mock)

    assert result == ('test_web_root/foo/bar', 'test_web_root/foo')
    mox.VerifyAll()


@skip('This seems to be an expected functionality. Its not implemented. Im maintaining this in here so that it will later be added')
def test_get_filename_from_path_when_path_ends_with_slash():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)
    settings = CustomSettings(WEB_ROOT="test_web_root")

    fs_mock = mox.CreateMockAnything()
    fs_mock.join("test_web_root", "foo/bar/index.html").AndReturn("test_web_root/foo/bar/index.html")
    fs_mock.dirname("test_web_root/foo/bar/index.html").AndReturn("test_web_root/foo/bar")

    path_mock = '/foo/bar/'

    mox.ReplayAll()

    instance = StaticGenerator(
        http_request=http_request,
        model_base=model_base,
        manager=manager,
        model=model,
        queryset=queryset,
        settings=settings,
        fs=fs_mock
    )

    result = instance.get_filename_from_path(path_mock)

    assert result == ('test_web_root/foo/bar/index.html', 'test_web_root/foo/bar')
    mox.VerifyAll()


def test_publish_raises_when_unable_to_create_folder():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)
    FAKE_WEB_ROOT = 'test_web_root'

    mox.StubOutWithMock(os, 'makedirs')
    mox.StubOutWithMock(os.path, 'exists')
    os.makedirs(FAKE_WEB_ROOT).AndRaise(ValueError())
    os.path.exists(FAKE_WEB_ROOT).AndReturn(False)

    settings = CustomSettings(WEB_ROOT=FAKE_WEB_ROOT)

    mox.ReplayAll()

    with remove_web_root_from_settings():
        instance = StaticGenerator(
            http_request=http_request,
            model_base=model_base,
            manager=manager,
            model=model,
            queryset=queryset,
            settings=settings,
        )

        try:
            instance.publish_from_path("some_path", content="some_content")
        except StaticGeneratorException, e:
            assert str(e) == 'Could not create the directory: ' + FAKE_WEB_ROOT
            mox.VerifyAll()
            return
        finally:
            mox.UnsetStubs()

        assert False, "Shouldn't have gotten this far."


def test_publish_raises_when_unable_to_create_temp_file():
    mox = Mox()
    _, model_base, manager, model, queryset = get_mocks(mox)

    FAKE_WEB_ROOT = 'test_web_root'

    mox.StubOutWithMock(tempfile, 'mkstemp')
    tempfile.mkstemp(dir="test_web_root").AndRaise(ValueError())

    settings = CustomSettings(WEB_ROOT=FAKE_WEB_ROOT)

    mox.ReplayAll()

    with remove_web_root_from_settings():
        instance = StaticGenerator(
            model_base=model_base,
            manager=manager,
            model=model,
            queryset=queryset,
            settings=settings,
        )

        try:
            instance.publish_from_path("some_path", content="some_content")
        except StaticGeneratorException, e:
            assert str(e) == 'Could not create the file: test_web_root/some_path'
            mox.VerifyAll()
            return
        finally:
            mox.UnsetStubs()

        assert False, "Shouldn't have gotten this far."


def test_publish_from_path():
    FAKE_WEB_ROOT = 'test_web_root'
    FILE_PATH = 'some_path'
    FILE_CONTENT = 'some_content'

    FILE_RELATIVE_PATH = os.path.join(FAKE_WEB_ROOT, FILE_PATH)

    settings = CustomSettings(WEB_ROOT=FAKE_WEB_ROOT)

    with remove_web_root_from_settings():
        instance = StaticGenerator(
            settings=settings
        )
        instance.publish_from_path(FILE_PATH, content=FILE_CONTENT)

    assert os.path.exists(FILE_RELATIVE_PATH), 'File {file_path} not found'.format(file_path=FILE_RELATIVE_PATH)

    with open(FILE_RELATIVE_PATH, 'r') as fd:
        assert fd.readline() == FILE_CONTENT, 'File {file_path} content differs'.format(file_path=FILE_RELATIVE_PATH)


def test_delete_raises_when_unable_to_delete_file():
    mox = Mox()

    FAKE_WEB_ROOT = 'test_web_root'
    FILE_PATH = 'some_path'
    FILE_RELATIVE_PATH = os.path.join(FAKE_WEB_ROOT, FILE_PATH)

    settings = CustomSettings(WEB_ROOT=FAKE_WEB_ROOT)

    mox.StubOutWithMock(os.path, 'exists')
    mox.StubOutWithMock(os, 'remove')

    os.path.exists(FILE_RELATIVE_PATH).AndReturn(True)
    os.remove(FILE_RELATIVE_PATH).AndRaise(Exception())

    mox.ReplayAll()

    with remove_web_root_from_settings():
        instance = StaticGenerator(
            settings=settings,
        )

        try:
            instance.delete_from_path(FILE_PATH)
        except StaticGeneratorException, e:
            assert str(e) == 'Could not delete file: {file_path}'.format(file_path=FILE_RELATIVE_PATH)
            mox.VerifyAll()
            return
        finally:
            mox.UnsetStubs()

    assert False, "Shouldn't have gotten this far."


def test_delete_ignores_folder_delete_when_unable_to_delete_folder():
    mox = Mox()
    http_request, model_base, manager, model, queryset = get_mocks(mox)

    fs_mock = mox.CreateMockAnything()

    fs_mock.join("test_web_root", "some_path").AndReturn("test_web_root/some_path")
    fs_mock.dirname("test_web_root/some_path").AndReturn("test_web_root")
    fs_mock.exists("test_web_root/some_path").AndReturn(True)
    fs_mock.remove("test_web_root/some_path")

    fs_mock.rmdir("test_web_root").AndRaise(OSError())

    settings = CustomSettings(WEB_ROOT="test_web_root")

    mox.ReplayAll()

    instance = StaticGenerator(http_request=http_request,
                               model_base=model_base,
                               manager=manager,
                               model=model,
                               queryset=queryset,
                               settings=settings,
                               fs=fs_mock)

    instance.delete_from_path("some_path")

    assert True, "Should work even when raising OSError"


def test_delete_from_path():
    FAKE_WEB_ROOT = 'test_web_root'
    FILE_PATH = 'some_path'

    FILE_RELATIVE_PATH = os.path.join(FAKE_WEB_ROOT, FILE_PATH)

    settings = CustomSettings(WEB_ROOT=FAKE_WEB_ROOT)

    with remove_web_root_from_settings():
        instance = StaticGenerator(
            settings=settings,
        )

        assert os.path.exists(FILE_RELATIVE_PATH), 'File {file_path} already exists =P'.format(file_path=FILE_RELATIVE_PATH)
        instance.delete_from_path(FILE_PATH)
        assert not os.path.exists(FILE_RELATIVE_PATH), 'File {file_path} still exists'.format(file_path=FILE_RELATIVE_PATH)


def test_publish_loops_through_all_resources():
    FAKE_WEB_ROOT = 'test_web_root'
    FILE_PATH_1 = 'some_path_1'
    FILE_PATH_2 = 'some_path_2'
    FILE_CONTENT = 'some_content'

    FILE_RELATIVE_PATH_1 = os.path.join(FAKE_WEB_ROOT, FILE_PATH_1)
    FILE_RELATIVE_PATH_2 = os.path.join(FAKE_WEB_ROOT, FILE_PATH_2)

    settings = CustomSettings(WEB_ROOT=FAKE_WEB_ROOT)

    not os.path.exists(FILE_RELATIVE_PATH_1) or os.remove(FILE_RELATIVE_PATH_1)
    not os.path.exists(FILE_RELATIVE_PATH_2) or os.remove(FILE_RELATIVE_PATH_2)

    try:
        with remove_web_root_from_settings():
            get_content_from_path = StaticGenerator.get_content_from_path
            StaticGenerator.get_content_from_path = lambda self, path: FILE_CONTENT
            instance = StaticGenerator(
                FILE_PATH_1, FILE_PATH_2,
                settings=settings,
            )

            instance.publish()

            with open(FILE_RELATIVE_PATH_1, 'r') as fd1, open(FILE_RELATIVE_PATH_2, 'r') as fd2:
                assert fd1.readline() == FILE_CONTENT, 'File {file_path} content differs'.format(file_path=FILE_RELATIVE_PATH_1)
                assert fd2.readline() == FILE_CONTENT, 'File {file_path} content differs'.format(file_path=FILE_RELATIVE_PATH_2)

    finally:
        StaticGenerator.get_content_from_path = get_content_from_path


def test_delete_loops_through_all_resources():
    FAKE_WEB_ROOT = 'test_web_root'
    FILE_PATH_1 = 'some_path_1'
    FILE_PATH_2 = 'some_path_2'
    FILE_CONTENT = 'some_content'

    FILE_RELATIVE_PATH_1 = os.path.join(FAKE_WEB_ROOT, FILE_PATH_1)
    FILE_RELATIVE_PATH_2 = os.path.join(FAKE_WEB_ROOT, FILE_PATH_2)

    settings = CustomSettings(WEB_ROOT=FAKE_WEB_ROOT)

    with remove_web_root_from_settings():
        instance = StaticGenerator(
            FILE_PATH_1, FILE_PATH_2,
            settings=settings,
        )

        with open(FILE_RELATIVE_PATH_1, 'w') as fd1, open(FILE_RELATIVE_PATH_2, 'w') as fd2:
            fd1.write(FILE_CONTENT)
            fd2.write(FILE_CONTENT)

        assert os.path.exists(FILE_RELATIVE_PATH_1), 'File {file_path} was not created'.format(file_path=FILE_RELATIVE_PATH_1)
        assert os.path.exists(FILE_RELATIVE_PATH_2), 'File {file_path} was not created'.format(file_path=FILE_RELATIVE_PATH_2)

        instance.delete()

        assert not os.path.exists(FILE_RELATIVE_PATH_1), 'File {file_path} still exists =P'.format(file_path=FILE_RELATIVE_PATH_1)
        assert not os.path.exists(FILE_RELATIVE_PATH_2), 'File {file_path} still exists =P'.format(file_path=FILE_RELATIVE_PATH_2)


def test_can_create_dummy_handler():
    handler = DummyHandler()

    handler.load_middleware = lambda: True
    handler.get_response = lambda request: 'bar'

    middleware_method = lambda request, response: (request, response)  # NOQA

    handler._response_middleware = [middleware_method]
    result = handler('foo')

    assert result == ('foo', 'bar')


def test_bad_request_raises_proper_exception():
    from django.test.client import RequestFactory

    mox = Mox()

    mox.StubOutWithMock(RequestFactory, 'get')

    settings = CustomSettings(WEB_ROOT="test_web_root")

    path_mock = 'some_path'

    request_mock = mox.CreateMockAnything()
    request_mock.META = mox.CreateMockAnything()
    request_mock.META.setdefault('SERVER_PORT', 80)
    request_mock.META.setdefault('SERVER_NAME', 'localhost')

    RequestFactory.get.__call__(path_mock).AndReturn(request_mock)

    response_mock = mox.CreateMockAnything()
    response_mock.content = 'foo'
    response_mock.status_code = 500

    handler_mock = mox.CreateMockAnything()
    handler_mock.__call__().AndReturn(handler_mock)
    handler_mock.__call__(request_mock).AndReturn(response_mock)

    mox.ReplayAll()

    try:
        with remove_web_root_from_settings():
            dummy_handler = staticgenerator.staticgenerator.DummyHandler
            staticgenerator.staticgenerator.DummyHandler = handler_mock

            instance = StaticGenerator(
                settings=settings
            )

            instance.get_content_from_path(path_mock)
    except StaticGeneratorException, e:
        assert str(e) == 'The requested page("some_path") returned http code 500. Static Generation failed.'
        mox.VerifyAll()
        return
    finally:
        staticgenerator.staticgenerator.DummyHandler = dummy_handler
        mox.UnsetStubs()

    assert False, "Shouldn't have gotten this far."


def test_not_found_raises_proper_exception():
    from django.test.client import RequestFactory
    mox = Mox()

    settings = CustomSettings(WEB_ROOT="test_web_root")

    path_mock = 'some_path'

    request_mock = mox.CreateMockAnything()
    request_mock.META = mox.CreateMockAnything()
    request_mock.META.setdefault('SERVER_PORT', 80)
    request_mock.META.setdefault('SERVER_NAME', 'localhost')

    mox.StubOutWithMock(RequestFactory, 'get')
    RequestFactory.get.__call__(path_mock).AndReturn(request_mock)

    response_mock = mox.CreateMockAnything()
    response_mock.content = 'foo'
    response_mock.status_code = 404

    handler_mock_class = mox.CreateMockAnything()
    handler_mock = mox.CreateMockAnything()
    handler_mock_class.__call__().AndReturn(handler_mock)
    handler_mock.__call__(request_mock).AndReturn(response_mock)

    mox.ReplayAll()

    try:
        dummy_handler = staticgenerator.staticgenerator.DummyHandler
        staticgenerator.staticgenerator.DummyHandler = handler_mock_class

        instance = StaticGenerator(
            settings=settings
        )

        instance.get_content_from_path(path_mock)
    except StaticGeneratorException, e:
        assert str(e) == 'The requested page("some_path") returned http code 404. Static Generation failed.'
        mox.VerifyAll()
        return
    finally:
        staticgenerator.staticgenerator.DummyHandler = dummy_handler

    mox.UnsetStubs()
    assert False, "Shouldn't have gotten this far."


def test_request_exception_raises_proper_exception():
    from django.test.client import RequestFactory

    mox = Mox()

    http_request, model_base, manager, model, queryset = get_mocks(mox)
    settings = CustomSettings(WEB_ROOT="test_web_root")

    path_mock = 'some_path'

    request_mock = mox.CreateMockAnything()
    request_mock.META = mox.CreateMockAnything()
    request_mock.META.setdefault('SERVER_PORT', 80)
    request_mock.META.setdefault('SERVER_NAME', 'localhost')

    mox.StubOutWithMock(RequestFactory, 'get')
    RequestFactory.get.__call__(path_mock).AndReturn(request_mock)

    handler_mock = mox.CreateMockAnything()
    handler_mock.__call__().AndReturn(handler_mock)
    handler_mock.__call__(request_mock).AndRaise(ValueError("exception"))

    mox.ReplayAll()

    try:
        dummy_handler = staticgenerator.staticgenerator.DummyHandler
        staticgenerator.staticgenerator.DummyHandler = handler_mock

        instance = StaticGenerator(
            http_request=http_request,
            model_base=model_base,
            manager=manager,
            model=model,
            queryset=queryset,
            settings=settings
        )

        instance.get_content_from_path(path_mock)
    except StaticGeneratorException, e:
        assert str(e) == 'The requested page("some_path") raised an exception. Static Generation failed. Error: exception'
        mox.VerifyAll()
        return
    finally:
        staticgenerator.staticgenerator.DummyHandler = dummy_handler

    mox.UnsetStubs()
    assert False, "Shouldn't have gotten this far."
