import subprocess
import os


def main():
    viewer_path = os.path.join(os.path.dirname(__file__), 'pages/dashboard.py')
    cmd = f"streamlit run {viewer_path} --server.maxUploadSize 1024"
    subprocess.run(cmd, shell=True, check=True)


if __name__ == '__main__':
    main()
