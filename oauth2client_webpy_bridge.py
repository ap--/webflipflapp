#!/usr/bin/env python

import web
import urlparse

class _FakeWebObOut(object):
    def __init__(self):
        self._buffer = ''
    def write(self, x):
        self._buffer += x

class _FakeWebObResponse(object):
    def __init__(self):
        self.out = _FakeWebObOut()

class _FakeWebObRequest(object):
    @property
    def url(self):
        return web.ctx.home + web.ctx.fullpath
    @property
    def uri(self):
        return web.ctx.home + web.ctx.fullpath
    def relative_url(self, x):
        return urlparse.urljoin(self.uri, x)

class FakeWebapp2RequestHandler(object):

    def __init__(self):
        if hasattr(self, 'GET'):
            def hack(f):
                def nGET(*args, **kwargs):
                    tmp = f(*args, **kwargs)
                    if self.response.out._buffer:
                        return tmp + self.response.out._buffer
                    else:
                        return tmp
                return nGET
            self.GET = hack(self.GET)

    response = _FakeWebObResponse()
    request = _FakeWebObRequest()

    def redirect(self, x):
        web.seeother(x)


"""
class WebPyOAuth2DecoratorFromClientSecrets(
        appengine.OAuth2DecoratorFromClientSecrets):

    def _display_error_message(self, *args):
        pass

    def oauth_required(self, method):
        # decorator!!
        def check_oauth(oldself, *args, **kwargs):
            if self._in_error:
                return ('<html><body>%s</body></html>' % 
                            appengine._safe_html(self._message))
            
            request_handler = self._FakeWebApp(web.ctx)
            user = users.get_current_user()
            if not user:
                raise web.seeother(users.create_login_url(request_handler.request.uri))

            self._create_flow(request_handler)

            self.flow.params['state'] = appengine._build_state_value(
                                                    request_handler, user)
            self.credentials = appengine.StorageByKeyName(
                                            appengine.CredentialsModel, 
                                            user.user_id(), 'credentials').get()
            if not self.has_credentials():
                raise web.seeother(self.authorize_url())
            try:
                return method(oldself, *args, **kwargs)
            except appengine.AccesTokenRefreshError:
                raise web.seeother(self.authorize_url())
            
        return check_oauth

    def oauth_aware(self, method):
        # decorator!!
        def setup_oauth(oldself, *args, **kwargs):
            if self._in_error:
                return ('<html><body>%s</body></html>' % 
                            appengine._safe_html(self._message))
            
            request_handler = self._FakeWebApp(web.ctx)
            user = users.get_current_user()
            if not user:
                raise web.seeother(users.create_login_url(request_handler.request.uri))

            self._create_flow(request_handler)

            self.flow.params['state'] = appengine._build_state_value(
                                                    request_handler, user)
            self.credentials = appengine.StorageByKeyName(
                                            appengine.CredentialsModel, 
                                            user.user_id(), 'credentials').get()
            return method(oldself, *args, **kwargs)
        return setup_oauth

    def callback_application(self):
        raise NotImplementedError()
    
    def callback_handler(self):
        decorator = self

        class WebPyOAuth2Handler(object):
            # @login_required # XXX we'll do that here
            def GET(self):
                # decorator @login_required
                user = users.get_current_user()
                if not user:
                    web.seeother(users.create_login_url(web.ctx.homepath + 
                                                        web.ctx.fullpath))
                data = web.input(error=None, state='')
                if data.error: # XXX
                    errormsg = data.error_description
                    return ('The authorization request faiiiled: %s' %
                                appengine._safe_html(errormsg))
                else:
                    user = users.get_current_user()
                    try:
                        decorator._FakeWebApp("", "", str(ruri))
                        decorator._create_flow(dec) #ruri
                    except Exception as e:
                        return 'error when creating flow! %s %s' % (e, web.ctx.fullpath)
                    try:
                        credentials = decorator.flow.step2_exchange(
                                                code=unicode(data.code))
                    except Exception as e:
                        return 'error when flowstep2 %s' % e
                    try:
                        appengine.StorageByKeyName(
                                    appengine.CredentialsModel, user.user_id(),
                                    'credentials').put(credentials)
                    except Exception as e:
                        return 'error when gae Storage %s' % e
                    try:
                        redirect_uri = appengine._parse_state_value(
                                                    data.state, user)
                    except Exception as e:
                        return 'error when reduri %s' % e
                    try:
                        if (decorator._token_response_param and 
                                    credentials.token_response):
                            resp_json = appengine.simplejson.dumps(
                                    credentials.token_response)
                            redirect_uri = util._add_query_parameter(
                                redirect_uri, decorator._token_response_param,
                                resp_json)
                    except Exception as e:
                        return 'something if %s' % e 
                    web.seeother(redirect_uri)
        
        return WebPyOAuth2Handler
"""

