import os
import uuid

from flask import abort, Flask, render_template, redirect, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.views import MethodView
from wtforms import BooleanField, Form, TextField, validators

app = Flask(__name__)
app.config.from_envvar('ENDOFIT_SETTINGS')
app.config['SERVER_NAME'] = os.environ['SERVER_NAME']
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

class QuestionObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(256), index=True, unique=True)
    secret = db.Column(db.String(56))
    answer = db.Column(db.Boolean())
    email = db.Column(db.String(120))

    def __init__(self, page_name, answer, email=None):
        self.page_name = page_name
        self.answer = answer
        self.email = email
        self.secret = self._make_secret()

    def __repr__(self):
        return self.page_name

    def get_display_answer(self):
        if self.answer:
            return "YES"
        else:
            return "NO"

    def _make_secret(self):
        return uuid.uuid4().hex


class QuestionObjectCreationForm(Form):
    page_name = TextField(
        'Your question',
        [
            validators.Regexp(r'^\w+$', message='Letters and numbers only, please'),
            validators.Length(min=1, max=256),
        ]
    )


class Home(MethodView):

    def get(self):
        return render_template('home.html')


class QuestionPageMixin(object):

    def get_question_object(self, page_name):
        question_object = QuestionObject.query.filter_by(page_name=page_name).first()
        return question_object


class VisitQuestionPage(QuestionPageMixin, MethodView):

    def get(self, page_name):
        if page_name in app.config['IGNORED_SUBDOMAINS']:
            return redirect(url_for('home'))
        question_object = self.get_question_object(page_name)
        if question_object:
            return self.get_existing_page(question_object)
        else:
            return self.get_placeholder_page(page_name)

    def get_existing_page(self, question_object):
        return render_template('page.html', question_object=question_object)

    def get_placeholder_page(self, page_name, form=None):
        form = form or QuestionObjectCreationForm()
        return render_template(
            'new_page.html',
            page_name=page_name,
            form=form,
        )

    def page_exists(self, page_name):
        form = QuestionObjectCreationForm()
        return render_template(
            'page_exists.html',
            form=form,
            existing_page_name=page_name,
        )

    def post(self, page_name):
        raw_form = request.form
        form = QuestionObjectCreationForm(raw_form)
        page_name = form.page_name.data or page_name
        question_object = self.get_question_object(page_name)
        if question_object:
            # if it exists, this isn't the place to post to it (editing is
            # from the admin view) so this is a potential duplicate that
            # the user should be told about
            return self.page_exists(page_name)
        else:
            return self.create_page(raw_form, form)

    def create_page(self, raw_form, form):
        if form.validate():
            new_question_object = QuestionObject(
                form.page_name.data,
                raw_form['answer']
            )
            db.session.add(new_question_object)
            db.session.commit()
            return redirect(url_for(
                'secret_admin',
                page_name=new_question_object.page_name,
                secret=new_question_object.secret,
            ))
        else:
            return self.get_placeholder_page(
                page_name=form.page_name.data,
                form=form
            )


class PublicAdmin(QuestionPageMixin, MethodView):

    def get(self, page_name):
        if page_name in app.config['IGNORED_SUBDOMAINS']:
            return redirect(url_for('home'))
        question_object = self.get_question_object(page_name)
        if not question_object:
            return redirect(url_for(
                'visit_question_page',
                page_name=page_name
            ))
        return render_template(
            'public_admin.html',
            question_object=question_object,
        )

    def post(self, page_name):
        # trim out any spaces from input (means users can submit as
        # separate words and thus take advantage of autocomplete)
        secret = request.form.get('secret', '').replace(" ", "")
        question_object = self.get_question_object(page_name)
        if question_object and question_object.secret == secret:
            return redirect(url_for(
                'secret_admin',
                page_name=page_name,
                secret=secret,
            ))
        else:
            return self.get(page_name=page_name)


class SecretAdmin(QuestionPageMixin, MethodView):

    def get(self, page_name, secret):
        if page_name in app.config['IGNORED_SUBDOMAINS']:
            return redirect(url_for('home'))
        question_object = self.get_question_object(page_name)
        if question_object and question_object.secret == secret:
            return self.get_admin(question_object)
        else:
            abort(404)

    def get_admin(self, question_object):
        return render_template(
            'secret_admin.html',
            question_object=question_object,
        )

    def post(self, page_name, secret):
        question_object = self.get_question_object(page_name)
        question_object.answer = request.form['answer']
        db.session.commit()
        return redirect(url_for(
            'secret_admin',
            page_name=page_name,
            secret=question_object.secret,
        ))


app.add_url_rule(
    '/',
    view_func=Home.as_view('home')
)

app.add_url_rule(
    '/',
    subdomain='<page_name>',
    view_func=VisitQuestionPage.as_view('visit_question_page')
)

app.add_url_rule(
    '/admin',
    subdomain='<page_name>',
    view_func=PublicAdmin.as_view('public_admin')
)

app.add_url_rule(
    '/<secret>',
    subdomain='<page_name>',
    view_func=SecretAdmin.as_view('secret_admin')
)

import logging
stream_handler = logging.StreamHandler()
app.logger.addHandler(stream_handler)
app.logger.setLevel(logging.INFO)
