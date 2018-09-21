import tempfile
import os
import logging
import shutil
from subprocess import call
from selenium import webdriver

from django.core.files.base import File
from django.conf import settings

class Thumbnailer:
    def __init__(self, doc, type):
        self.doc = doc
        self.type = type

    def get_thumbnail(self):
        pass

class DocThumbnailer(Thumbnailer):
    def get_thumbnail(self):
        """
        Convert files to  image using libreoffice headless
        """
        # Create copy of the doc
        # libreoffice command requires local file
        temp_doc = tempfile.NamedTemporaryFile(dir=settings.BASE_DIR, suffix='.{}'.format(self.type))
        self.doc.seek(0)
        temp_doc.write(self.doc.read())
        temp_doc.flush()
        # libreoffice doesn't provide custom filename and generates file of
        # same name as source file with converted extension
        call(['libreoffice', '--headless', '--convert-to',
              'png', temp_doc.name, '--outdir', settings.BASE_DIR])
        fileprefix = os.path.splitext(os.path.basename(temp_doc.name))[0]
        thumbnail = os.path.join(settings.BASE_DIR, '{}.png'.format(fileprefix))
        temp_doc.close()
        return File(open(thumbnail, 'rb'))


class WebThumbnailer(Thumbnailer):
    """
    Generate thumbnail of the lead using selenium
    and headless chrome, window size is same as Pixel 2
    to make thumbnail smaller and compact
    """
    def get_thumbnail(self):
        if self.doc is not None:
            # Filename TODO: naming?
            file_name = 'tmp.png'
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            options.add_argument('window-size=412x732')
            # fix for root user
            options.add_argument("no-sandbox")
            # running in docker
            options.add_argument("disable-gpu")
            mobile_emulation = {
                "deviceMetrics": { "width": 412, "height": 732, "pixelRatio": 3.0 },
            }
            options.add_experimental_option("mobileEmulation", mobile_emulation)
            browser = webdriver.Chrome(chrome_options=options)
            browser.get('http://google.com')
            # wait 2 sec to finish rendering
            browser.implicitly_wait(2)
            browser.get_screenshot_as_file(file_name)
            return File(open(file_name, 'rb'))
        return None
