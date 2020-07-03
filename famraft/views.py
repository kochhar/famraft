import copy
import json
import logging
import re
from flask import abort, redirect, render_template, request, url_for
from famraft import app
from famraft import forms as frm
from famraft import models as m

log = logging.getLogger(__name__)

u1 = m.Person.create('/person/1', name='Person 1')
u2 = m.Person.create('/person/2', name='Person 2', gender='Female')

@app.route('/', methods=['GET'])
def index():
    for person in m.Person.all():
        print(person.id, person.type, person.name, person.gender)

    return render_template('index.html')


@app.route('/person/new', methods=['GET', 'POST'])
def new_person():
    model_class = m.Person
    model_form = frm.create_entity_form(model_class)

    log.info(model_form.data)
    if model_form.validate_on_submit():
        entity = create_person(model_form)
        log.info("%s: %s", entity.id, entity)
        return redirect(url_for('view_person', id=entity.id))
    return render_template('new-person.htm.j2', form=model_form)


# @app.route('/<model_type>/new', methods=['GET', 'POST'])
# def new_entity_of_type(model_type):
#     model_class = getattr(m, model_type.title(), None)
#     log.debug("Found model class: %s for type: %s", model_class, model_type)
#     if model_class is None: abort(404)

#     model_form = frm.create_entity_form(model_class)
#     if model_form.validate_on_submit():
#         entity = create_entity(model_form, model_class)
#         return redirect(url_for('view_entity_of_type', model_type, entity.id))
#     return render_template('new-entity.htm.j2', model_type=model_type, form=model_form)


@app.route('/person/id/<id>', methods=['GET'])
def view_person(id):
    model_class = m.Person

    person_entity = model_class.by_id(id)
    if person_entity is None: abort(404)
    log.debug("Viewing entity: %s", person_entity)
    return render_template('view-person.htm.j2', person=person_entity)


# @app.route('/<model_type>/id/<id>', methods=['GET'])
# def view_entity_of_type(model_type, id):
#     model_class = getattr(m, model_type.title(), None)
#     if model_class is None: abort(404)

#     entity = model_class.by_id(id)
#     if entity is None: abort(404)
#     return render_template('view-entity.htm.j2', entity=entity)


def create_person(person_form):
    """Creates a new Person entity using data from the person form."""
    model_class = m.Person
    log.info(model_class.__bases__)

    person_properties = copy.deepcopy(person_form.data)
    person_properties.pop('csrf_token', None)
    person_properties.pop('submit', None)

    object_id = person_properties.pop('object.id', None)
    log.info(person_properties)
    if not object_id:
        object_id =  m.create_id(person_form.data['object.name'])
    return model_class.create(id=object_id, **person_properties)


@app.route('/person/search', methods=['GET'])
def search_person():
    q_str = request.args.get('q');
    q = json.loads(q_str)
    result = list(m.Person.by_attr(**q))
    log.info("found %s results: %s", len(result), result)
    return ", ".join(str(r) for r in result)
