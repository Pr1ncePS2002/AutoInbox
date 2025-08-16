from workflows.new_emails import process_new_emails
from workflows.existing_emails import process_existing_emails
from workflows.cleanup import daily_cleanup

if __name__ == "__main__":
    print("=== Running New Emails Workflow ===")
    new_wf = process_new_emails()
    new_wf.invoke({})

    print("=== Running Existing Emails Workflow ===")
    existing_wf = process_existing_emails()
    existing_wf.invoke({})

    print("=== Running Daily Cleanup ===")
    cleanup_wf = daily_cleanup()
    cleanup_wf.invoke({})
