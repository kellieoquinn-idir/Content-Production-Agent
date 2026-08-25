class WorkflowState:
    """
    Shared state that moves through the entire workflow.
    Every agent reads from and updates this object.
    """

    def __init__(self, topic):
        self.topic = topic
        self.research = None
        self.outline = None
        self.draft = None
        self.review = None
        self.approved = False
        self.retry_count = 0