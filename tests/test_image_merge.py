import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import find_images


class ImageMergeTests(unittest.TestCase):
    def test_failed_image_encoding_preserves_existing_asset_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);dest = root / 'public/assets/part-1.webp'
            dest.parent.mkdir(parents=True);dest.write_bytes(b'old image')
            class FailedImage:
                def save(self, *args, **kwargs):raise OSError('injected encoder failure')
            with self.assertRaises(OSError):find_images.store_image(root,dest,FailedImage())
            self.assertEqual(dest.read_bytes(),b'old image')

    def test_lookup_miss_keeps_only_valid_existing_local_image_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'data').mkdir()
            (root / 'public/assets').mkdir(parents=True)
            (root / 'public/assets/part-1.webp').write_bytes(b'validated image')
            old = [{'id': 'one', 'image': '/assets/part-1.webp', 'imageSource': 'https://parts.example/1'},
                   {'id': 'two', 'image': '/assets/missing.webp', 'imageSource': 'https://parts.example/2'}]
            import json
            (root / 'data/images.json').write_text(json.dumps(old), encoding='utf-8')
            with patch.object(find_images, 'root', root):
                merged = find_images.merge_results(root, [{'id': 'one'}, {'id': 'two'}])
            self.assertEqual(merged[0], old[0])
            self.assertEqual(merged[1], {'id': 'two'})
            self.assertEqual((root / 'public/assets/part-1.webp').read_bytes(), b'validated image')


if __name__ == '__main__':
    unittest.main()
