import copy
import logging
import uuid
from pygraph.classes import digraph
from pygraph.algorithms import searching
from pygraph.algorithms.filters import find


log = logging.getLogger(__name__)


def init_db(app):
    """Iniitalizes a graphdb for the flask application."""
    if not hasattr(app, 'graphdb'):
        graphdb = PyGraphDB(app)
    return app.graphdb


def make_model_base(graphdb, model_class, relation_class, metadata=None):
        if metadata is not None and model_class.metadata is not metadata:
            model_class.metadata = metadata
        if metadata is not None and relation_class.metadata is not metadata:
            relation_class.metadata = metadata

        model_class._graphdb = graphdb
        relation_class._graphdb = graphdb
        return (model_class, relation_class)


class GraphDB(object):
    """Abstract class representing an in-memory graph databse.
    Implementation derive from this interface.

    An example of using this database: ::

        app = Flask(__name__)
        graphdb = PyGraphDB(app)

        class User(graphdb.GraphModel):
            pass
    """
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.graphdb = self
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['graphdb'] = self

    def add_node(self, node_id, **attributes):
        raise NotImplementedError

    def get_node(self, node_id):
        raise NotImplementedError

    def update_node(self, node_id, **attributes):
        raise NotImplementedError

    def delete_node(self, node_id):
        raise NotImplementedError

    def list_nodes(self, filter):
        raise NotImplementedError

    def node_attributes(self, node):
        raise NotImplementedError


class GraphModel(object):
    """Base class for representing a type in the graph.

    This class must be bound to an instance of GraphDB using the
    make_model_base function.
    """
    # Initialized by make_model_base function
    _graphdb = None
    @staticmethod
    def graphdb():
        return GraphModel._graphdb

    def __init__(self, node_id):
        node_attributes = GraphModel._graphdb.node_attributes(node_id)
        self.node_id = node_id
        self.node_attributes = node_attributes

    def __str__(self):
        return "%s(node_id=%s, node_attributes=%s)" % (
            self.__class__.__name__,
            self.node_id,
            self.node_attributes
        )

    @classmethod
    def types(cls):
        return cls.__name__

    @classmethod
    def create(cls, **attributes):
        """Creates a new instance of the GraphModel cls with a given
        attributes."""
        # TODO(kochhs): generalise create by examining the attributes
        # of the class passed in
        guid = uuid.uuid4()
        GraphModel._graphdb.add_node(guid, **attributes)
        return cls(guid)


class GraphRelation(object):

    def __init__(self, edge):
        self.edge = edge
        self.edge_properties = GraphRelation._graphdb.get_edge_properties(edge)
        self.edge_attributes = GraphRelation._graphdb.edge_attributes(edge)

    def __str__(self):
        return "%s(subj=%s, %s, obj=%s)" % (
            self.__class__.__name__,
            self.edge[0],
            self.edge_properties,
            self.edge[1]
        )

    @classmethod
    def types(cls):
        return cls.__name__

    @classmethod
    def relate(cls, relation, label=None, **attributes):
        """Relates a tuple of of GraphNode objects in relation by an edge with label,
        no weight and optional attributes."""
        (subj, obj) = relation
        edge = (subj.node_id, obj.node_id)
        if label is None: label = cls.types()
        GraphModel._graphdb.add_edge(edge, label=label, **attributes)
        return cls(edge)


class PyGraphDB(GraphDB):
    """Implementation of GraphDB interface using pygraph library."""
    def __init__(self, *args, **kwargs):
        super(PyGraphDB, self).__init__(*args, **kwargs)
        self._graph = digraph.digraph()

    def __getattr__(self, attr):
        try:
            return getattr(self._graph, attr)
        except AttributeError as e:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))

    def __iter__(self):
        return iter(self._graph)

    def add_node(self, node_id, **attributes):
        self._graph.add_node(node_id, attrs=list(attributes.items()))

    def get_node(self, node_id):
        found = searching.breadth_first_search(self._graph, filter=find.find(node_id))
        log.debug("Found get results: %s", found)
        return found

    def update_node(self, node_id, **attributes):
        if not self._graph.has_node(node_id):
            raise KeyError(node_id)
        current_attributes = set(self._graph.node_attributes(node_id))
        new_attributes = current_attributes.difference(attributes)
        self._graph.add_node_attribute(new_attributes)

    def delete_node(self, node_id):
        self._graph.del_node(node_id)

    def list_nodes(self, filter):
        """Returns a filtered iterator over the nodes in the graphdb."""
        found = searching.breadth_first_search(self._graph, filter=filter)
        log.debug("Found list results: %s", found)
        return found

    def node_attributes(self, node):
        return dict(self._graph.node_attributes(node))


class attributefilter(object):
    """PyGraph search filter which selects nodes having a given attribute value."""
    def __init__(self, attr, val):
        self.graph = None
        self.spanning_tree = None
        self.attr = attr
        self.val = val

    def configure(self, graph, spanning_tree):
        self.graph = graph
        self.spanning_tree = spanning_tree

    def __call__(self, node, parent):
        node_attributes = dict(self.graph.node_attributes(node))
        attr_val = node_attributes.get(self.attr, None)
        if attr_val == self.val:
            return True
        else:
            return False


class andfilter(object):
    """PyGraph search filter which selects notes by appliyng multiple filters."""
    def __init__(self, *filters):
        self.filters = filters

    def configure(self, graph, spanning_tree):
        for filter in self.filters:
            filter.configure(graph, spanning_tree)

    def __call__(self, node, parent):
        for filter in self.filters:
            if not filter(node, parent):
                return False
        return True


def bootstrap_db(model, relation):
    props1 = {
        'object.id': 'abc',
        'object.name': 'Abc',
        'object.type': 'Person',
        'person.gender': 'Male',
        'person.date_of_birth': '1900-01-01'
    }
    obj1 = model.create(**props1)

    props2 = {
        'object.id': 'def',
        'object.name': 'Def',
        'object.type': 'Person',
        'person.gender': 'Female',
        'person.date_of_birth': '1901-02-02'
    }
    obj2 = model.create(**props2)

    props3 = {
        'object.id': 'ghi',
        'object.name': 'Ghi',
        'object.type': 'Person',
        'person.gender': 'Female',
        'person.date_of_birth': '1925-02-02'
    }
    obj3 = model.create(**props3)

    props4 = {
        'object.id': 'jkl',
        'object.name': 'Jkl',
        'object.type': 'Person',
        'person.gender': 'Male',
        'person.date_of_birth': '1950-04-04'
    }
    obj4 = model.create(**props4)

    relation.relate((obj1, obj3), 'ParentChild')
    relation.relate((obj2, obj3), 'ParentChild')
    relation.relate((obj3, obj4), 'ParentChild')
