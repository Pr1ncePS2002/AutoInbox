import argparse
from workflows.new_emails import process_new_emails
from workflows.existing_emails import process_existing_emails
from workflows.cleanup import daily_cleanup

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Gmail management using LangGraph.")
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of existing emails to classify. Default is 5."
    )
    args = parser.parse_args()

    # Pass the user-specified count to the workflow
    print("=== Running New Emails Workflow ===")
    new_wf = process_new_emails()
    new_wf.invoke({})

    # print(f"=== Running Existing Emails Workflow for {args.count} emails ===")
    # existing_wf = process_existing_emails()
    # existing_wf.invoke({"count": args.count}) # Pass the count as part of the initial state

    # print("=== Running Daily Cleanup ===")
    # cleanup_wf = daily_cleanup()
    # cleanup_wf.invoke({})