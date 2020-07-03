import logging
from flask import Flask
from famraft import db

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.config.from_object('config')

# Initialize the graphdb and the OGM base class
graphdb = db.init_db(app)
GraphModel, GraphRelation = db.make_model_base(graphdb, db.GraphModel, db.GraphRelation)
db.bootstrap_db(GraphModel, GraphRelation)
