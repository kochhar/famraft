import copy
import logging

from famraft import db
from famraft import GraphModel
from famraft import GraphRelation

log = logging.getLogger('__name__')


def create_id(name):
    """Given a name converts it to an id without any spaces and prefixed by '/id'"""
    str_sub = re.compile('\s+')
    name = re.sub(str_sub, '_', name)
    return name.lower()


class Object(GraphModel):
    """Base class reppresenting objects in the model."""
    ID_KEY = 'object.id'
    TYPE_KEY = 'object.type'
    NAME_KEY = 'object.name'

    def __init__(self, node_id):
        super(Object, self).__init__(node_id)
        assert Object.ID_KEY in self.node_attributes
        assert Object.TYPE_KEY in self.node_attributes
        assert Object.NAME_KEY in self.node_attributes

    @classmethod
    def create(cls, id, name=None, **attributes):
        attributes.update({
            Object.TYPE_KEY: cls.types(),
            Object.ID_KEY: id,
        })
        if name is not None:
            attributes[Object.NAME_KEY] = name
        return super(Object, cls).create(**attributes)

    @classmethod
    def typefilter(cls):
        return db.attributefilter(Object.TYPE_KEY, cls.types())

    @classmethod
    def namefilter(cls, name):
        return db.attributefilter(Object.NAME_KEY, name)

    @classmethod
    def by_id(cls, id):
        mst, order = GraphModel._graphdb.list_nodes(db.attributefilter(Object.ID_KEY, id))
        nodes = list(mst.keys())
        if len(nodes) > 1: log.warn("Found %d objects with id: %s", len(nodes), id)

        return cls(nodes[0])

    @classmethod
    def by_attr(cls, **attrs):
        filters = [db.attributefilter(attr, val) for attr, val in attrs.items()]
        mst, order = GraphModel._graphdb.list_nodes(db.andfilter(*filters))
        return (cls(guid) for guid in mst.keys())

    @classmethod
    def all(cls):
        mst, order = GraphModel._graphdb.list_nodes(cls.typefilter())
        return (cls(guid) for guid in mst)

    @classmethod
    def named(cls, name):
        mst, _ = GraphModel._graphdb.list_nodes(cls.namefilter(name))
        return (cls(guid) for guid in mst.keys())

    @property
    def attrs(self):
        return copy.deepcopy(self.node_attributes)

    @property
    def neighbours(self):
        return GraphModel.graphdb().neighbours(self.node_id)

    @property
    def incidents(self):
        return GraphModel.graphdb().incidents(self.node_id)

    @property
    def id(self):
        return self.node_attributes[self.ID_KEY]

    @property
    def type(self):
        return self.node_attributes[self.TYPE_KEY]

    @property
    def name(self):
        return self.node_attributes[self.NAME_KEY]

    def related_by(self, related, relcls):
        return []

    def related_neighbours(self, relcls):
        """Returns neighbours of the current object which are related
        by Relation class relcls."""
        relations = [Relation((self.node_id, n)) for n in self.neighbours]
        return [relcls(r.edge) for r in relations if relcls.types() == r.label]

    def related_incidents(self, relcls):
        """Returns incidents of the current object which are related
        by Relation class relcls."""
        relations = [Relation((i, self.node_id)) for i in self.incidents]
        log.debug("Found %s incident relations on %s", relations, self)
        return [relcls(r.edge) for r in relations if relcls.types() == r.label]


class Relation(GraphRelation):
    """Base class representing relations in the model."""
    LABEL_KEY = 'label'
    WEIGHT_KEY = 'weight'

    def __init__(self, edge):
        super(Relation, self).__init__(edge)
        assert self.LABEL_KEY in self.edge_properties

    @classmethod
    def relate(cls, relation, **attributes):
        attributes.update({
            Relation.LABEL_KEY: cls.types()
        })
        return super(Relation, cls).relate(relation, **attributes)

    @property
    def label(self):
        return self.edge_properties[self.LABEL_KEY]

    @property
    def subj(self):
        return Object(self.edge[0])

    @property
    def obj(self):
        return Object(self.edge[1])

    @property
    def weight(self):
        return self.edge_properties.get(self.WEIGHT_KEY, 0.0)


class CompoundRelation(Object):
    """Compund relation between tow or more object with its own
    attributes."""
    pass


class User(Object):
    """Model representing a user-class in the database."""
    pass


class Person(Object):
    """Model representing a person in the database."""
    DOB_KEY = 'person.date_of_birth'
    GENDER_KEY = 'person.gender'

    def __init__(self, node_id):
        super(Person, self).__init__(node_id)

    @classmethod
    def create(cls, id, dob=None, gender=None, **attributes):
        if dob is not None:
            attributes[Person.DOB_KEY] = dob
        if gender is not None:
            attributes[Person.GENDER_KEY] = gender
        return super(Person, cls).create(id, **attributes)

    @property
    def date_of_birth(self):
        return self.node_attributes.get(self.DOB_KEY)

    @property
    def gender(self):
        return self.node_attributes.get(self.GENDER_KEY)

    def parent(self, parent_person):
        return ParentChild.relate((parent_person, self))

    @property
    def parents(self):
        return self.related_incidents(ParentChild)

    def child(self, child_person):
        return ParentChild.relate((self, child_person))

    @property
    def children(self):
        return self.related_neighbours(ParentChild)

    def marriage(self, dated_marriage):
        return Marriage.relate((self, dated_marriage))

    @property
    def marriages(self):
        return self.related_neighbours(Marriage)


class ParentChild(Relation):

    @property
    def parent(self):
        return Person(self.subj.node_id)

    @property
    def child(self):
        return Person(self.obj.node_id)



class Marriage(Relation):
    pass


class DatedMarriage(CompoundRelation):
    START_DATE_KEY = 'marriage.start_date'
    END_DATE_KEY = 'marriage.end_date'

    def participant(self, participant_person):
        return Marriage.relate((participant_person, self))
