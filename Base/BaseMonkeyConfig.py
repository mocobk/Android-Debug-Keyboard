import configparser
import os

# PATH = lambda p: os.path.abspath(
#     os.path.join(os.path.dirname(__file__), p)
# )
PATH = lambda p: p

def monkeyConfig(init_file):
    config = configparser.ConfigParser()
    config.read(init_file)
    app = {}
    app["package_name"] = config['DEFAULT']['package_name']
    # app["activity"] = config['DEFAULT']['activity']
    app["net"] = config['DEFAULT']['net']
    app["cmd"] = config['DEFAULT']['cmd'] + ">"
    return app
