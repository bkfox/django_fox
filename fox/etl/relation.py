import networkx as nx


__all__ = ("Relation",)


class Relation:
    """Describe a relationship between two models."""

    source = None
    """Source RecordSet."""
    target = None
    """Destination RecordSet."""
    column = None
    """Column on the source record set referring to target's index."""

    def __init__(self, source, target, column, many=False):
        self.source = source
        self.target = target
        self.column = column
        self.many = many

    def resolve(self, df):
        pass

    # TODO: provide node and edges from here => this ease m2m handling


class DependencyGraph:
    graph: nx.DiGraph = None
    """The graph by itself."""
    _relations: [Relation] = None
    """List of relations."""
    _nodes: dict = None
    """Dict of `{node: obj}`, where `node` is the node indice, and `obj` a
    relation source or target."""

    def __init__(self, relations=None):
        self._relations = tuple()
        self._nodes = []
        self.graph = nx.DiGraph()
        if relations:
            self.extend(relations)

    @property
    def relations(self) -> tuple[Relation]:
        """The list of registered relations."""
        return self._relations

    def add(self, relation):
        """Add a relation to the dependency graph."""
        self.relations = self.relations + (relation,)
        source = self._set_node(relation.source)
        target = self._set_node(relation.target)
        self.graph.add_edge(source, target, relation=relation)

    def extend(self, relations):
        """Extend dependency graph with the provided relations."""
        relations = tuple(relations)
        self.relations = self.relations + relations

        lookups = {rel.source: self._set_node(rel.source) for rel in relations}
        lookups.update(
            {
                rel.target: self._set_node(rel.target)
                for rel in relations
                if rel.target not in lookups
            }
        )

        edges = [
            (lookups[rel.source], lookups[rel.target], {"relation": rel})
            for rel in relations
        ]
        self.graph.update(edges=edges)

    def _set_node(self, obj):
        """Add object to nodes."""
        if obj in self._nodes:
            index = self._nodes.index(obj)
        else:
            # FIXME: concurrency race on the two next lines
            index = len(self._nodes)
            self._nodes.append(obj)
            self.graph.add_node(index, obj=obj)
        return index

    def get_sorted_dependencies(self) -> list:
        """Return a list of source and target objects topologically sorted."""
        nodes = nx.topological_sort(self.graph)
        return [self.graph.nodes[n]["obj"] for n in nodes]
