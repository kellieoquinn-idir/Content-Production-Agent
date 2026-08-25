from orchestrator.state import WorkflowState
from pipeline import run_pipeline


class Orchestrator:
    """
    Controls the overall content production workflow.
    Responsible for:
    - Creating workflow state
    - Running the pipeline
    - Interpreting the editor's decision
    - Returning the completed workflow state
    """

    def __init__(self):
        self.state = None

    def get_decision(self, verdict):
        """
        Extract PASS or REVISE from the editor's response.
        """
        verdict = verdict.upper()

        if "REVISE" in verdict:
            return "REVISE"

        if "PASS" in verdict:
            return "PASS"

        return "UNKNOWN"

    def run(self, topic):
        # Create workflow state
        self.state = WorkflowState(topic)

        print("\n" + "=" * 50)
        print("FIELDSTONE CONTENT ORCHESTRATOR")
        print("=" * 50)
        print(f"Topic: {topic}")
        print("Starting content production workflow...\n")

        # Run the integrated pipeline
        result = run_pipeline(topic)

        print("✓ Pipeline execution completed.\n")

        # Save results
        self.state.pipeline_result = result
        self.state.editor_verdict = result["editor_verdict"]

        # Determine editor decision
        decision = self.get_decision(self.state.editor_verdict)

        print("=" * 50)
        print("WORKFLOW SUMMARY")
        print("=" * 50)

        if decision == "PASS":
            self.state.approved = True

            print("Editor Decision : PASS")
            print("Retry Count    :", self.state.retry_count)
            print("Next Action    : Publish Content")

        elif decision == "REVISE":
            self.state.approved = False
            self.state.retry_count += 1

            print("Editor Decision : REVISE")
            print("Retry Count    :", self.state.retry_count)
            print("Next Action    : Retry Pipeline")

        else:
            self.state.approved = False

            print("Editor Decision : UNKNOWN")
            print("Next Action    : Human Review Required")

        return self.state