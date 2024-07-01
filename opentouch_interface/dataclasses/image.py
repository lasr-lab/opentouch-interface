import numpy as np
import h5py
import torch
from typing import Tuple, List, Optional


class Image:
    def __init__(self, image: np.ndarray, rotation: Tuple[int, int, int]) -> None:
        self.image = image
        self.rotation = rotation

    def as_cv2(self) -> np.ndarray:
        return self.image

    def as_tensor(self) -> torch.Tensor:
        return torch.from_numpy(np.transpose(self.image, self.rotation))


class ImageWriter:
    def __init__(self, file_path: str, fps: int):
        self.file_path = file_path
        self.frames_buffer = []
        self.total_frames = 0
        self.fps = fps

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save_buffer_to_file()

    def save(self, image: Image):
        self.frames_buffer.append(image)

    def _save_buffer_to_file(self):
        if not self.frames_buffer:
            return

        with h5py.File(self.file_path, 'a') as hf:
            if 'frames' not in hf:
                group = hf.create_group('frames')
                hf.attrs['fps'] = self.fps  # Save FPS as an attribute of the file
            else:
                group = hf['frames']

            for image in self.frames_buffer:
                dataset_name = f'image_{self.total_frames:06d}_cv2'
                group.create_dataset(dataset_name, data=image.as_cv2())
                self.total_frames += 1

        self.frames_buffer = []


class ImageReader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.frames = []
        self.current_index = 0
        self.fps = self._read_fps_from_file()
        self._load_data()

    def _read_fps_from_file(self) -> int:
        with h5py.File(self.file_path, 'r') as hf:
            return hf.attrs.get('fps', 30)  # Read FPS from file, default to 30 if not found

    def _load_data(self) -> List[Image]:
        images = []
        with h5py.File(self.file_path, 'r') as hf:
            if 'frames' in hf:
                group = hf['frames']
                for key in group.keys():
                    if key.startswith('image_') and key.endswith('_cv2'):
                        img_data = group[key][()]
                        images.append(Image(img_data, (0, 1, 2)))

        self.frames = images
        self.current_index = 0  # Reset index after reading all images
        return images

    def get_all(self) -> List[Image]:
        return self.frames

    def get_next(self) -> Optional[Image]:
        if self.current_index < len(self.frames):
            next_image = self.frames[self.current_index]
            self.current_index += 1
            return next_image
        else:
            return None

