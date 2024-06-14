import datetime

from lead.models import Lead

PDNA_MOCK_DATA_RAW = """
<!DOCTYPE html>
<html>
   <body class="path-node page-node-type-page page-post-disaster-needs-assessments has-glyphicons no-filters">
        <table>
        <thead>
        </thead>
        <tbody>
        </tbody>
        <tbody class="tdtext">
            <tr class="grey" height="20">
                <td class="rtecenter" height="20"><span class="tdtext"><a href="https://www.gfdrr.org/sites/default/files/Seychelles-Fantala-PDNA.pdf" style="text-decoration: none;" target="_blank">Seychelles</a></span></td>
                <td class="rtecenter"><span class="tdtext">2016</span></td>
                <td class="rtecenter"><span class="tdtext">Cyclone</span></td>
            </tr>
            <tr class="white" height="20">
                <td class="rtecenter" height="20"><span class="tdtext"><a href="/sites/default/files/publication/Post%20Disaster%20Needs%20Assessments%20CYCLONE%20WINSTON%20Fiji%202016%20%28Online%20Version%29.pdf" style="text-decoration: none;" target="_blank">Fiji</a></span></td>
                <td class="rtecenter"><span class="tdtext">2016</span></td>
                <td class="rtecenter"><span class="tdtext">Cyclone</span></td>
            </tr>
            <tr class="grey" height="20">
                <td class="rtecenter" height="20"><span class="tdtext"><a href="/sites/default/files/publication/Myanmar%20FY2016.pdf" style="text-decoration: none;" target="_blank">Myanmar</a></span></td>
                <td class="rtecenter"><span class="tdtext">2015</span></td>
                <td class="rtecenter"><span class="tdtext">Flood</span></td>
            </tr>
            <tr class="white">
                <td class="rtecenter" height="20"><a href="https://www.gfdrr.org/sites/default/files/publication/tbilisi_disaster_needs_assessment_2015.pdf"><span class="tdtext">Georgia</span></a></td>
                <td class="rtecenter"><span class="tdtext">2015-2018</span></td>
                <td class="rtecenter"><span class="tdtext">Flood</span></td>
            </tr>
            <tr class="grey">
                <td class="rtecenter" height="20"><a href="https://www.gfdrr.org/sites/default/files/publication/Nepal%20Earthquake%202015%20Post-Disaster%20Needs%20Assessment%20Vol%20A.pdf"><span class="tdtext">Nepal</span></a></td>
                <td class="rtecenter"><span class="tdtext">2015</span></td>
                <td class="rtecenter"><span class="tdtext">Earthquake</span></td>
            </tr>
            <tr class="white">
                <td class="rtecenter" height="20"><a href="https://www.gfdrr.org/sites/default/files/publication/Vanuatu_PDNA_Web.pdf"><span class="tdtext">Vanuatu</span></a></td>
                <td class="rtecenter"><span class="tdtext">2015</span></td>
                <td class="rtecenter"><span class="tdtext">Cyclone</span></td>
            </tr>
        </tbody>
        </table>
   </body>
</html>
"""

PDNA_PARAMS = {
    "country": "Nepal",
}

PDNA_MOCK_EXCEPTED_LEADS = [
    {
        "title": "Earthquake",
        "url": "https://www.gfdrr.org/sites/default/files/publication/Nepal%20Earthquake%202015%20Post-Disaster%20Needs%20Assessment%20Vol%20A.pdf",
        "source_raw": "PDNA portal",
        "author_raw": "PDNA portal",
        "published_on": datetime.date(2015, datetime.date.today().month, datetime.date.today().day),
        "source_type": Lead.SourceType.WEBSITE,
    }
]
