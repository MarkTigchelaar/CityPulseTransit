import subprocess
import sys

def get_clean_exception_message(generic_exception: Exception) -> str:
    return (
        generic_exception.stderr.strip()
        if generic_exception.stderr
        else "No error message captured"
    )

def run_command(command, description, continue_if_failed=False):
    try:
        subprocess.check_call(command, shell=True)
        print(f" {description} Complete!\n")
    except subprocess.CalledProcessError as e:
        message = get_clean_exception_message(e)
        if continue_if_failed:
            print(f"Command {description} failed with: {message}")
            print("Non critical, or expected error, continuing")
        else:
            print(f"Error during: {description}:\n {message}")
            sys.exit(1)
