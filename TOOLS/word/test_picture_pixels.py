"""核对PNG重编码与真实作者图片编辑的区分, 不操作正式Word或PPT."""

from io import BytesIO
from pathlib import Path
import sys
import unittest

from PIL import Image,PngImagePlugin

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from TOOLS.word.manuscript_conversion import same_image_pixels


class PicturePixelsTests(unittest.TestCase):
    def test_reencoding_keeps_source_equivalence(self):
        picture=Image.new('RGBA',(7,5),(17,83,112,255))
        a,b=BytesIO(),BytesIO();picture.save(a,format='PNG',compress_level=0)
        metadata=PngImagePlugin.PngInfo();metadata.add_text('Software','different encoder')
        picture.save(b,format='PNG',compress_level=9,pnginfo=metadata)
        self.assertNotEqual(a.getvalue(),b.getvalue())
        self.assertTrue(same_image_pixels(a.getvalue(),b.getvalue()))

    def test_pixel_and_alpha_edits_are_preserved(self):
        original=Image.new('RGBA',(7,5),(17,83,112,255));a=BytesIO();original.save(a,format='PNG')
        for value in [(18,83,112,255),(17,83,112,254)]:
            edited=original.copy();edited.putpixel((2,3),value);b=BytesIO();edited.save(b,format='PNG')
            self.assertFalse(same_image_pixels(a.getvalue(),b.getvalue()))

    def test_dimension_edits_are_preserved(self):
        a,b=BytesIO(),BytesIO()
        Image.new('RGB',(7,5)).save(a,format='PNG');Image.new('RGB',(7,6)).save(b,format='PNG')
        self.assertFalse(same_image_pixels(a.getvalue(),b.getvalue()))


if __name__=='__main__':unittest.main()
