import json
import zipfile
import tempfile
from pathlib import Path

import onnxruntime as ort
from streamlit.runtime.uploaded_file_manager import UploadedFile


class ModelLoader:
    """
    A class responsible for loading ONNX models from an uploaded zip file,
    attaching metadata, and returning an ONNX Runtime session.
    """

    @staticmethod
    def from_file(uploaded_file: UploadedFile) -> ort.InferenceSession:
        """
        Loads an ONNX model from an uploaded zip file, reads its metadata,
        and returns an ONNX Runtime session with metadata attributes set.

        Args:
            uploaded_file (UploadedFile): The uploaded zip file containing the ONNX model and metadata.

        Returns:
            onnxruntime.InferenceSession: The ONNX Runtime session with metadata attributes.
        """
        # Create a temporary directory to extract the files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the contents of the uploaded zip file into the temporary directory
            with zipfile.ZipFile(uploaded_file, 'r') as model_zip:
                model_zip.extractall(temp_dir)

            # Locate the ONNX model and metadata files
            onnx_file = next(Path(temp_dir).glob("*.onnx"))
            metadata_file = next(Path(temp_dir).glob("*_metadata.json"))

            # Read and parse the metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Initialize ONNX Runtime Inference Session
            session = ort.InferenceSession(str(onnx_file))

            # Set metadata attributes on the session
            for key, value in metadata.items():
                setattr(session, key, value)

            return session

    @staticmethod
    def from_path(path: str) -> ort.InferenceSession:
        """
        Loads an ONNX model from a zip file, reads its metadata, and returns an ONNX Runtime session
        with metadata attributes set.

        Returns:
            onnxruntime.InferenceSession: The ONNX Runtime session with metadata attributes.
        """
        # Ensure the zip file exists
        zip_path = Path(path)
        if not zip_path.is_file():
            raise FileNotFoundError(f"The file {path} does not exist.")

        # Create a temporary directory to extract the files
        temp_dir = zip_path.with_suffix('')
        temp_dir.mkdir(exist_ok=True)

        # Extract the zip file contents
        with zipfile.ZipFile(zip_path, 'r') as model_zip:
            model_zip.extractall(temp_dir)

        # Locate the ONNX model and metadata files
        onnx_file = next(temp_dir.glob("*.onnx"))
        metadata_file = next(temp_dir.glob("*_metadata.json"))

        # Read and parse the metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Initialize ONNX Runtime Inference Session
        session = ort.InferenceSession(str(onnx_file))

        # Set metadata attributes on the session
        for key, value in metadata.items():
            setattr(session, key, value)

        # Clean up temporary files
        for file in temp_dir.glob("*"):
            file.unlink()
        temp_dir.rmdir()

        return session
