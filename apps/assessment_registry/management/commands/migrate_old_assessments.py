from ary.models import (
    Assessment,
    ScoreQuestionnaire,
    ScoreQuestionnaireSector,
    ScoreQuestionnaireSubSector,
)
from assessment_registry.models import (
    AdditionalDocument,
    Answer,
    AssessmentRegistry,
    AssessmentRegistryOrganization,
    MethodologyAttribute,
    Question,
    ScoreAnalyticalDensity,
    ScoreRating,
)
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import OuterRef, Subquery
from gallery.models import File
from geo.models import GeoArea, Region
from organization.models import Organization


def empty_str_to_none(value):
    if value == "":
        return None
    return value


def get_key(choice_model, label):
    if not label:
        return
    new_choices_list = [v.lower() for k, v in choice_model.choices]
    if label.lower() in new_choices_list:
        for key, value in choice_model.choices:
            if value == label:
                return key


def get_choice_field_key(metadata, value, choice_model):
    for schema in metadata:
        if isinstance(value, int):
            value = schema["schema"]["options"][value]
            return get_key(choice_model, value)
        elif schema["value"] == value:
            return get_key(choice_model, value)
        else:
            get_key(choice_model, value)


def save_countries(assessment_registry, metadata):
    countries = Region.objects.filter(id__in=metadata["Country"]["key"])
    if countries:
        for country in countries:
            assessment_registry.bg_countries.add(country)


def get_affected_groups_key(choice_model, label):
    choices = {k: v.split("/")[-1] for k, v in choice_model.choices}
    if not label:
        return
    for key, value in choices.items():
        if value.lower() == label.lower():
            return key
    return None


def create_stakeholders(organizations, assessment_reg, org_type):
    for org in organizations:
        AssessmentRegistryOrganization.objects.create(
            organization_type=org_type, assessment_registry=assessment_reg, organization=org
        )


def save_stakeholders(metadata_dict, assessment_registry):
    stakeholders_dict = {k: v for k, v in AssessmentRegistryOrganization.Type.choices}
    for org_type_key, org_type_value in stakeholders_dict.items():
        stakeholder_keys = [] if not metadata_dict[org_type_value]["key"] else metadata_dict[org_type_value]["key"]
        organizations = Organization.objects.filter(id__in=stakeholder_keys)
        if organizations:
            create_stakeholders(organizations, assessment_registry, org_type_key)


def save_locations(methodology_json, assessment_registry):
    if methodology_json.get("Locations"):
        locations = GeoArea.objects.filter(title__in=methodology_json.get("Locations"))
        if locations:
            for loc in locations:
                assessment_registry.locations.add(loc)


def save_methodology_attributes(methodology_json, assessment_registry):
    methodology_attributes = methodology_json.get("Attributes", None)
    if methodology_attributes:
        for attribute in methodology_attributes:
            MethodologyAttribute.objects.create(
                assessment_registry=assessment_registry,
                data_collection_technique=empty_str_to_none(attribute["Collection Technique"][0]["key"]),
                sampling_approach=empty_str_to_none(attribute["Sampling"][1]["key"]),
                sampling_size=empty_str_to_none(attribute["Sampling"][0]["key"]),
                proximity=empty_str_to_none(attribute["Proximity"][0]["key"]),
                unit_of_analysis=empty_str_to_none(attribute["Unit of Analysis"][0]["key"]),
                unit_of_reporting=empty_str_to_none(attribute["Unit of Reporting"][0]["key"]),
            )


def get_focus_data(methodology_json):
    def _get_focus_key(model_choice, label):
        if label == "Impact (scope & Scale)":
            return get_key(model_choice, AssessmentRegistry.FocusType.IMPACT.label)
        if label == "Information and communication":
            return get_key(model_choice, AssessmentRegistry.FocusType.INFORMATION_AND_COMMUNICATION.label)
        return get_key(model_choice, label)

    focus_data = [_get_focus_key(AssessmentRegistry.FocusType, value) for value in methodology_json.get("Focuses") or []]
    return list(filter(lambda x: x is not None, focus_data))


def get_sector_data(methodology_json):
    def _get_sector_key(model_choice, label):
        if label == "Food":
            return get_key(model_choice, AssessmentRegistry.SectorType.FOOD_SECURITY.label)
        if label == "WASH":
            return get_key(model_choice, AssessmentRegistry.SectorType.WASH.label)
        return get_key(model_choice, label)

    sector_data = [_get_sector_key(AssessmentRegistry.SectorType, value) for value in methodology_json.get("Sectors") or []]
    return list(filter(lambda x: x is not None, sector_data))


def create_additional_document(assessment_reg, old_file_type, old_file_id=None, external_link=None):
    file = File.objects.get(id=old_file_id) if old_file_id else None

    def _save_additional_doc(doc_type):
        AdditionalDocument.objects.create(
            document_type=doc_type, assessment_registry=assessment_reg, file=file, external_link=external_link or ""
        )

    if old_file_type == "assessment_data":
        _save_additional_doc(AdditionalDocument.DocumentType.ASSESSMENT_DATABASE)
    if old_file_type == "misc":
        _save_additional_doc(AdditionalDocument.DocumentType.MISCELLANEOUS)
    if old_file_type == "questionnaire":
        _save_additional_doc(AdditionalDocument.DocumentType.QUESTIONNAIRE)


def save_additional_documents(old_ary, assessment_registry):
    old_ary_additional_docs = (old_ary.metadata or {}).get("additional_documents")
    for k, v in old_ary_additional_docs.items():
        if v:
            for file in v:
                file_id = file.get("id", None)
                if file_id:
                    create_additional_document(
                        assessment_reg=assessment_registry,
                        old_file_type=k,
                        old_file_id=file["id"],
                    )
                else:
                    create_additional_document(assessment_reg=assessment_registry, old_file_type=k, external_link=file["url"])


def migrate_score_data(old_ary, assessment_reg):
    score_json = old_ary.get_score_json()
    analytical_density_data = (score_json.get("matrix_pillars"))["Analytical Density"]
    sector_value_dict = [(k, v["value"]) for k, v in analytical_density_data.items() if not v["value"] == ""]
    for sector, value in sector_value_dict:
        sector_key = get_key(AssessmentRegistry.SectorType, sector)
        if sector_key:
            ScoreAnalyticalDensity.objects.get_or_create(assessment_registry=assessment_reg, sector=sector_key, score=value * 2)

    score_rating_data = score_json.get("pillars")

    score_criteria_list = []
    for analytical_statement, score_criterias in score_rating_data.items():
        score_criteria_score = [(criteria, v["value"]) for criteria, v in score_criterias.items()]
        score_criteria_list.extend(score_criteria_score)

    for score_criteria, score_value in score_criteria_list:
        score_key = get_key(ScoreRating.ScoreCriteria, score_criteria)
        if score_key:
            ScoreRating.objects.get_or_create(
                assessment_registry=assessment_reg,
                score_type=get_key(ScoreRating.ScoreCriteria, score_criteria),
                rating=score_value,
            )


def migrate_cna_questions():
    cna_sectors = ScoreQuestionnaireSector.objects.filter(method="cna")
    cna_subsectors = ScoreQuestionnaireSubSector.objects.filter(sector__in=cna_sectors)
    cna_questions = ScoreQuestionnaire.objects.filter(sub_sector__in=cna_subsectors)

    for question in cna_questions:
        Question.objects.get_or_create(
            sub_sector=get_key(Question.QuestionSubSector, question.sub_sector.title),
            sector=get_key(Question.QuestionSector, question.sub_sector.sector.title),
            question=question.text,
        )


def migrate_cna_data(old_ary, new_assessment_registry):
    questionnaire = old_ary.questionnaire
    if questionnaire:
        questions = questionnaire.get("cna", None)
        if questions:
            cna = questions["questions"]
            for k, v in cna.items():
                if v:
                    old_q = ScoreQuestionnaire.objects.get(id=int(k))
                    ass_question = Question.objects.get(
                        question=old_q.text,
                        sector=get_key(Question.QuestionSector, old_q.sub_sector.sector.title),
                        sub_sector=get_key(Question.QuestionSubSector, old_q.sub_sector.title),
                    )
                    if ass_question:
                        Answer.objects.create(
                            question=ass_question, assessment_registry=new_assessment_registry, answer=v["value"]
                        )


def update_new_ary_created_update_date():
    AssessmentRegistry.objects.update(
        created_at=Subquery(Assessment.objects.filter(lead=OuterRef("lead")).values("created_at")),
        created_by=Subquery(Assessment.objects.filter(lead=OuterRef("lead")).values("created_by")),
        modified_at=Subquery(Assessment.objects.filter(lead=OuterRef("lead")).values("modified_at")),
        modified_by=Subquery(Assessment.objects.filter(lead=OuterRef("lead")).values("modified_by")),
    )


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        migrate_cna_questions()
        failed_ids = []
        for ary in Assessment.objects.all():
            try:
                self.map_old_to_new_data(ary.id)
            except Exception:
                failed_ids.append(ary.id)
        if not failed_ids == []:
            self.stdout.write(f"Failed to migrate data IDs: {failed_ids}")
        update_new_ary_created_update_date()

    @transaction.atomic
    def map_old_to_new_data(self, assessment_id):
        old_ary = Assessment.objects.get(id=assessment_id)
        if not old_ary:
            return
        self.stdout.write(f"Migrating data for assessment id {old_ary.id}")

        meta_data_json = old_ary.get_metadata_json()
        meta_data = (
            meta_data_json.get("Background")
            + meta_data_json.get("Details")
            + meta_data_json.get("Dates")
            + meta_data_json.get("Stakeholders")
        )
        metadata_dict = {}
        for d in meta_data:
            k = d["schema"]["name"]
            v = dict()
            v["value"] = d["value"]
            v["key"] = d["key"]
            metadata_dict[k] = v

        methodology_json = old_ary.get_methodology_json()

        # protection management
        old_protection_mgmt = methodology_json.get("Protection Info", None)
        new_protection_mgmt = []
        if old_protection_mgmt:
            for value in old_protection_mgmt:
                new_protection_mgmt.append(get_key(AssessmentRegistry.ProtectionInfoType, value))

        # Affected Groups
        old_affected_groups = methodology_json.get("Affected Groups", None)
        new_affected_groups = []
        if old_affected_groups:
            old_affected_groups_list = [aff_grp["title"] for aff_grp in old_affected_groups]
            for aff_grp in old_affected_groups_list:
                new_affected_groups.append(get_affected_groups_key(AssessmentRegistry.AffectedGroupType, aff_grp))

        def _get_bg_crisis_type():
            crisis_type = (
                get_choice_field_key(
                    meta_data_json.get("Background"), metadata_dict["Crisis Type"]["value"], AssessmentRegistry.CrisisType
                )
                if metadata_dict["Crisis Type"]["key"] == 14 or 11
                else metadata_dict["Crisis Type"]["key"]
            )

            return crisis_type

        input_data = {
            "project": old_ary.project,
            "lead": old_ary.lead,
            "bg_crisis_type": _get_bg_crisis_type(),
            "bg_crisis_start_date": metadata_dict["Crisis Start Date"]["value"],
            "bg_preparedness": metadata_dict["Preparedness"]["key"],
            "external_support": get_key(AssessmentRegistry.ExternalSupportType, metadata_dict["External Support"]["value"]),
            "coordinated_joint": metadata_dict["Coordination"]["key"],
            "cost_estimates_usd": metadata_dict["Cost estimates in USD"]["key"],
            "details_type": metadata_dict["Type"]["key"],
            "family": metadata_dict["Family"]["key"],
            "frequency": metadata_dict["Frequency"]["key"],
            "confidentiality": get_key(AssessmentRegistry.ConfidentialityType, metadata_dict["Confidentiality"]["value"]),
            "language": metadata_dict["Language"]["key"],
            "no_of_pages": metadata_dict["Number of Pages"]["key"],
            "data_collection_start_date": metadata_dict["Data Collection Start Date"]["value"],
            "data_collection_end_date": metadata_dict["Data Collection End Date"]["value"],
            "publication_date": metadata_dict["Publication Date"]["value"],
            "executive_summary": "",
            "focuses": get_focus_data(methodology_json) or [],
            "sectors": get_sector_data(methodology_json) or [],
            "protection_info_mgmts": new_protection_mgmt,
            "affected_groups": new_affected_groups,
            "sampling": methodology_json.get("Sampling", None),
            "objectives": methodology_json.get("Objectives", None),
            "limitations": methodology_json.get("Limitations", None),
            "data_collection_techniques": methodology_json.get("Data Collection Technique", None),
            "created_at": old_ary.created_at,
            "modified_at": old_ary.modified_at,
            "created_by": old_ary.created_by,
            "modified_by": old_ary.modified_by,
        }
        assessment_reg, created = AssessmentRegistry.objects.get_or_create(**input_data)

        if created:

            save_countries(assessment_reg, metadata_dict)

            save_stakeholders(metadata_dict, assessment_reg)

            save_locations(methodology_json, assessment_reg)

            save_methodology_attributes(methodology_json, assessment_reg)

            save_additional_documents(old_ary, assessment_reg)

            migrate_cna_data(old_ary, assessment_reg)

            migrate_score_data(old_ary, assessment_reg)

        self.stdout.write(f"Migrating data for assessment id {old_ary.id} Done")
