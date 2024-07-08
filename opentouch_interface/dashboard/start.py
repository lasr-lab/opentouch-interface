import subprocess
import os


def main():
    viewer_path = os.path.join(os.path.dirname(__file__), 'pages/dashboard.py')
    cmd = ['streamlit', 'run', viewer_path]
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()
