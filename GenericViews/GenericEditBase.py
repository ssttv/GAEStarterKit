"""
Provides superclass for GenericEditExisting, GenericEditNew, and GenericDelete
"""

import flask
from google.appengine.ext import ndb
from wtforms_appengine.ndb import model_form

from .BetterModelConverter import BetterModelConverter
from .GenericBase import GenericBase


class GenericEditBase(GenericBase):
    template = 'generic-editor.html'

    def get_form(self):
        assert issubclass(self.model, ndb.Model)

        return model_form(self.model, exclude=self.form_exclude, only=self.form_include, base_class=SeaSurfForm, converter=BetterModelConverter(),
                          field_args=self.wtforms_field_args)

    def _pre_put_hook(self, obj):
        pass

    def _post_pook_hook(self, obj):
        pass

    def handle(self, urlsafe=None):
        FormClass = self.get_form()
        form, is_new, obj = self.handle_url(FormClass, urlsafe)
        flask.g.current_object = obj

        if form.validate_on_submit():
            if obj is None:
                obj = self.model()
            form.populate_obj(obj)
            self._pre_put_hook(obj)
            obj.put()
            self._post_pook_hook(obj)
            self.flash_message(obj)
            if self.retrieve_view:
                return flask.redirect(flask.url_for(self.retrieve_view, urlsafe=obj.key.urlsafe()))
            else:
                return self.redirect_after_completion()

        context = {
            self.variable_form: form,
            'is_new': is_new,
            'current_object': obj
        }

        if obj:
            obj = self.add_extra_fields(obj)

        return self.render(**context)

    def handle_url(self, FormClass, urlsafe=None):
        if urlsafe:
            obj = self.fetch_object(urlsafe)
            form = FormClass(flask.request.form, obj)
            is_new = False
        else:
            form = FormClass(flask.request.form)
            obj = None
            is_new = True
        return form, is_new, obj

    def post(self, urlsafe=None):
        return self.handle(urlsafe=urlsafe)

    def get(self, urlsafe=None):
        return self.handle(urlsafe=urlsafe)

    def fetch_object(self, urlsafe):
        try:
            key = ndb.Key(urlsafe=urlsafe)
        except:
            raise flask.abort(404)

        obj = key.get()
        if not obj:
            raise flask.abort(404)

        if not isinstance(obj, self.model):
            raise flask.abort(404)

        if not self.user_has_access(obj):
            raise flask.abort(403)

        return obj

    def redirect_after_completion(self):
        return flask.redirect('/')

from util.SeaSurfForm import SeaSurfForm
