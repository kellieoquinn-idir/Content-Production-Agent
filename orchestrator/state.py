class WorkflowState:
    """
    Shared state for the orchestration workflow.
    """

    def __init__(self, topic):
        self.topic = topic

        # Entire pipeline output
        self.pipeline_result = None

        # Editor decision
        self.editor_verdict = None

        # Workflow status
        self.approved = False
        self.retry_count = 0

        # Human escalation flag
        self.requires_human_review = False