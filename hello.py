from flask import Flask
app = Flask(__name__)
app.config.from_envvar('ENDOFIT_SETTINGS')

@app.route('/', subdomain='<page_name>')
def hello_world(page_name):
    return "Hello {page_name}".format(**{'page_name': page_name})

if __name__ == '__main__':
    app.run()
