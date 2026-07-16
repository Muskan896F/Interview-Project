from langgraph.graph import StateGraph, END
from app.graph.state import ConversationState
from app.graph import nodes, router
from app.config import constants
from app.utils.logger import logger

def build_agent_workflow():
    """Compiles the StateGraph for the outbound agent flow."""
    workflow = StateGraph(ConversationState)

    # 1. Register all nodes
    workflow.add_node(constants.Node.GREETING, nodes.greeting_node)
    workflow.add_node(constants.Node.PERMISSION, nodes.permission_node)
    workflow.add_node(constants.Node.LANGUAGE_DETECTION, nodes.language_detection_node)
    workflow.add_node(constants.Node.QUALIFICATION, nodes.qualification_node)
    workflow.add_node(constants.Node.KNOWLEDGE, nodes.knowledge_node)
    workflow.add_node(constants.Node.OBJECTION, nodes.objection_node)
    workflow.add_node(constants.Node.BOOKING_DECISION, nodes.booking_decision_node)
    workflow.add_node(constants.Node.BOOKING, nodes.booking_node)
    workflow.add_node(constants.Node.FOLLOWUP, nodes.followup_node)
    workflow.add_node(constants.Node.SUMMARY, nodes.summary_node)
    workflow.add_node(constants.Node.END, nodes.end_node)

    # 2. Define starting entry node
    # Every turn begins with language detection to parse input
    workflow.set_entry_point(constants.Node.LANGUAGE_DETECTION)

    # 3. Add conditional edges from Language Detection to the target turn node
    workflow.add_conditional_edges(
        constants.Node.LANGUAGE_DETECTION,
        router.route_next_node,
        {
            constants.Node.GREETING: constants.Node.GREETING,
            constants.Node.PERMISSION: constants.Node.PERMISSION,
            constants.Node.QUALIFICATION: constants.Node.QUALIFICATION,
            constants.Node.KNOWLEDGE: constants.Node.KNOWLEDGE,
            constants.Node.OBJECTION: constants.Node.OBJECTION,
            constants.Node.BOOKING_DECISION: constants.Node.BOOKING_DECISION,
            constants.Node.BOOKING: constants.Node.BOOKING,
            constants.Node.FOLLOWUP: constants.Node.FOLLOWUP,
            constants.Node.SUMMARY: constants.Node.SUMMARY,
            constants.Node.END: constants.Node.END
        }
    )

    # 4. Every logic execution node goes directly to END so the API call completes
    workflow.add_edge(constants.Node.GREETING, END)
    workflow.add_edge(constants.Node.PERMISSION, END)
    workflow.add_edge(constants.Node.QUALIFICATION, END)
    workflow.add_edge(constants.Node.KNOWLEDGE, END)
    workflow.add_edge(constants.Node.OBJECTION, END)
    workflow.add_edge(constants.Node.BOOKING_DECISION, END)
    workflow.add_edge(constants.Node.BOOKING, END)
    workflow.add_edge(constants.Node.FOLLOWUP, END)
    workflow.add_edge(constants.Node.SUMMARY, END)
    workflow.add_edge(constants.Node.END, END)

    logger.info("LangGraph StateGraph assembled and compiled in turn-based mode.")
    return workflow.compile()

agent_workflow = build_agent_workflow()
