#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.core.handlers.base import BaseHandler
from django.middleware.transaction import TransactionMiddleware


class DummyHandler(BaseHandler):
    """Required to process request and response middleware"""

    def __call__(self, request):
        self.load_middleware()
        response = self.get_response(request)

        for middleware_method in self._response_middleware:
            if hasattr(middleware_method, 'im_self') and isinstance(middleware_method.im_self, TransactionMiddleware):
                continue

            response = middleware_method(request, response)
        return response
