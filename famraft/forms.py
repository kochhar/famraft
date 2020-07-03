import inspect
import logging
from flask_wtf import FlaskForm
from wtforms import StringField, TextField, SubmitField
from wtforms.validators import DataRequired

log = logging.getLogger(__name__)


def safe_field_name(field_name):
    """Replaces forbidden charaters in a field name with periods."""
    return field_name


def create_entity_form(model):
    """Generates a new entity form from a model."""
    form_cls = getattr(model, 'wtform', None)
    if form_cls is None:
        model.wtform = dyn_form_from_model(model)
    form = model.wtform()
    return form


def dyn_form_from_model(model):
    """Creates a dynamically generated form class from a model class."""
    members = inspect.getmembers(model, lambda mem: not(inspect.isroutine(mem)))
    members = [(mem, val) for (mem, val) in members if not mem.startswith('__')]
    form_name = 'New%sForm' % (model.__name__,)
    return dyn_form_for_members(form_name, members)


def dyn_form_for_members(form_name, members):
    """Creates a dynamically generated form class for a given set of members."""
    form_cls = type(form_name, (FlaskForm,), {})
    fields = [(val, TextField(label=val)) for (mem, val) in members if mem == mem.upper()]
    # fields = [(name, TextField) ... ]
    _ = list(map(lambda tup: setattr(form_cls, safe_field_name(tup[0]), tup[1]), fields))
    setattr(form_cls,  'submit', SubmitField('Submit'))
    return form_cls
