from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.workflows.object_permanence.agents.analyze_diff_frames import analyze_diff_frames
from app.workflows.object_permanence.agents.analyze_static_frame import analyze_static_frame
from app.workflows.object_permanence.agents.check_frame_similarity import check_frame_similarity
from app.workflows.object_permanence.agents.filter_results import filter_results
from app.workflows.object_permanence.agents.save_analysis import save_analysis
from app.workflows.object_permanence.state import State


def create_compiled_state_graph() -> CompiledStateGraph:
    workflow = StateGraph(State)
    workflow.add_node("check_frame_similarity", check_frame_similarity)
    workflow.add_node("analyze_static_frame", analyze_static_frame)
    workflow.add_node("analyze_diff_frames", analyze_diff_frames)
    workflow.add_node("filter_results", filter_results)
    workflow.add_node("save_analysis", save_analysis)

    workflow.set_entry_point("check_frame_similarity")

    workflow.add_conditional_edges(
        "check_frame_similarity",
        lambda state: ["analyze_static_frame", "analyze_diff_frames"] if state.should_analyze else END,
    )

    workflow.add_edge("analyze_static_frame", "filter_results")
    workflow.add_edge("analyze_diff_frames", "filter_results")
    workflow.add_edge("filter_results", "save_analysis")

    workflow.set_finish_point("save_analysis")

    return workflow.compile()
