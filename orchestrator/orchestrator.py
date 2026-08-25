from orchestrator.state import WorkflowState


class Orchestrator:
    """
    Controls the flow of the multi-agent system.
    """

    def __init__(self):
        self.state = None

    def run(self, topic):
        self.state = WorkflowState(topic)

        print(f"Starting workflow for: {self.state.topic}")

        return self.state