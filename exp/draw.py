from pydantic import BaseModel

from langgraph.graph import StateGraph, START, END


class DummyState(BaseModel):
    pass_count: int = 0


def increment_pass_count(state: DummyState):
    state.pass_count += 1
    return state


def route_b(state: DummyState):
    if state.pass_count == 0:
        return "X"
    else:
        return "Y"


migration_graph = StateGraph(DummyState)

migration_graph.add_node("B", increment_pass_count)
migration_graph.add_node("C", increment_pass_count)
migration_graph.add_node("D", increment_pass_count)

migration_graph.add_edge(START, "B")

migration_graph.add_conditional_edges(
    "B",
    route_b,
    {
        "X": "C",
        "Y": "D",
    },
)

migration_graph.add_edge("D", "B")
migration_graph.add_edge("C", END)

app = migration_graph.compile()


from buddy.utils import save_graph

save_graph(app)
