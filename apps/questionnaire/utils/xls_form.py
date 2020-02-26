import os
from tempfile import NamedTemporaryFile

from pyxform import create_survey_from_xls
from lxml import etree as ET


class XLSForm:
    @classmethod
    def create_xform(cls, xlsx_file):
        with NamedTemporaryFile(suffix='.xlsx') as tmp:
            tmp.write(xlsx_file.read())
            tmp.seek(0)
            survey = create_survey_from_xls(tmp)
            # survey.title = name
        return survey.to_xml()

    @classmethod
    def create_enketo_form(cls, xlsx_file):
        tree = ET.fromstring(cls.create_xform(xlsx_file))

        form_xslt = ET.parse(os.path.join(os.path.dirname(__file__), 'openrosa2html5form.xsl'))
        model_xslt = ET.parse(os.path.join(os.path.dirname(__file__), 'openrosa2xmlmodel.xsl'))

        form_transform = ET.XSLT(form_xslt)
        model_transform = ET.XSLT(model_xslt)

        form = form_transform(tree)
        model = model_transform(tree)

        return {
            'form': ET.tostring(form.getroot()[0]).decode(),
            'model': ET.tostring(model.getroot()[0]).decode(),
        }
