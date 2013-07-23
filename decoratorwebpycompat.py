#!/usr/bin/env python
#
#

import httplib2
import web

from google.appengine.api import memcache
from google.appengine.api import users
from oauth2client import appengine


class WebPyOAuth2DecoratorFromClientSecrets(
        appengine.OAuth2DecoratorFromClientSecrets):

    class _FakeWebApp(object):
        def __init__(self, url0, uri0, relurl):
            class _FakeWebObRequest:
                url = url0
                uri = uri0
                def ru(*args):
                    return relurl
                relative_url = ru
            self.request = _FakeWebObRequest()

    def _display_error_message(self, *args):
        pass

    def oauth_required(self, method):
        # decorator!!
        def check_oauth(oldself, *args, **kwargs):
            if self._in_error:
                return ('<html><body>%s</body></html>' % 
                            appengine._safe_html(self._message))
            url = web.ctx.home + web.ctx.path
            uri = web.ctx.home + web.ctx.fullpath
            relurl = web.ctx.home + self.callback_path
            request_handler = self._FakeWebApp(url, uri, relurl)
            user = users.get_current_user()
            if not user:
                raise web.seeother(users.create_login_url(uri))

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
            url = web.ctx.home + web.ctx.path
            uri = web.ctx.home + web.ctx.fullpath
            relurl = web.ctx.home + self._callback_path
            request_handler = self._FakeWebApp(url, uri, relurl)
            user = users.get_current_user()
            if not user:
                raise web.seeother(users.create_login_url(url))

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
                    ruri = web.ctx.home + web.ctx.fullpath
                    ruri = decorator._FakeWebApp('','',ruri)
                    decorator._create_flow(web.ctx.fullpath) #ruri
                    data.code
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


