import datetime

from lead.models import Lead

HUMANITARIAN_RESPONSE_MOCK_DATA_RAW = """
<!DOCTYPE html>
<html lang="en" dir="ltr">
   <body class="html not-front not-logged-in one-sidebar sidebar-first page-documents page-documents-table i18n-en" >
        <div id="content" class="col-md-12">
            <table class="views-table cols-5 table table-striped table-bordered" >
                <thead>
                </thead>
                <tbody>
                    <tr class="odd views-row-first">
                        <td class="views-field views-field-title-field" >
                        <a href="/en/operations/democratic-republic-congo/document/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8Bcompte-rendu-%E2%80%93-avril-2021">​​​​​​​Compte rendu – avril 2021</a>
                        </td>
                        <td class="views-field views-field-field-document-type" >
                        Meeting Minutes
                        </td>
                        <td class="views-field views-field-field-organizations" >
                        Education Cluster - Democratic Republic of Congo
                        </td>
                        <td class="views-field views-field-field-publication-date active" >
                        <span class="date-display-single">04/28/2028</span>
                        </td>
                        <td class="views-field views-field-field-files-collection" >
                        <div class="btn-group">
                            <button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">
                            download <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a href="https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/compte_rendu_-_avril_2021.pdf">compte_rendu_-_avril_2021.pdf </a></li>
                            </ul>
                        </div>
                        </td>
                    </tr>
                    <tr class="even">
                        <td class="views-field views-field-title-field" >
                        <a href="/en/operations/democratic-republic-congo/document/compte-rendu-%E2%80%93-janvier-2021">Compte rendu – janvier 2021</a>
                        </td>
                        <td class="views-field views-field-field-document-type" >
                        Meeting Minutes
                        </td>
                        <td class="views-field views-field-field-organizations" >
                        Education Cluster - Democratic Republic of Congo
                        </td>
                        <td class="views-field views-field-field-publication-date active" >
                        <span class="date-display-single">01/27/2027</span>
                        </td>
                        <td class="views-field views-field-field-files-collection" >
                        <div class="btn-group">
                            <button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">
                            download <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a href="https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/compte_rendu_-_janvier_2021.pdf">compte_rendu_-_janvier_2021.pdf </a></li>
                            </ul>
                        </div>
                        </td>
                    </tr>
                    <tr class="odd">
                        <td class="views-field views-field-title-field" >
                        <a href="/en/operations/sudan/document/sudan-2022-humanitarian-response-plan-january-december-2022">Sudan 2022 Humanitarian Response Plan (January - December 2022)</a>
                        </td>
                        <td class="views-field views-field-field-document-type" >
                        Strategic Response Plan
                        </td>
                        <td class="views-field views-field-field-organizations" >
                        United Nations Office for the Coordination of Humanitarian Affairs
                        </td>
                        <td class="views-field views-field-field-publication-date active" >
                        <span class="date-display-single">12/20/2022</span>
                        </td>
                        <td class="views-field views-field-field-files-collection" >
                        <div class="btn-group">
                            <button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">
                            download <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a href="https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/2021-12_sudan_2022_humanitarian_response_plan_january_-_december_2022.pdf">2021-12_sudan_2022_humanitarian_response_plan_january_-_december_2022.pdf </a></li>
                                <li><a href="https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/2021-12_sudan_2022_humanitarian_response_plan_january_-_december_2022_ar.pdf">2021-12_sudan_2022_humanitarian_response_plan_january_-_december_2022_ar.pdf </a></li>
                            </ul>
                        </div>
                        </td>
                    </tr>
                    <tr class="even">
                        <td class="views-field views-field-title-field" >
                        <a href="/en/operations/somalia/document/10272021baysouth-west-wash-cluster-meeting-minutes">10_27_2021_Bay_South-West WASH Cluster Meeting Minutes</a>
                        </td>
                        <td class="views-field views-field-field-document-type" >
                        Meeting Minutes
                        </td>
                        <td class="views-field views-field-field-organizations" >
                        WASH Cluster - Somalia
                        </td>
                        <td class="views-field views-field-field-publication-date active" >
                        <span class="date-display-single">10/27/2022</span>
                        </td>
                        <td class="views-field views-field-field-files-collection" >
                        <div class="btn-group">
                            <button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">
                            download <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a href="https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/10_27_2021_bay_south-west_wash_cluster_meeting_minutes.pdf">10_27_2021_bay_south-west_wash_cluster_meeting_minutes.pdf </a></li>
                            </ul>
                        </div>
                        </td>
                    </tr>
                    <tr class="odd">
                        <td class="views-field views-field-title-field" >
                        <a href="/en/operations/stima/document/nws-aawg-flood-rna-2021">NWS AAWG - Flood RNA - 2021</a>
                        </td>
                        <td class="views-field views-field-field-document-type" >
                        Tool
                        </td>
                        <td class="views-field views-field-field-organizations" >
                        United Nations Office for the Coordination of Humanitarian Affairs
                        </td>
                        <td class="views-field views-field-field-publication-date active" >
                        <span class="date-display-single">10/15/2022</span></td>
                        <td class="views-field views-field-field-files-collection" >
                        <div class="btn-group">
                            <button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">
                            download <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a href="https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/flood_rna.zip">flood_rna.zip </a></li>
                            </ul>
                        </div>
                        </td>
                    </tr>
                    <tr class="even">
                        <td class="views-field views-field-title-field" >
                        <a href="/en/operations/cameroon/document/cameroon-chapeau-information-sharing-protocols-data-responsibility">Cameroon: Chapeau - Information Sharing Protocols for Data Responsibility, September 2021</a>
                        </td>
                        <td class="views-field views-field-field-document-type" >
                        Standard Operating Procedures
                        </td>
                        <td class="views-field views-field-field-organizations" >
                        United Nations Office for the Coordination of Humanitarian Affairs
                        </td>
                        <td class="views-field views-field-field-publication-date active" >
                        <span class="date-display-single">10/03/2022</span>
                        </td>
                        <td class="views-field views-field-field-files-collection" >
                        <div class="btn-group">
                            <button type="button" class="btn btn-primary btn-sm dropdown-toggle" data-toggle="dropdown">
                            download <span class="caret"></span>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a href="https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/chapeau_isp_-_cameroon_sept_2021_v2.pdf">chapeau_isp_-_cameroon_sept_2021_v2.pdf </a></li>
                            </ul>
                        </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
   </body>
</html>
"""

HUMANITARIAN_RESPONSE_MOCK_EXCEPTED_LEADS = [
    {
        "id": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/compte_rendu_-_avril_2021.pdf",
        "title": "Compte rendu – avril 2021",
        "published_on": datetime.date(2028, 4, 28),
        "url": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/compte_rendu_-_avril_2021.pdf",
        "source_raw": "Humanitarian Response",
        "author_raw": "Humanitarian Response",
        "source_type": Lead.SourceType.WEBSITE,
    },
    {
        "id": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/compte_rendu_-_janvier_2021.pdf",
        "title": "Compte rendu – janvier 2021",
        "published_on": datetime.date(2027, 1, 27),
        "url": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/compte_rendu_-_janvier_2021.pdf",
        "source_raw": "Humanitarian Response",
        "author_raw": "Humanitarian Response",
        "source_type": Lead.SourceType.WEBSITE,
    },
    {
        "id": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/2021-12_sudan_2022_humanitarian_response_plan_january_-_december_2022.pdf",
        "title": "Sudan 2022 Humanitarian Response Plan (January - December 2022)",
        "published_on": datetime.date(2022, 12, 20),
        "url": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/2021-12_sudan_2022_humanitarian_response_plan_january_-_december_2022.pdf",
        "source_raw": "Humanitarian Response",
        "author_raw": "Humanitarian Response",
        "source_type": Lead.SourceType.WEBSITE,
    },
    {
        "id": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/10_27_2021_bay_south-west_wash_cluster_meeting_minutes.pdf",
        "title": "10_27_2021_Bay_South-West WASH Cluster Meeting Minutes",
        "published_on": datetime.date(2022, 10, 27),
        "url": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/10_27_2021_bay_south-west_wash_cluster_meeting_minutes.pdf",
        "source_raw": "Humanitarian Response",
        "author_raw": "Humanitarian Response",
        "source_type": Lead.SourceType.WEBSITE,
    },
    {
        "id": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/flood_rna.zip",
        "title": "NWS AAWG - Flood RNA - 2021",
        "published_on": datetime.date(2022, 10, 15),
        "url": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/flood_rna.zip",
        "source_raw": "Humanitarian Response",
        "author_raw": "Humanitarian Response",
        "source_type": Lead.SourceType.WEBSITE,
    },
    {
        "id": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/chapeau_isp_-_cameroon_sept_2021_v2.pdf",
        "title": "Cameroon: Chapeau - Information Sharing Protocols for Data Responsibility, September 2021",
        "published_on": datetime.date(2022, 10, 3),
        "url": "https://www.humanitarianresponse.info/sites/www.humanitarianresponse.info/files/documents/files/chapeau_isp_-_cameroon_sept_2021_v2.pdf",
        "source_raw": "Humanitarian Response",
        "author_raw": "Humanitarian Response",
        "source_type": Lead.SourceType.WEBSITE,
    },
]
