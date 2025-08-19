import subprocess
import os


def main():
    """
    Main function to launch the Streamlit dashboard with specific configurations.

    This function builds the path to the `dashboard.py` file, constructs the appropriate command to run the
    Streamlit app with specific settings, and executes it using the `subprocess` module.

    Streamlit is configured with:
    - Maximum upload size set to 1024MB.
    - Suppressing warnings related to direct execution.

    :raises subprocess.CalledProcessError: If the subprocess command fails.
    """
    try:
        # Build the full path to the dashboard.py file
        viewer_path = os.path.join(os.path.dirname(__file__), 'pages/dashboard.py')

        # Construct the command to run the Streamlit app with custom settings
        cmd = (
            f"streamlit run {viewer_path} "
            f"--server.maxUploadSize 1024 "
            f"--global.showWarningOnDirectExecution false"
        )

        # Execute the command in a new subprocess
        subprocess.run(cmd, shell=True, check=True)

    except subprocess.CalledProcessError as e:
        # Handle the error if the subprocess fails
        print(f"Error: Streamlit failed to start. {e}")
        raise


if __name__ == '__main__':
    main()
