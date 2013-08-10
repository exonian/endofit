from flask import Flask
from flask import render_template

app = Flask(__name__)
app.config.from_envvar('ENDOFIT_SETTINGS')

@app.route('/', subdomain='<page_name>')
def hello_world(page_name):
    return render_template('hello.html', page_name=page_name)

if __name__ == '__main__':
    app.run()
