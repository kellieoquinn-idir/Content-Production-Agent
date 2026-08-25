from orchestrator.orchestrator import Orchestrator


def main():
    print("=" * 60)
    print("FIELDSTONE CONTENT PRODUCTION SYSTEM")
    print("=" * 60)

    topic = input("Enter a blog topic: ")

    orchestrator = Orchestrator()

    state = orchestrator.run(topic)

    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)

    if state.approved:
        print("Status: APPROVED")
    else:
        print("Status: REQUIRES REVISION")

    print(f"Retries: {state.retry_count}")


if __name__ == "__main__":
    main()