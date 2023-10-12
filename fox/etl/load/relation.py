import networkx as nx
import pandas as pd


from ..pandas import DjangoAccessor


__all__ = ("Relation",)


class Relation:
    """Describe a relationship between two models."""

    source = None
    """Source RecordSet."""
    target = None
    """Destination RecordSet."""
    column = None
    """Column on the source record set referring to target's index."""

    def __init__(self, source, target, source_field, target_field, many=False):
        self.source = source
        self.target = target
        self.source_field = source_field
        self.target_field = target_field
        self.source_col = DjangoAccessor.get_column(source_field)
        self.target_col = DjangoAccessor.get_column(target_field)
        self.many = many

    def resolve(self, source_df, target_df):
        sources = source_df.loc[pd.notnull(self.source_col)]
        sources_fks = sources[self.source_col]
        lookup = target_df[self.target_col].isin(sources_fks)
        return target_df.loc[lookup]

    def _get_graph_nodes(self):
        """Return a tuple of objects used as nodes in dependency graph."""
        return (self.source, self.target)

    def _get_graph_edges(self):
        """Return a tuple of `(source, target)` tuples used as edges in
        dependency graph."""
        return ((self.source, self.target),)


class DependencyGraph:
    """From provided relations, create and handle a dependency graph."""

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

        lookups = {
            obj: self._set_node(obj)
            for rel in relations
            for obj in rel._get_graph_nodes()
        }

        edges = [
            (lookups[source], lookups[target], {"relation": rel})
            for rel in relations
            for source, target in rel._get_graph_edges()
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
