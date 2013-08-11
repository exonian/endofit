import os

from flask import Flask
from flask import render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.views import MethodView

app = Flask(__name__)
app.config.from_envvar('ENDOFIT_SETTINGS')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

MOCK_PAGES = ['foo', 'bar']

class VisitQuestionPage(MethodView):

    def get(self, page_name):
        question_object = self.get_question_object(page_name)
        if question_object:
            return self.get_existing_page(question_object)
        else:
            return self.get_placeholder_page(page_name)

    def get_question_object(self, page_name):
        if page_name in MOCK_PAGES:
            return page_name
        else:
            return None

    def get_existing_page(self, question_object):
        return render_template('hello.html', page_name=question_object)

    def get_placeholder_page(self, page_name):
        return render_template('new_page.html', page_name=page_name)

app.add_url_rule(
    '/',
    subdomain='<page_name>',
    view_func=VisitQuestionPage.as_view('visit_question_page')
)


if __name__ == '__main__':
    app.run()
