from flask import Flask
import os
from dotenv import load_dotenv
from pathlib import Path
from slackeventsapi import SlackEventAdapter

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Test'
    slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)

    from .routes import routes

    app.register_blueprint(routes, url_prefix='/')

    return app
