from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from user_resource.models import UserResource
from geo.models import Region
from organization.models import Organization
from gallery.models import File
from lead.models import Lead
from geo.models import GeoArea


class AssessmentRegistry(UserResource):
    class CrisisType(models.IntegerChoices):
        EARTH_QUAKE = 0, 'Earth Quake'
        GROUND_SHAKING = 1, 'Ground Shaking'
        TSUNAMI = 2, 'Tsunami'
        VOLCANO = 3, 'Volcano'
        VOLCANIC_ERUPTION = 4, 'Volcanic Eruption'
        MASS_MOMENT_DRY = 5, 'Mass Movement (Dry)'
        ROCK_FALL = 6, 'Rockfall'
        AVALANCE = 7, 'Avalance'
        LANDSLIDE = 8, 'Landslide'
        SUBSIDENCE = 9, 'Subsidence'
        EXTRA_TROPICAL_CYCLONE = 10, 'Extra Tropical Cyclone'
        TROPICAL_CYCLONE = 11, 'Tropical Cyclone'
        LOCAL_STROM = 12, 'Local/Convective Strom'
        FLOOD_RAIN = 13, 'Flood/Rain'
        GENERAL_RIVER_FLOOD = 14, 'General River Flood'
        FLASH_FLOOD = 15, 'Flash flood'
        STROM_SURGE_FLOOD = 16, 'Strom Surge/Coastal Flood'
        MASS_MOVEMENT_WET = 17, 'Mass Movement (Wet)'
        EXTREME_TEMPERATURE = 18, 'Extreme Temperature'
        HEAT_WAVE = 19, 'Heat Wave'
        COLD_WAVE = 20, 'Cold Wave'
        EXTREME_WEATHER_CONDITION = 21, 'Extreme Weather Condition'
        DROUGHT = 22, 'Drought'
        WILDFIRE = 23, 'Wildfire'
        POPULATION_DISPLACEMENT = 24, 'Population Displacement'
        CONFLICT = 25, 'Conflict'

    class PreparednessType(models.IntegerChoices):
        WITH_PREPAREDNESS = 1, 'With Preparedness'
        WITHOUT_PREPAREDNESS = 2, 'Without Preparedness'

    class ExternalSupportType(models.IntegerChoices):
        EXTERNAL_SUPPORT_RECIEVED = 1, 'External Support Received'
        NO_EXTERNAL_SUPPORT_RECEIVED = 2, 'No External Support Received'

    class CoordinationType(models.IntegerChoices):
        COORDINATED = 1, 'Coordinated Joint'
        HARMONIZED = 2, 'Coordinated Harmonized'
        UNCOORDINATED = 3, 'Uncoordinated'

    class Type(models.IntegerChoices):
        INITIAL = 1, 'Initial'
        RAPID = 2, 'Rapid'
        IN_DEPTH = 3, 'In depth'
        MONITORING = 4, 'Monitoring'
        OTHER = 5, 'Other'

    class FamilyType(models.IntegerChoices):
        DISPLACEMENT_TRAKING_MATRIX = 1, 'Displacement Traking Matrix'
        MULTI_CLUSTER_INITIAL_AND_RAPID_ASSESSMENT = 2, 'Multi Cluster Initial and Rapid Assessment (MIRA)'
        MULTI_SECTORIAL_NEEDS_ASSESSMENT = 3, 'Multi sectorial Needs Assessment (MSNA)'
        EMERGENCY_FOOD_SECURITY_ASSESSMENT = 4, 'Emergency Food Security Assessment (EFSA)'
        COMPREHENSIVE_FOOD_SECURITY_AND_VULNERABILITY_ANALYSIS = \
            5, 'Comprehensive Food Security and Vulnerability Analysis(CFSVA)'
        PROTECTION_MONITORING = 6, 'Protection Monitoring'
        HUMANITARIAN_NEEDS_OVERVIEW = 7, 'Humanitarian Needs Overview (HNO)'
        BRIEFING_NOTE = 8, 'Briefing note'
        REGISTRATION = 9, 'Registration'
        IDP_PROFILING_EXERCISE = 10, 'IDPs profiling exercise'
        CENSUS = 11, 'Census'
        REFUGEE_AND_MIGRANT_RESPONSE_PLAN = 12, 'Refugee and Migrant Response Plan (RMRP)'
        RUFUGEE_RESPONSE_PLAN = 13, 'Refugee Response Plan (RRP)'
        SMART_NUTRITION_SURVEY = 14, 'Smart Nutrition Survey'
        OTHER = 15, 'Other'

    class FrequencyType(models.IntegerChoices):
        ONE_OFF = 1, 'One off'
        REGULAR = 2, 'Regular'

    class ConfidentialityType(models.IntegerChoices):
        UNPROTECTED = 1, 'Unprotected'
        CONFIDENTIAL = 2, 'Confidential'

    class Language(models.IntegerChoices):
        ENGLISH = 1, 'English'
        FRENCH = 2, 'French'
        SPANISH = 3, 'Spanish'
        PORTUGESE = 4, 'Portugese'
        ARABIC = 5, 'Arabic'

    class FocusType(models.IntegerChoices):
        CONTEXT = 1, 'Context'
        SHOCK_EVENT = 2, 'Shock/Event'
        DISPLACEMENT = 3, 'Displacement'
        CASUALTIES = 4, 'Casualties'
        INFORMATION_AND_COMMUNICATION = 5, 'Information and Communication'
        HUMANITERIAN_ACCESS = 6, 'Humaniterian Access'
        IMPACT = 7, 'Impact'
        HUMANITARIAN_CONDITIONS = 8, 'Humanitarian Conditions'
        PEOPLE_AT_RISK = 9, 'People at risk'
        PRIORITIES_AND_PREFERENCES = 10, 'Priorities & Preferences'
        RESPONSE_AND_CAPACITIES = 11, 'Response and Capacities'

    class SectorType(models.IntegerChoices):
        FOOD_SECURITY = 1, 'Food Security'
        HEALTH = 2, 'Heath'
        SHELTER = 3, 'Shelter'
        WASH = 4, 'Wash'
        PROTECTION = 5, 'Protection'
        NUTRITION = 6, 'Nutrition'
        LIVELIHOOD = 7, 'Livelihood'
        EDUCATION = 8, 'Education'
        LOGISTICS = 9, 'Logistics'
        INTER_CROSS_SECTOR = 10, 'Inter/Cross Sector'

    class ProtectionInfoType(models.IntegerChoices):
        PROTECTION_MONITORING = 1, 'Protection Monitoring'
        PROTECTION_NEEDS_ASSESSMENT = 2, 'Protection Needs Assessment'
        CASE_MANAGEMENT = 3, 'Case Management'
        POPULATION_DATA = 4, 'Population Data'
        PROTECTION_RESPONSE_M_E = 5, 'Protection Response M&E'
        COMMUNICATING_WITH_IN_AFFECTED_COMMUNITIES = 6, 'Communicating with(in) Affected Communities'
        SECURITY_AND_SITUATIONAL_AWARENESS = 7, 'Security & Situational Awareness'
        SECTORAL_SYSTEM_OTHER = 8, 'Sectoral System/Other'

    class AffectedGroupType(models.IntegerChoices):
        ALL = 1, 'All'
        ALL_AFFECTED = 2, 'All/Affected'
        ALL_NOT_AFFECTED = 3, 'All/Not Affected'
        ALL_AFFECTED_NOT_DISPLACED = 4, 'All/Affected/Not Displaced'
        ALL_AFFECTED_DISPLACED = 5, 'All/Affected/Displaced'
        ALL_AFFECTED_DISPLACED_IN_TRANSIT = 6, 'All/Affected/Displaced/In Transit'
        ALL_AFFECTED_DISPLACED_MIGRANTS = 7, 'All/Affected/Displaced/Migrants'
        ALL_AFFECTED_DISPLACED_IDPS = 8, 'All/Affected/Displaced/IDPs'
        ALL_AFFECTED_DISPLACED_ASYLUM_SEEKER = 9, 'All/Affected/Displced/Asylum Seeker'
        ALL_AFFECTED_DISPLACED_OTHER_OF_CONCERN = 10, 'All/Affected/Displaced/Other of concerns'
        ALL_AFFECTED_DISPLACED_RETURNEES = 11, 'All/Affected/Displaced/Returnees'
        ALL_AFFECTED_DISPLACED_REFUGEES = 12, 'All/Affected/Displaced/Refugees'
        ALL_AFFECTED_DISPLACED_MIGRANTS_IN_TRANSIT = 13, 'All/Affected/Displaced/Migrants/In transit'
        ALL_AFFECTED_DISPLACED_MIGRANTS_PERMANENTS = 14, 'All/Affected/Displaced/Migrants/Permanents'
        ALL_AFFECTED_DISPLACED_MIGRANTS_PENDULAR = 15, 'All/Affected/Displaced/Migrants/Pendular'
        ALL_AFFECTED_NOT_DISPLACED_NO_HOST = 16, 'All/Affected/Not Displaced/No Host'
        ALL_AFFECTED_NOT_DISPLACED_HOST = 17, 'All/Affected/Not Displaced/Host'

    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    lead = models.OneToOneField(
        Lead, on_delete=models.CASCADE,
    )

    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    lead = models.OneToOneField(
        Lead, default=None, blank=True, null=True, on_delete=models.CASCADE,
    )
    lead_group = models.OneToOneField(
        LeadGroup, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )

    # Metadata Group
    # -- Background Fields
    bg_countries = models.ManyToManyField(Region)
    bg_crisis_type = models.IntegerField(choices=CrisisType.choices)
    bg_crisis_start_date = models.DateField()
    bg_preparedness = models.IntegerField(choices=PreparednessType.choices)
    external_support = models.IntegerField(choices=ExternalSupportType.choices)
    coordinated_joint = models.IntegerField(choices=CoordinationType.choices)
    cost_estimates_usd = models.IntegerField(null=True, blank=True)

    # -- Details Field
    details_type = models.IntegerField(choices=Type.choices)
    family = models.IntegerField(choices=FamilyType.choices)
    frequency = models.IntegerField(choices=FrequencyType.choices)
    confidentiality = models.IntegerField(choices=ConfidentialityType.choices)
    language = ArrayField(models.IntegerField(choices=Language.choices))
    no_of_pages = models.IntegerField(null=True, blank=True)

    # -- Dates
    data_collection_start_date = models.DateField(null=True, blank=True)
    data_collection_end_date = models.DateField(null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)

    # -- Stakeholders
    stakeholders = models.ManyToManyField(
        Organization,
        through='AssessmentRegistryOrganization',
        through_fields=('assessment_registry', 'organization'),
        blank=True,
    )

    # Additional Documents
    executive_summary = models.TextField(blank=True)

    # Methodology
    objectives = models.TextField(blank=True, null=True)
    data_collection_techniques = models.TextField(blank=True, null=True)
    sampling = models.TextField(blank=True, null=True)
    limitations = models.TextField(blank=True, null=True)

    # Focus
    # -- Focus Sectors
    focuses = ArrayField(models.IntegerField(choices=FocusType.choices), default=list)
    sectors = ArrayField(models.IntegerField(choices=SectorType.choices), default=list)
    protection_info_mgmts = ArrayField(
        models.IntegerField(choices=ProtectionInfoType.choices),
        default=list, blank=True
    )
    affected_groups = ArrayField(
        models.IntegerField(choices=AffectedGroupType.choices),
        default=list
    )

    locations = models.ManyToManyField(GeoArea, related_name='focus_location_assessment_reg', blank=True)
    metadata_complete = models.BooleanField(default=False)
    additional_document_complete = models.BooleanField(default=False)
    focus_complete = models.BooleanField(default=False)
    methodology_complete = models.BooleanField(default=False)
    summary_complete = models.BooleanField(default=False)
    cna_complete = models.BooleanField(default=False)
    score_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.lead.title

    def can_delete(self, user):
        return self.project.is_member(user)


class AssessmentRegistryOrganization(models.Model):
    class Type(models.IntegerChoices):
        LEAD_ORGANIZATION = 1, 'Lead Organization'  # Project Owner
        INTERNATIONAL_PARTNER = 2, 'International Partner'
        NATIONAL_PARTNER = 3, 'National Partner'
        DONOR = 4, 'Donor'
        GOVERNMENT = 5, 'Government'

    organization_type = models.IntegerField(choices=Type.choices)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    assessment_registry = models.ForeignKey(AssessmentRegistry, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('assessment_registry', 'organization_type', 'organization')


class MethodologyAttribute(UserResource):
    class CollectionTechniqueType(models.IntegerChoices):
        SECONDARY_DATA_REVIEW = 1, 'Secondary Data Review'
        KEY_INFORMAT_INTERVIEW = 2, 'Key Informant Interview'
        DIRECT_OBSERVATION = 3, 'Direct Observation'
        COMMUNITY_GROUP_DISCUSSION = 4, 'Community Group Discussion'
        FOCUS_GROUP_DISCUSSION = 5, 'Focus Group Discussion'
        HOUSEHOLD_INTERVIEW = 6, 'Household Interview'
        INDIVIDUAL_INTERVIEW = 7, 'Individual Interview'
        SATELLITE_IMAGERY = 8, 'Satellite Imagery'

    class SamplingApproachType(models.IntegerChoices):
        NON_RANDOM_SELECTION = 1, 'Non-Random Selection'
        RANDOM_SELECTION = 2, 'Random Selection'
        FULL_ENUMERATION = 3, 'Full Enumeration'

    class ProximityType(models.IntegerChoices):
        FACE_TO_FACE = 1, 'Face-to-Face'
        REMOTE = 2, 'Remote'
        MIXED = 3, 'Mixed'

    class UnitOfAnalysisType(models.IntegerChoices):
        CRISIS = 1, 'Crisis'
        COUNTRY = 2, 'Country'
        REGION = 3, 'Region'
        PROVINCE_GOV_PREFECTURE = 4, 'Province/governorate/prefecture'
        DEPARTMENT_DISTRICT = 5, 'Department/District'
        SUB_DISTRICT_COUNTRY = 6, 'Sub-District/Country'
        MUNICIPALITY = 7, 'Municipality'
        NEIGHBORHOOD_QUARTIER = 8, 'Neighborhood/Quartier'
        COMMUNITY_SITE = 9, 'Community/Site'
        AFFECTED_GROUP = 10, 'Affected group'
        HOUSEHOLD = 11, 'Household'
        INDIVIDUAL = 12, 'Individual'

    class UnitOfReportingType(models.IntegerChoices):
        CRISIS = 1, 'Crisis'
        COUNTRY = 2, 'Country'
        REGION = 3, 'Region'
        PROVINCE_GOV_PREFECTURE = 4, 'Province/governorate/prefecture'
        DEPARTMENT_DISTRICT = 5, 'Department/District'
        SUB_DISTRICT_COUNTRY = 6, 'Sub-District/Country'
        MUNICIPALITY = 7, 'Municipality'
        NEIGHBORHOOD_QUARTIER = 8, 'Neighborhood/Quartier'
        COMMUNITY_SITE = 9, 'Community/Site'
        AFFECTED_GROUP = 10, 'Affected group'
        HOUSEHOLD = 11, 'Household'
        INDIVIDUAL = 12, 'Individual'

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='methodology_attributes',
    )
    data_collection_technique = models.IntegerField(choices=CollectionTechniqueType.choices, null=True, blank=True)
    sampling_approach = models.IntegerField(choices=SamplingApproachType.choices, null=True, blank=True)
    sampling_size = models.IntegerField(blank=True, null=True)
    proximity = models.IntegerField(choices=ProximityType.choices, null=True, blank=True)
    unit_of_analysis = models.IntegerField(choices=UnitOfAnalysisType.choices, null=True, blank=True)
    unit_of_reporting = models.IntegerField(choices=UnitOfReportingType.choices, null=True, blank=True)


class AdditionalDocument(UserResource):
    class DocumentType(models.IntegerChoices):
        ASSESSMENT_DATABASE = 1, 'Assessment database'
        QUESTIONNAIRE = 2, 'Questionnaire'
        MISCELLANEOUS = 3, 'Miscellaneous'

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='additional_documents',
    )
    document_type = models.IntegerField(choices=DocumentType.choices)
    file = models.ForeignKey(
        File,
        on_delete=models.SET_NULL,
        related_name='assessment_reg_file',
        null=True, blank=True
    )
    external_link = models.URLField(max_length=500, blank=True)

    def __str__(self):
        return f'FileID: {self.file_id}'


class ScoreRating(UserResource):
    class AnalyticalStatement(models.IntegerChoices):
        FIT_FOR_PURPOSE = 1, 'Fit for purpose'
        TRUSTWORTHINESS = 2, 'Trustworthiness'
        ANALYTICAL_RIGOR = 3, 'Analytical Rigor'
        ANALYTICAL_WRITING = 4, 'Analytical Writing'

    class ScoreCriteria(models.IntegerChoices):
        RELEVANCE = 1, "Relevance"
        COMPREHENSIVENESS = 2, "Comprehensiveness"
        TIMELINESS = 3, "Timeliness"
        GRANULARITY = 4, "Granularity"
        COMPARABILITY = 5, "Comparability"
        SOURCE_REABILITY = 6, "Source reability"
        METHODS = 7, "Methods"
        TRIANGULATION = 8, "Triangulation"
        PLAUSIBILITY = 9, "Plausibility"
        INCLUSIVENESS = 10, "Inclusiveness"
        ASSUMPTIONS = 11, "Assumptions"
        CORROBORATION = 12, "Corroboration"
        STRUCTURED_ANALYTICAL_TECHNIQUE = 13, "Structured Ananlytical Technique"
        CONSENSUS = 14, "Consensus"
        REPRODUCIBILITY = 15, "Reproducibility"
        CLEARLY_ARTICULATED_RESULT = 16, "Clearly Articulated Result"
        LEVEL_OF_CONFIDENCE = 17, "Level Of Confidence"
        ILLUSTRATION = 18, "Illustration"
        SOURCED_DATA_EVIDENCE = 19, "Sourced data and evidence"
        CLEARLY_STATED_OUTLIERS = 20, "Clearly stated outliers"

    class RatingType(models.IntegerChoices):
        VERY_POOR = 1, "Very poor"
        POOR = 2, "Poor"
        FAIR = 3, "Fair"
        GOOD = 4, "Good"
        VERY_GOOD = 5, "Very Good"

    ANALYTICAL_STATEMENT_SCORE_CRITERIA_MAP = {
        AnalyticalStatement.FIT_FOR_PURPOSE: [
            ScoreCriteria.RELEVANCE,
            ScoreCriteria.COMPREHENSIVENESS,
            ScoreCriteria.TIMELINESS,
            ScoreCriteria.GRANULARITY,
            ScoreCriteria.COMPARABILITY,
        ],
        AnalyticalStatement.TRUSTWORTHINESS: [
            ScoreCriteria.SOURCE_REABILITY,
            ScoreCriteria.METHODS,
            ScoreCriteria.TRIANGULATION,
            ScoreCriteria.PLAUSIBILITY,
            ScoreCriteria.INCLUSIVENESS,
        ],
        AnalyticalStatement.ANALYTICAL_RIGOR: [
            ScoreCriteria.ASSUMPTIONS,
            ScoreCriteria.CORROBORATION,
            ScoreCriteria.STRUCTURED_ANALYTICAL_TECHNIQUE,
            ScoreCriteria.CONSENSUS,
            ScoreCriteria.REPRODUCIBILITY,
        ],
        AnalyticalStatement.ANALYTICAL_WRITING: [
            ScoreCriteria.CLEARLY_ARTICULATED_RESULT,
            ScoreCriteria.LEVEL_OF_CONFIDENCE,
            ScoreCriteria.ILLUSTRATION,
            ScoreCriteria.SOURCED_DATA_EVIDENCE,
            ScoreCriteria.CLEARLY_STATED_OUTLIERS,
        ],
    }

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='score_ratings',
    )
    score_type = models.IntegerField(choices=ScoreCriteria.choices)
    rating = models.IntegerField(choices=RatingType.choices, default=RatingType.FAIR)
    reason = models.TextField(blank=True, null=True)


class ScoreAnalyticalDensity(UserResource):
    class AnalysisLevelCovered(models.IntegerChoices):
        ISSUE_UNMET_NEEDS_ARE_DETAILED = 1, 'Issues/unmet needs are detailed'
        ISSUE_UNMET_NEEDS_ARE_PRIORITIZED_RANKED = 2, 'Issues/unmet needs are prioritized/ranked'
        CAUSES_OR_UNDERLYING_MECHANISMS_BEHIND_ISSUES_UNMET_NEEDS_ARE_DETAILED = 3, \
            'Causes or underlying mechanisms behind issues/unmet needs are detailed'
        CAUSES_OR_UNDERLYING_MECHANISMS_BEHIND_ISSUES_UNMET_NEEDS_ARE_PRIORITIZED_RANKED = 4, \
            'Causes or underlying mechanisms behind issues/unmet needs are prioritized/ranked'
        SEVERITY_OF_SOME_ALL_ISSUE_UNMET_NEEDS_IS_DETAILED = 5, \
            'Severity of some/all issues/unmet_needs_is_detailed'
        FUTURE_ISSUES_UNMET_NEEDS_ARE_DETAILED = 6, 'Future issues/unmet needs are detailed'
        FUTURE_ISSUES_UNMET_NEEDS_ARE_PRIORITIZED_RANKED = 7, 'Future issues/unmet needs are prioritized/ranked'
        SEVERITY_OF_SOME_ALL_FUTURE_ISSUE_UNMET_NEEDS_IS_DETAILED = 8, \
            'Severity of some/all future issues/unmet_needs_is_detailed'
        RECOMMENDATIONS_INTERVENTIONS_ARE_DETAILED = 9, 'Recommendations/interventions are detailed'
        RECOMMENDATIONS_INTERVENTIONS_ARE_PRIORITIZED_RANKED = 10, \
            'Recommendations/interventions are prioritized/ranked'

    class FigureProvidedByAssessment(models.IntegerChoices):
        TOTAL_POP_IN_THE_ASSESSED_AREAS = 1, 'Total population in the assessed areas'
        TOTAL_POP_EXPOSED_TO_THE_SHOCK_EVENT = 2, 'Total population exposed to the shock/event'
        TOTAL_POP_AFFECTED_LIVING_IN_THE_AFFECTED_AREAS = 3, \
            'Total population affected/living in the affected area'
        TOTAL_POP_FACING_HUMANITARIAN_ACCESS_CONSTRAINTS = 4, 'Total population facing humanitarian access constraints'
        TOTAL_POP_IN_NEED = 5, 'Total population in need'
        TOTAL_POP_IN_CRITICAL_NEED = 6, 'Total population in critical need'
        TOTAL_POP_IN_SEVERE_NEED = 7, 'Total population in severe need'
        TOTAL_POP_IN_MODERATE_NEED = 8, 'Total population in moderate need'
        TOTAL_POP_AT_RISK_VULNERABLE = 9, 'Total population at risk/vulnerable'
        TOTAL_POP_REACHED_BY_ASSISTANCE = 10, 'Total population reached by assistance'

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='analytical_density'
    )
    sector = models.IntegerField(choices=AssessmentRegistry.SectorType.choices)
    analysis_level_covered = ArrayField(models.IntegerField(choices=AnalysisLevelCovered.choices), default=list)
    figure_provided = ArrayField(models.IntegerField(choices=FigureProvidedByAssessment.choices), default=list)


class Question(UserResource):
    class QuestionSector(models.IntegerChoices):
        RELEVANCE = 1, 'Relevance'
        COMPREHENSIVENESS = 2, 'Comprehensiveness'
        ETHICS = 3, 'Ethics'
        METHODOLOGICAL_RIGOR = 4, 'Methodological rigor'
        ANALYTICAL_VALUE = 5, 'Analytical value'
        TIMELINESS = 6, 'Timeliness'
        EFFECTIVE_COMMUNICATION = 7, 'Effective Communication'
        USE = 8, 'Use',
        PEOPLE_CENTERED_AND_INCLUSIVE = 9, 'People-centered and inclusive'
        ACCOUNTABILITY_TO_AFFECTED_POPULATIONS = 10, 'Accountability to affected populations'
        DO_NOT_HARM = 11, 'Do not harm'
        DESIGNED_WITH_PURPOSE = 12, 'Designed with a purpose'
        COMPETENCY_AND_CAPACITY = 13, 'Competency and capacity'
        IMPARTIALITY = 14, 'Impartiality'
        COORDINATION_AND_DATA_MINIMIZATION = 15, 'Coordination and data minimization'
        JOINT_ANALYSIS = 16, 'Joint Analysis'
        ACKNOWLEDGE_DISSENTING_VOICES_IN_JOINT_NEEDS_ANALYSIS = 17, 'Acknowledge dissenting voices in joint needs analysis'
        IFORMED_CONSENT_CONFIDENTIALITY_AND_DATA_SECURITY = 18, 'Informed consent, confidentiality and data security'
        SHARING_RESULTS = 19, 'Sharing results (data and analysis)'
        TRANSPARENCY_BETWEEN_ACTORS = 20, 'Tranparency between actors'
        MINIMUM_TECHNICAL_STANDARDS = 21, 'Minimum technical standards'

    class QuestionSubSector(models.IntegerChoices):
        RELEVANCE = 1, 'Relevance'
        GEOGRAPHIC_COMPREHENSIVENESS = 2, 'Geographic comprehensiveness'
        SECTORAL_COMPREHENSIVENESS = 3, 'Sectoral comprehensiveness'
        AFFECTED_AND_VULNERABLE_GROUPS_COMPREHENSIVENESS = 4, 'Affected and vulnerabel groups comprehensiveness'
        SAFETY_AND_PROTECTION = 5, 'Safety and protection'
        HUMANITARIAN_PRINCIPLES = 6, 'Humanitarian Principles'
        CONTRIBUTION = 7, 'Contribution'
        TRANSPARENCY = 8, 'Transparency'
        MITIGATING_BIAS = 9, 'Mitigating Bias'
        PARTICIPATION = 10, 'Participation'
        CONTEXT_SPECIFICITY = 11, 'Context specificity'
        ANALYTICAL_STANDARDS = 12, 'Ananlytical standards'
        DESCRIPTIONS = 13, 'Descriptions'
        EXPLANATION = 14, 'Explanation'
        INTERPRETATION = 15, 'Interpretation'
        ANTICIPATION = 16, 'Anticipation'
        TIMELINESS = 17, 'Timeliness'
        USER_FRIENDLY_PRESENTATION = 18, 'User-friendly presentation'
        ACTIVE_DISSEMINATION = 19, 'Active dissemination'
        USE_FOR_COLLECTIVE_PLANNING = 20, 'Use for collective planning'
        BUY_IN_AND_USE_BY_HUMANITARIAN_CLUSTERS_SECTORS = 21, 'Buy-in and use by humanitarian clusters/sectors'
        BUY_IN_AND_USE_BY_UN_AGENCIES = 22, 'Buy-in and use by UN agencies'
        BUY_IN_AND_USE_BY_INTERNATIONAL_NGO = 23, 'Buy-in and use by international non-governmental organizations (NGOs)'
        BUY_IN_AND_USE_BY_LOCAL_NGO = 24, 'Buy-in and use by local non-governmental organization (local NGOs)'
        BUY_IN_AND_USE_BY_MEMBER_OF_RED_CROSS_RED_CRESENT_MOVEMENT = 25, \
            'Buy-in and use by member of Red Cross/Red Cresent Movement'
        BUY_IN_AND_USE_BY_DONORS = 26, 'Buy-in and use by donors'
        BUY_IN_AND_USE_BY_NATIONAL_AND_LOCAL_GOVERNMENT_AGENCIES = 27, \
            'Buy-in and use by naional and local government agencies'
        BUY_IN_AND_USE_BY_DEVELOPMENT_AND_STABILIZATION_ACTORS = 28, 'Buy-in and use by development and stabilization actors'

    QUESTION_SECTOR_SUB_SECTOR_MAP = {
        QuestionSector.RELEVANCE: [
            QuestionSubSector.RELEVANCE,
        ],
        QuestionSector.COMPREHENSIVENESS: [
            QuestionSubSector.GEOGRAPHIC_COMPREHENSIVENESS,
            QuestionSubSector.SECTORAL_COMPREHENSIVENESS,
            QuestionSubSector.AFFECTED_AND_VULNERABLE_GROUPS_COMPREHENSIVENESS,
        ],
        QuestionSector.ETHICS: [
            QuestionSubSector.SAFETY_AND_PROTECTION,
            QuestionSubSector.HUMANITARIAN_PRINCIPLES,
            QuestionSubSector.CONTRIBUTION,
        ],
        QuestionSector.METHODOLOGICAL_RIGOR: [
            QuestionSubSector.TRANSPARENCY,
            QuestionSubSector.MITIGATING_BIAS,
            QuestionSubSector.PARTICIPATION,
            QuestionSubSector.CONTEXT_SPECIFICITY,
        ],
        QuestionSector.ANALYTICAL_VALUE: [
            QuestionSubSector.ANALYTICAL_STANDARDS,
            QuestionSubSector.DESCRIPTIONS,
            QuestionSubSector.EXPLANATION,
            QuestionSubSector.INTERPRETATION,
            QuestionSubSector.ANTICIPATION,
            QuestionSubSector.TIMELINESS,
        ],
        QuestionSector.EFFECTIVE_COMMUNICATION: [
            QuestionSubSector.USER_FRIENDLY_PRESENTATION,
            QuestionSubSector.ACTIVE_DISSEMINATION,
        ],
        QuestionSector.USE: [
            QuestionSubSector.USE_FOR_COLLECTIVE_PLANNING,
            QuestionSubSector.BUY_IN_AND_USE_BY_HUMANITARIAN_CLUSTERS_SECTORS,
            QuestionSubSector.BUY_IN_AND_USE_BY_UN_AGENCIES,
            QuestionSubSector.BUY_IN_AND_USE_BY_INTERNATIONAL_NGO,
            QuestionSubSector.BUY_IN_AND_USE_BY_LOCAL_NGO,
            QuestionSubSector.BUY_IN_AND_USE_BY_MEMBER_OF_RED_CROSS_RED_CRESENT_MOVEMENT,
            QuestionSubSector.BUY_IN_AND_USE_BY_DONORS,
            QuestionSubSector.BUY_IN_AND_USE_BY_NATIONAL_AND_LOCAL_GOVERNMENT_AGENCIES,
            QuestionSubSector.BUY_IN_AND_USE_BY_DEVELOPMENT_AND_STABILIZATION_ACTORS,
        ],
        QuestionSector.PEOPLE_CENTERED_AND_INCLUSIVE: [
            QuestionSubSector.AFFECTED_AND_VULNERABLE_GROUPS_COMPREHENSIVENESS,
            QuestionSubSector.SAFETY_AND_PROTECTION,
            QuestionSubSector.PARTICIPATION,
            QuestionSubSector.CONTEXT_SPECIFICITY,
        ],
        QuestionSector.ACCOUNTABILITY_TO_AFFECTED_POPULATIONS: [
            QuestionSubSector.PARTICIPATION,
            QuestionSubSector.CONTEXT_SPECIFICITY,
            QuestionSubSector.DESCRIPTIONS,
            QuestionSubSector.ACTIVE_DISSEMINATION,
        ],
        QuestionSector.DO_NOT_HARM: [
            QuestionSubSector.SAFETY_AND_PROTECTION,
        ],
        QuestionSector.DESIGNED_WITH_PURPOSE: [
            QuestionSubSector.RELEVANCE,
        ],
        QuestionSector.COMPETENCY_AND_CAPACITY: [
            QuestionSubSector.SAFETY_AND_PROTECTION,
            QuestionSubSector.CONTEXT_SPECIFICITY,
        ],
        QuestionSector.IMPARTIALITY: [
            QuestionSubSector.HUMANITARIAN_PRINCIPLES,
        ],
        QuestionSector.COORDINATION_AND_DATA_MINIMIZATION: [
            QuestionSubSector.RELEVANCE,
            QuestionSubSector.CONTRIBUTION,
        ],
        QuestionSector.JOINT_ANALYSIS: [
            QuestionSubSector.MITIGATING_BIAS,
            QuestionSubSector.ANALYTICAL_STANDARDS,
        ],
        QuestionSector.ACKNOWLEDGE_DISSENTING_VOICES_IN_JOINT_NEEDS_ANALYSIS: [
            QuestionSubSector.ANALYTICAL_STANDARDS,
        ],
        QuestionSector.IFORMED_CONSENT_CONFIDENTIALITY_AND_DATA_SECURITY: [
            QuestionSubSector.SAFETY_AND_PROTECTION,
        ],
        QuestionSector.SHARING_RESULTS: [
            QuestionSubSector.ACTIVE_DISSEMINATION,
        ],
        QuestionSector.TRANSPARENCY_BETWEEN_ACTORS: [
            QuestionSubSector.TRANSPARENCY,
            QuestionSubSector.ANALYTICAL_STANDARDS,
        ],
        QuestionSector.MINIMUM_TECHNICAL_STANDARDS: [
            QuestionSubSector.MITIGATING_BIAS,
            QuestionSubSector.ANALYTICAL_STANDARDS,
        ],
    }

    QUESTION_SECTOR_SUB_SECTOR_MAP = {
        QuestionSector.RELEVANCE: [
            QuestionSubSector.RELEVANCE,
        ],
        QuestionSector.COMPREHENSIVENESS: [
            QuestionSubSector.GEOGRAPHIC_COMPREHENSIVENESS,
            QuestionSubSector.SECTORAL_COMPREHENSIVENESS,
            QuestionSubSector.AFFECTED_AND_VULNERABLE_GROUPS_COMPREHENSIVENESS,
        ],
        QuestionSector.ETHICS: [
            QuestionSubSector.SAFETY_AND_PROTECTION,
            QuestionSubSector.HUMANITARIAN_PRINCIPLES,
            QuestionSubSector.CONTRIBUTION,
        ],
        QuestionSector.METHODOLOGICAL_RIGOR: [
            QuestionSubSector.TRANSPARENCY,
            QuestionSubSector.MITIGATING_BIAS,
            QuestionSubSector.PARTICIPATION,
            QuestionSubSector.CONTEXT_SPECIFICITY,
        ],
        QuestionSector.ANALYTICAL_VALUE: [
            QuestionSubSector.ANALYTICAL_STANDARDS,
            QuestionSubSector.DESCRIPTIONS,
            QuestionSubSector.EXPLANATION,
            QuestionSubSector.INTERPRETATION,
            QuestionSubSector.ANTICIPATION,
            QuestionSubSector.TIMELINESS,
        ],
        QuestionSector.EFFECTIVE_COMMUNICATION: [
            QuestionSubSector.USER_FRIENDLY_PRESENTATION,
            QuestionSubSector.ACTIVE_DISSEMINATION,
        ],
        QuestionSector.USE: [
            QuestionSubSector.USE_FOR_COLLECTIVE_PLANNING,
            QuestionSubSector.BUY_IN_AND_USE_BY_HUMANITARIAN_CLUSTERS_SECTORS,
            QuestionSubSector.BUY_IN_AND_USE_BY_UN_AGENCIES,
            QuestionSubSector.BUY_IN_AND_USE_BY_INTERNATIONAL_NGO,
            QuestionSubSector.BUY_IN_AND_USE_BY_LOCAL_NGO,
            QuestionSubSector.BUY_IN_AND_USE_BY_MEMBER_OF_RED_CROSS_RED_CRESENT_MOVEMENT,
            QuestionSubSector.BUY_IN_AND_USE_BY_DONORS,
            QuestionSubSector.BUY_IN_AND_USE_BY_NATIONAL_AND_LOCAL_GOVERNMENT_AGENCIES,
            QuestionSubSector.BUY_IN_AND_USE_BY_DEVELOPMENT_AND_STABILIZATION_ACTORS,
        ],
        QuestionSector.PEOPLE_CENTERED_AND_INCLUSIVE: [
            QuestionSubSector.AFFECTED_AND_VULNERABLE_GROUPS_COMPREHENSIVENESS,
            QuestionSubSector.SAFETY_AND_PROTECTION,
            QuestionSubSector.PARTICIPATION,
            QuestionSubSector.CONTEXT_SPECIFICITY,
        ],
        QuestionSector.ACCOUNTABILITY_TO_AFFECTED_POPULATIONS: [
            QuestionSubSector.PARTICIPATION,
            QuestionSubSector.CONTEXT_SPECIFICITY,
            QuestionSubSector.DESCRIPTIONS,
            QuestionSubSector.ACTIVE_DISSEMINATION,
        ],
        QuestionSector.DO_NOT_HARM: [
            QuestionSubSector.SAFETY_AND_PROTECTION,
        ],
        QuestionSector.DESIGNED_WITH_PURPOSE: [
            QuestionSubSector.RELEVANCE,
        ],
        QuestionSector.COMPETENCY_AND_CAPACITY: [
            QuestionSubSector.SAFETY_AND_PROTECTION,
            QuestionSubSector.CONTEXT_SPECIFICITY,
        ],
        QuestionSector.IMPARTIALITY: [
            QuestionSubSector.HUMANITARIAN_PRINCIPLES,
        ],
        QuestionSector.COORDINATION_AND_DATA_MINIMIZATION: [
            QuestionSubSector.RELEVANCE,
            QuestionSubSector.CONTRIBUTION,
        ],
        QuestionSector.JOINT_ANALYSIS: [
            QuestionSubSector.MITIGATING_BIAS,
            QuestionSubSector.ANALYTICAL_STANDARDS,
        ],
        QuestionSector.ACKNOWLEDGE_DISSENTING_VOICES_IN_JOINT_NEEDS_ANALYSIS: [
            QuestionSubSector.ANALYTICAL_STANDARDS,
        ],
        QuestionSector.IFORMED_CONSENT_CONFIDENTIALITY_AND_DATA_SECURITY: [
            QuestionSubSector.SAFETY_AND_PROTECTION,
        ],
        QuestionSector.SHARING_RESULTS: [
            QuestionSubSector.ACTIVE_DISSEMINATION,
        ],
        QuestionSector.TRANSPARENCY_BETWEEN_ACTORS: [
            QuestionSubSector.TRANSPARENCY,
            QuestionSubSector.ANALYTICAL_STANDARDS,
        ],
        QuestionSector.MINIMUM_TECHNICAL_STANDARDS: [
            QuestionSubSector.MITIGATING_BIAS,
            QuestionSubSector.ANALYTICAL_STANDARDS,
        ],
    }

    sector = models.IntegerField(choices=QuestionSector.choices)
    sub_sector = models.IntegerField(choices=QuestionSubSector.choices)
    question = models.CharField(max_length=500)

    def clean(self):
        sector = self.sector
        sub_sector = self.sub_sector

        # NOTE We are adding this validation here because Question are added from Admin Panel.
        if hasattr(self, 'sector'):
            if hasattr(self, 'sub_sector'):
                if sub_sector not in Question.QUESTION_SECTOR_SUB_SECTOR_MAP[sector]:
                    raise ValidationError('Invalid sebsector selected for given sector provided')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.question


class Answer(UserResource):
    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='answer'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    answer = models.BooleanField()

    class Meta:
        ordering = ["id"]
        unique_together = [["assessment_registry", "question"]]

    def __str__(self):
        return str(self.answer)


class Summary(UserResource):
    class Pillar(models.IntegerChoices):
        CONTEXT = 1, 'Context'
        EVENT_SHOCK = 2, 'Event/Shock'
        DISPLACEMENT = 3, 'Displacement'
        INFORMATION_AND_COMMUNICATION = 4, 'Information & Communication'
        HUMANITARIAN_ACCESS = 5, 'Humanitarian Access'

    assessment_registry = models.OneToOneField(AssessmentRegistry, related_name='summary', on_delete=models.CASCADE)
    total_people_assessed = models.IntegerField(null=True, blank=True)
    total_dead = models.IntegerField(null=True, blank=True)
    total_injured = models.IntegerField(null=True, blank=True)
    total_missing = models.IntegerField(null=True, blank=True)
    total_people_facing_hum_access_cons = models.IntegerField(null=True, blank=True)
    percentage_of_people_facing_hum_access_cons = models.IntegerField(null=True, blank=True)


class SummarySubPillarIssue(UserResource):
    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='summary_sub_sector_issue_ary'
    )
    summary_issue = models.ForeignKey(
        'SummaryIssue',
        on_delete=models.CASCADE,
        related_name='summary_subsector_issue'
    )
    text = models.TextField(blank=True)
    order = models.IntegerField()
    lead_preview_text_ref = models.JSONField(default=None, blank=True, null=True)


class SummaryFocus(UserResource):
    class Dimension(models.IntegerChoices):
        IMPACT = 1, 'Impact'
        HUMANITARIAN_CONDITIONS = 2, 'Humanitarian Conditions'
        PRIORITIES_AND_PREFERENCES = 3, 'Priorities & Preferences'
        CONCLUSIONS = 4, 'Conclusions'
        HUMANITARIAN_POPULATION_FIGURES = 5, 'Humanitarian Population Figures'

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='summary_focus'
    )

    sector = models.IntegerField(choices=AssessmentRegistry.SectorType.choices)
    percentage_of_people_affected = models.IntegerField(null=True, blank=True)
    total_people_affected = models.IntegerField(null=True, blank=True)
    percentage_of_moderate = models.IntegerField(null=True, blank=True)
    percentage_of_severe = models.IntegerField(null=True, blank=True)
    percentage_of_critical = models.IntegerField(null=True, blank=True)
    percentage_in_need = models.IntegerField(null=True, blank=True)
    total_moderate = models.IntegerField(null=True, blank=True)
    total_severe = models.IntegerField(null=True, blank=True)
    total_critical = models.IntegerField(null=True, blank=True)
    total_in_need = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("SummaryDimension")

    class Meta:
        verbose_name = _("SummaryDimmension")


class SummaryIssue(models.Model):
    class SubPillar(models.IntegerChoices):
        POLITICS = 1, 'Politics'
        DEMOGRAPHY = 2, 'Demography'
        SOCIO_CULTURAL = 3, 'Socio-Cultural'
        ENVIRONMENT = 4, 'Environment'
        SECURITY_AND_STABILITY = 5, 'Security & Stability'
        ECONOMICS = 6, 'Economics'
        CHARACTERISTICS = 7, 'Characteristics'
        DRIVERS_AND_AGGRAVATING_FACTORS = 8, 'Drivers and Aggravating Factors'
        MITIGATING_FACTORS = 9, 'Mitigating Factors'
        HAZARDS_AND_THREATS = 10, 'Hazards & Threats'
        DISPLACEMENT_CHARACTERISTICS = 11, 'Characteristics'
        PUSH_FACTORS = 12, 'Push Factors'
        PULL_FACTORS = 13, 'Pull Factors'
        INTENTIONS = 14, 'Intentions'
        LOCAL_INTREGATIONS = 15, 'Local Integrations'
        SOURCE_AND_MEANS = 16, 'Source & Means'
        CHALLANGES_AND_BARRIERS = 17, 'Challanges & Barriers'
        KNOWLEDGE_AND_INFO_GAPS_HUMAN = 18, 'Knowledge & Info Gaps (Humanitarian)'
        KNOWLEDGE_AND_INFO_GAPS_POP = 19, 'Knowledge & Info Gaps (Population)'
        POPULATION_TO_RELIEF = 20, 'Population To Relief'
        RELIEF_TO_POPULATION = 21, 'Relief To Population'
        PHYSICAL_AND_SECURITY = 22, 'Physical & Security'

    class SubDimension(models.IntegerChoices):
        DRIVERS = 1, 'Drivers'
        IMPACT_ON_PEOPLE = 2, 'Impact on People'
        IMPACT_ON_SYSTEM = 3, 'Impact On System, Network And Services'
        LIVING_STANDARDS = 4, 'Living Standards'
        COPING_MECHANISMS = 5, 'Coping Mechanisms'
        PHYSICAL_AND_MENTAL_WELL_BEING = 6, 'Physical And Mental Well Being'
        NEEDS_POP = 7, 'Needs (Population)'
        NEEDS_HUMAN = 8, 'Needs (Humanitarian)'
        INTERVENTIONS_POP = 9, 'Interventions (Population)'
        INTERVENTIONS_HUMAN = 10, 'Interventions (Humanitarian)'
        DEMOGRAPHIC_GROUPS = 11, 'Demographic Groups'
        GROUPS_WITH_SPECIFIC_NEEDS = 12, 'Groups With Specific Needs'
        GEOGRAPHICAL_AREAS = 13, 'Geographical Areas'
        PEOPLE_AT_RISKS = 14, 'People At Risks'
        FOCAL_ISSUES = 15, 'Focal Issues'

    PILLAR_SUB_PILLAR_MAP = {
        Summary.Pillar.CONTEXT: [
            SubPillar.POLITICS,
            SubPillar.DEMOGRAPHY,
            SubPillar.SOCIO_CULTURAL,
            SubPillar.ENVIRONMENT,
            SubPillar.SECURITY_AND_STABILITY,
            SubPillar.ECONOMICS,
        ],
        Summary.Pillar.EVENT_SHOCK: [
            SubPillar.CHARACTERISTICS,
            SubPillar.DRIVERS_AND_AGGRAVATING_FACTORS,
            SubPillar.MITIGATING_FACTORS,
            SubPillar.HAZARDS_AND_THREATS,
        ],
        Summary.Pillar.DISPLACEMENT: [
            SubPillar.DISPLACEMENT_CHARACTERISTICS,
            SubPillar.PUSH_FACTORS,
            SubPillar.PULL_FACTORS,
            SubPillar.INTENTIONS,
            SubPillar.LOCAL_INTREGATIONS,
        ],
        Summary.Pillar.INFORMATION_AND_COMMUNICATION: [
            SubPillar.SOURCE_AND_MEANS,
            SubPillar.CHALLANGES_AND_BARRIERS,
            SubPillar.KNOWLEDGE_AND_INFO_GAPS_HUMAN,
            SubPillar.KNOWLEDGE_AND_INFO_GAPS_POP,
        ],
        Summary.Pillar.HUMANITARIAN_ACCESS: [
            SubPillar.POPULATION_TO_RELIEF,
            SubPillar.RELIEF_TO_POPULATION,
            SubPillar.PHYSICAL_AND_SECURITY,
        ]
    }

    DIMMENSION_SUB_DIMMENSION_MAP = {
        SummaryFocus.Dimension.IMPACT: [
            SubDimension.DRIVERS,
            SubDimension.IMPACT_ON_PEOPLE,
            SubDimension.IMPACT_ON_SYSTEM,
        ],
        SummaryFocus.Dimension.HUMANITARIAN_CONDITIONS: [
            SubDimension.LIVING_STANDARDS,
            SubDimension.COPING_MECHANISMS,
            SubDimension.PHYSICAL_AND_MENTAL_WELL_BEING,
        ],
        SummaryFocus.Dimension.PRIORITIES_AND_PREFERENCES: [
            SubDimension.NEEDS_POP,
            SubDimension.NEEDS_HUMAN,
            SubDimension.INTERVENTIONS_HUMAN,
            SubDimension.INTERVENTIONS_POP,
        ],
        SummaryFocus.Dimension.CONCLUSIONS: [
            SubDimension.DEMOGRAPHIC_GROUPS,
            SubDimension.GROUPS_WITH_SPECIFIC_NEEDS,
            SubDimension.GEOGRAPHICAL_AREAS,
            SubDimension.PEOPLE_AT_RISKS,
            SubDimension.FOCAL_ISSUES,
        ],
    }

    sub_pillar = models.IntegerField(choices=SubPillar.choices, blank=True, null=True)
    sub_dimension = models.IntegerField(choices=SubDimension.choices, blank=True, null=True)
    parent = models.ForeignKey(
        'SummaryIssue',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    label = models.CharField(max_length=220)
    full_label = models.CharField(max_length=220, blank=True)

    def __str__(self):
        return self.label


class SummarySubDimensionIssue(UserResource):
    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='summary_focus_subsector_issue_ary'
    )
    sector = models.IntegerField(choices=AssessmentRegistry.SectorType.choices)
    summary_issue = models.ForeignKey(
        SummaryIssue,
        on_delete=models.CASCADE,
        related_name='summary_focus_subsector_issue'
    )
    text = models.TextField(blank=True)
    order = models.IntegerField()
    lead_preview_text_ref = models.JSONField(default=None, blank=True, null=True)
