from critic import REVISE_LIMIT, parse_decision
from orchestrator.state import WorkflowState
from pipeline import run_pipeline


class Orchestrator:
    """
    Controls the overall content production workflow.
    Responsible for:
    - Creating workflow state
    - Running the pipeline (which includes critic retry)
    - Recording the editor's final decision
    """

    def __init__(self):
        self.state = None

    def get_decision(self, verdict):
        return parse_decision(verdict)

    def run(self, topic):
        self.state = WorkflowState(topic)

        print("\n" + "=" * 50)
        print("FIELDSTONE CONTENT ORCHESTRATOR")
        print("=" * 50)
        print(f"Topic: {topic}")
        print(f"Human editor flagged if REVISE is given {REVISE_LIMIT} times")
        print("Starting content production workflow...\n")

        result = run_pipeline(topic)

        print("✓ Pipeline execution completed.\n")

        self.state.pipeline_result = result
        self.state.editor_verdict = result["editor_verdict"]
        self.state.retry_count = result["retry_count"]
        self.state.requires_human_review = result["requires_human_review"]

        decision = result.get("decision") or self.get_decision(self.state.editor_verdict)
        self.state.approved = decision == "PASS"

        print("=" * 50)
        print("WORKFLOW SUMMARY")
        print("=" * 50)
        print("Editor Decision :", decision)
        print("REVISE count    :", result.get("revise_count", 0), "/", REVISE_LIMIT)

        if decision == "PASS":
            print("Next Action    : Publish Content")
        else:
            print("Next Action    : Human Editor Review")
            if result.get("human_review_reason"):
                print("Reason         :", result["human_review_reason"])

        return self.state
