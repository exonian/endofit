import os
basedir = os.path.abspath(os.path.dirname(__file__))

# these subdomains just redirect to the apex instead of being handled
# as questions
IGNORED_SUBDOMAINS = ['www']
