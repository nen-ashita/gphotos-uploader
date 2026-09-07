import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from uploader import get_mime_type, collect_files, GooglePhotosUploader, is_supported_media

class TestUploader(unittest.TestCase):
    def test_mime_types(self):
        self.assertEqual(get_mime_type(Path("photo.jpg")), "image/jpeg")
        self.assertEqual(get_mime_type(Path("photo.PNG")), "image/png")
        self.assertEqual(get_mime_type(Path("photo.heic")), "image/heic")
        self.assertEqual(get_mime_type(Path("photo.HEIF")), "image/heic")
        self.assertEqual(get_mime_type(Path("photo.dng")), "image/x-adobe-dng")
        self.assertEqual(get_mime_type(Path("video.mp4")), "video/mp4")
        self.assertEqual(get_mime_type(Path("video.MOV")), "video/quicktime")

    def test_supported_media(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = Path(tmpdir) / "image1.JPG"
            p1.touch()
            p2 = Path(tmpdir) / "readme.txt"
            p2.touch()
            p3 = Path(tmpdir) / "movie.mov"
            p3.touch()

            self.assertTrue(is_supported_media(p1))
            self.assertFalse(is_supported_media(p2))
            self.assertTrue(is_supported_media(p3))

            collected = collect_files([str(Path(tmpdir))])
            names = [f.name for f in collected]
            self.assertIn("image1.JPG", names)
            self.assertIn("movie.mov", names)
            self.assertNotIn("readme.txt", names)

    @patch("requests.post")
    def test_upload_raw_file(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "mock_upload_token_123"
        mock_post.return_value = mock_response

        creds = MagicMock()
        creds.valid = True
        creds.token = "test_token"

        with tempfile.NamedTemporaryFile(suffix=".jpg") as tmp:
            tmp.write(b"\xff\xd8\xff\xe0testimage")
            tmp.flush()

            uploader = GooglePhotosUploader(creds)
            token = uploader.upload_raw_file(Path(tmp.name))

            self.assertEqual(token, "mock_upload_token_123")
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_token")
            self.assertEqual(kwargs["headers"]["X-Goog-Upload-Content-Type"], "image/jpeg")

    @patch("requests.post")
    def test_batch_create(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "newMediaItemResults": [
                {
                    "uploadToken": "token1",
                    "status": {"message": "Success"},
                    "mediaItem": {"id": "item1"}
                }
            ]
        }
        mock_post.return_value = mock_response

        creds = MagicMock()
        creds.valid = True
        creds.token = "test_token"

        uploader = GooglePhotosUploader(creds)
        res = uploader.batch_create_media_items([{"file_name": "test.jpg", "upload_token": "token1"}])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["mediaItem"]["id"], "item1")

if __name__ == "__main__":
    unittest.main()
