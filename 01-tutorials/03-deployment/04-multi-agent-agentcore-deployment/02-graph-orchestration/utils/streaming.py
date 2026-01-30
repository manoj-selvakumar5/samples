"""Streaming display utilities for graph orchestration events.

Provides clean terminal output visualization for GraphBuilder streaming events.
Displays node execution progress, text output, and graph completion metrics.

Key features:
- Node-level progress tracking (start/stop events)
- Text accumulation from active nodes
- Graph completion summary with execution metrics
"""


class GraphStreamingDisplay:
    """Display GraphBuilder streaming events with node-level progress tracking.

    Handles three categories of graph execution events:
    1. Node lifecycle events (node_start, node_stop) - execution progress
    2. Text streaming events - real-time agent output from active nodes
    3. Graph completion events - summary metrics

    Tracks which nodes have been visited to provide execution path visualization
    matching the GraphBuilder's batch-based execution model.
    """

    def __init__(self, customer_id: str, query: str):
        """Initialize streaming display with session context.

        Args:
            customer_id: Customer identifier for display header.
            query: User query text for display header.
        """
        self.customer_id = customer_id
        self.query = query
        self.content = []
        self.active_node = None
        self.visited_nodes = []

    def start(self):
        """Display session header with customer ID and query."""
        print(f"Customer: {self.customer_id}")
        print(f"Query: {self.query}")
        print("=" * 60)

    def handle_event(self, event: dict):
        """Process and display a graph streaming event.

        Args:
            event: Structured event dictionary with 'type' field from graph orchestrator.
        """
        event_type = event.get("type")

        if event_type == "node_start":
            node_id = event.get("node_id", "unknown")
            self.active_node = node_id
            self.visited_nodes.append(node_id)
            print(f"\n>> Executing: {node_id}")

        elif event_type == "node_stop":
            node_id = event.get("node_id", "unknown")
            print(f"<< Completed: {node_id}")
            self.active_node = None

        elif event_type == "text":
            text = event.get("content", "")
            node_id = event.get("node_id", "")
            print(text, end="", flush=True)
            self.content.append(text)

        elif event_type == "graph_complete":
            total = event.get("total_nodes", 0)
            completed = event.get("completed_nodes", 0)
            exec_time = event.get("execution_time", 0)
            print(f"\n{'=' * 60}")
            print(f"Graph complete: {completed}/{total} nodes executed")
            if exec_time:
                print(f"Execution time: {exec_time:.1f}s")
            if self.visited_nodes:
                print(f"Execution path: {' -> '.join(self.visited_nodes)}")

    def get_full_response(self) -> str:
        """Retrieve complete response text from accumulated content chunks.

        Returns:
            Concatenated response text from all text events.
        """
        return "".join(self.content)
