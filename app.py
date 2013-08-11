import os

from flask import Flask, render_template, redirect, request, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.views import MethodView
from wtforms import BooleanField, Form, TextField, validators

app = Flask(__name__)
app.config.from_envvar('ENDOFIT_SETTINGS')
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

    def __repr__(self):
        return self.page_name

    def get_display_answer(self):
        if self.answer:
            return "YES"
        else:
            return "NO"


class QuestionObjectCreationForm(Form):
    page_name = TextField('Your question', [validators.Length(min=1, max=256)])


class Home(MethodView):

    def get(self):
        return render_template('home.html')


class VisitQuestionPage(MethodView):

    def get(self, page_name):
        question_object = self.get_question_object(page_name)
        if question_object:
            return self.get_existing_page(question_object)
        else:
            return self.get_placeholder_page(page_name)

    def get_question_object(self, page_name):
        question_object = QuestionObject.query.filter_by(page_name=page_name).first()
        return question_object

    def get_existing_page(self, question_object):
        return render_template('page.html', question_object=question_object)

    def get_placeholder_page(self, page_name, form=None):
        form = form or QuestionObjectCreationForm()
        return render_template(
            'new_page.html',
            page_name=page_name,
            form=form,
        )

    def post(self, page_name):
        question_object = self.get_question_object(page_name)
        if question_object:
            # if it exists, you can only POST to it from its admin page
            abort(403)
        else:
            return self.create_page(page_name)

    def create_page(self, page_name):
        raw_form = request.form
        form = QuestionObjectCreationForm(raw_form)
        if form.validate():
            new_question_object = QuestionObject(
                form.page_name.data,
                raw_form['answer']
            )
            db.session.add(new_question_object)
            db.session.commit()
            return redirect(url_for(
                'visit_question_page',
                page_name=new_question_object.page_name
            ))
        else:
            return self.get_placeholder_page(
                page_name=form.page_name.data,
                form=form
            )


app.add_url_rule(
    '/',
    view_func=Home.as_view('home')
)

app.add_url_rule(
    '/',
    subdomain='<page_name>',
    view_func=VisitQuestionPage.as_view('visit_question_page')
)


if __name__ == '__main__':
    app.run()
