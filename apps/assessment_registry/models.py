from django.db import models
from django.contrib.postgres.fields import ArrayField

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
        WITH_PREPAREDNESS = 0, 'With Preparedness'
        WITHOUT_PREPAREDNESS = 1, 'Without Preparedness'

    class ExternalSupportType(models.IntegerChoices):
        EXTERNAL_SUPPORT_RECIEVED = 0, 'External Support Received'
        NO_EXTERNAL_SUPPORT_RECEIVED = 1, 'No External Support Received'

    class CoordinationType(models.IntegerChoices):
        COORDINATED = 0, 'Coordinated Joint'
        HARMONIZED = 1, 'Coordinated Harmonized'
        UNCOORDINATED = 2, 'Uncoordinated'

    class Type(models.IntegerChoices):
        INITIAL = 0, 'Initial'
        RAPID = 1, 'Rapid'
        IN_DEPTH = 2, 'In depth'
        MONITORING = 3, 'Monitoring'
        OTHER = 4, 'Other'

    class FamilyType(models.IntegerChoices):
        DISPLACEMENT_TRAKING_MATRIX = 0, 'Displacement Traking Matrix'
        MULTI_CLUSTER_INITIAL_AND_RAPID_ASSESSMENT = 1, 'Multi Cluster Initial and Rapid Assessment (MIRA)'
        MULTI_SECTORIAL_NEEDS_ASSESSMENT = 2, 'Multi sectorial Needs Assessment (MSNA)'
        EMERGENCY_FOOD_SECURITY_ASSESSMENT = 3, 'Emergency Food Security Assessment (EFSA)'
        COMPREHENSIVE_FOOD_SECURITY_AND_VULNERABILITY_ANALYSIS = \
            4, 'Comprehensive Food Security and Vulnerability Analysis(CFSVA)'
        PROTECTION_MONITORING = 5, 'Protection Monitoring'
        HUMANITARIAN_NEEDS_OVERVIEW = 6, 'Humanitarian Needs Overview (HNO)'
        BRIEFING_NOTE = 7, 'Briefing note'
        REGISTRATION = 8, 'Registration'
        IDP_PROFILING_EXERCISE = 9, 'IDPs profiling exercise'
        CENSUS = 10, 'Census'
        REFUGEE_AND_MIGRANT_RESPONSE_PLAN = 11, 'Refugee and Migrant Response Plan (RMRP)'
        RUFUGEE_RESPONSE_PLAN = 12, 'Refugee Response Plan (RRP)'
        SMART_NUTRITION_SURVEY = 13, 'Smart Nutrition Survey'
        OTHER = 14, 'Other'

    class FrequencyType(models.IntegerChoices):
        ONE_OFF = 0, 'One off'
        REGULAR = 1, 'Regular'

    class ConfidentialityType(models.IntegerChoices):
        UNPROTECTED = 0, 'Unprotected'
        CONFIDENTIAL = 1, 'Confidential'

    class Language(models.IntegerChoices):
        ENGLISH = 0, 'English'
        FRENCH = 1, 'French'
        SPANISH = 2, 'Spanish'
        PORTUGESE = 3, 'Portugese'
        ARABIC = 4, 'Arabic'

    class FocusType(models.IntegerChoices):
        CONTEXT = 0, 'Context'
        SHOCK_EVENT = 1, 'Shock/Event'
        DISPLACEMENT = 2, 'Displacement'
        CASUALTIES = 3, 'Casualties'
        INFORMATION_AND_COMMUNICATION = 4, 'Information and Communication'
        HUMANITERIAN_ACCESS = 5, 'Humaniterian Access'
        IMPACT = 6, 'Impact'
        HUMANITARIAN_CONDITIONS = 7, 'Humanitarian Conditions'
        PEOPLE_AT_RISK = 8, 'People at risk'
        PRIORITIES_AND_PREFERENCES = 9, 'Priorities & Preferences'
        RESPONSE_AND_CAPACITIES = 10, 'Response and Capacities'

    class SectorType(models.IntegerChoices):
        FOOD_SECURITY = 0, 'Food Security'
        HEALTH = 1, 'Heath'
        SHELTER = 2, 'Shelter'
        WASH = 3, 'Wash'
        PROTECTION = 4, 'Protection'
        NUTRITION = 5, 'Nutrition'
        LIVELIHOOD = 6, 'Livelihood'
        EDUCATION = 7, 'Education'
        LOGISTICS = 8, 'Logistics'
        INTER_CROSS_SECTOR = 9, 'Inter/Cross Sector'

    class ProtectionInfoType(models.IntegerChoices):
        PROTECTION_MONITORING = 0, 'Protection Monitoring'
        PROTECTION_NEEDS_ASSESSMENT = 1, 'Protection Needs Assessment'
        CASE_MANAGEMENT = 2, 'Case Management'
        POPULATION_DATA = 3, 'Population Data'
        PROTECTION_RESPONSE_M_E = 4, 'Protection Response M&E'
        COMMUNICATING_WITH_IN_AFFECTED_COMMUNITIES = 5, 'Communicating with(in) Affected Communities'
        SECURITY_AND_SITUATIONAL_AWARENESS = 6, 'Security & Situational Awareness'
        SECTORAL_SYSTEM_OTHER = 7, 'Sectoral System/Other'

    class AffectedGroupType(models.IntegerChoices):
        ALL = 0, 'All'
        ALL_AFFECTED = 1, 'All/Affected'
        ALL_NOT_AFFECTED = 2, 'All/Not Affected'
        ALL_AFFECTED_NOT_DISPLACED = 3, 'All/Affected/Not Displaced'
        ALL_AFFECTED_DISPLACED = 4, 'All/Affected/Displaced'
        ALL_AFFECTED_DISPLACED_IN_TRANSIT = 5, 'All/Affected/Displaced/In Transit'
        ALL_AFFECTED_DISPLACED_MIGRANTS = 6, 'All/Affected/Displaced/Migrants'
        ALL_AFFECTED_DISPLACED_IDPS = 7, 'All/Affected/Displaced/IDPs'
        ALL_AFFECTED_DISPLACED_ASYLUM_SEEKER = 8, 'All/Affected/Displced/Asylum Seeker'
        ALL_AFFECTED_DISPLACED_OTHER_OF_CONCERN = 9, 'All/Affected/Displaced/Other of concerns'
        ALL_AFFECTED_DISPLACED_RETURNEES = 10, 'All/Affected/Displaced/Returnees'
        ALL_AFFECTED_DISPLACED_REFUGEES = 11, 'All/Affected/Displaced/Refugees'
        ALL_AFFECTED_DISPLACED_MIGRANTS_IN_TRANSIT = 12, 'All/Affected/Displaced/Migrants/In transit'
        ALL_AFFECTED_DISPLACED_MIGRANTS_PERMANENTS = 13, 'All/Affected/Displaced/Migrants/Permanents'
        ALL_AFFECTED_DISPLACED_MIGRANTS_PENDULAR = 14, 'All/Affected/Displaced/Migrants/Pendular'
        ALL_AFFECTED_NOT_DISPLACED_NO_HOST = 15, 'All/Affected/Not Displaced/No Host'
        ALL_AFFECTED_NOT_DISPLACED_HOST = 16, 'All/Affected/Not Displaced/Host'

    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    lead = models.OneToOneField(
        Lead, on_delete=models.CASCADE,
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
    lead_organizations = models.ManyToManyField(Organization, related_name='lead_org_assessment_reg', blank=True)
    international_partners = models.ManyToManyField(Organization, related_name='int_partners_assessment_reg', blank=True)
    donors = models.ManyToManyField(Organization, related_name='donor_assessment_reg', blank=True)
    national_partners = models.ManyToManyField(Organization, related_name='national_partner_assessment_reg', blank=True)
    governments = models.ManyToManyField(Organization, related_name='gov_assessment_reg', blank=True)

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
        blank=True, null=True
    )
    affected_groups = ArrayField(
        models.IntegerField(choices=AffectedGroupType.choices),
        default=list
    )

    locations = models.ManyToManyField(GeoArea, related_name='focus_location_assessment_reg', blank=True)

    # Score Fields
    matrix_score = models.IntegerField(default=0)
    final_score = models.IntegerField(default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.project.title


class MethodologyAttribute(UserResource):
    class CollectionTechniqueType(models.IntegerChoices):
        SECONDARY_DATA_REVIEW = 0, 'Secondary Data Review'
        KEY_INFORMAT_INTERVIEW = 1, 'Key Informant Interview'
        DIRECT_OBSERVATION = 2, 'Direct Observation'
        COMMUNITY_GROUP_DISCUSSION = 3, 'Community Group Discussion'
        FOCUS_GROUP_DISCUSSION = 4, 'Focus Group Discussion'
        HOUSEHOLD_INTERVIEW = 5, 'Household Interview'
        INDIVIDUAL_INTERVIEW = 6, 'Individual Interview'
        SATELLITE_IMAGERY = 7, 'Satellite Imagery'

    class SamplingApproachType(models.IntegerChoices):
        NON_RANDOM_SELECTION = 0, 'Non-Random Selection'
        RANDOM_SELECTION = 1, 'Random Selection'
        FULL_ENUMERATION = 2, 'Full Enumeration'

    class ProximityType(models.IntegerChoices):
        FACE_TO_FACE = 0, 'Face-to-Face'
        REMOTE = 1, 'Remote'
        MIXED = 2, 'Mixed'

    class UnitOfAnalysisType(models.IntegerChoices):
        CRISIS = 0, 'Crisis'
        COUNTRY = 1, 'Country'
        REGION = 2, 'Region'
        PROVINCE_GOV_PREFECTURE = 3, 'Province/governorate/prefecture'
        DEPARTMENT_DISTRICT = 4, 'Department/District'
        SUB_DISTRICT_COUNTRY = 5, 'Sub-District/Country'
        MUNICIPALITY = 6, 'Municipality'
        NEIGHBORHOOD_QUARTIER = 7, 'Neighborhood/Quartier'
        COMMUNITY_SITE = 8, 'Community/Site'
        AFFECTED_GROUP = 9, 'Affected group'
        HOUSEHOLD = 10, 'Household'
        INDIVIDUAL = 11, 'Individual'

    class UnitOfReportingType(models.IntegerChoices):
        CRISIS = 0, 'Crisis'
        COUNTRY = 1, 'Country'
        REGION = 2, 'Region'
        PROVINCE_GOV_PREFECTURE = 3, 'Province/governorate/prefecture'
        DEPARTMENT_DISTRICT = 4, 'Department/District'
        SUB_DISTRICT_COUNTRY = 5, 'Sub-District/Country'
        MUNICIPALITY = 6, 'Municipality'
        NEIGHBORHOOD_QUARTIER = 7, 'Neighborhood/Quartier'
        COMMUNITY_SITE = 8, 'Community/Site'
        AFFECTED_GROUP = 9, 'Affected group'
        HOUSEHOLD = 10, 'Household'
        INDIVIDUAL = 11, 'Individual'

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
        ASSESSMENT_DATABASE = 0, 'Assessment database'
        QUESTIONNAIRE = 1, 'Questionnaire'
        MISCELLANEOUS = 2, 'Miscellaneous'

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


class ScoreRating(UserResource):
    class AnalyticalStatement(models.IntegerChoices):
        FIT_FOR_PURPOSE = 0, 'Fit for purpose'
        TRUSTWORTHINESS = 1, 'Trustworthiness'
        ANALYTICAL_RIGOR = 2, 'Analytical Rigor'
        ANALYTICAL_WRITING = 3, 'Analytical Writing'

    class ScoreCriteria(models.IntegerChoices):
        RELEVANCE = 0, "Relevance"
        COMPREHENSIVENESS = 1, "Comprehensiveness"
        TIMELINESS = 2, "Timeliness"
        GRANULARITY = 3, "Granularity"
        COMPARABILITY = 4, "Comparability"
        SOURCE_REABILITY = 5, "Source reability"
        METHODS = 6, "Methods"
        TRIANGULATION = 7, "Triangulation"
        PLAUSIBILITY = 8, "Plausibility"
        INCLUSIVENESS = 9, "Inclusiveness"
        ASSUMPTIONS = 10, "Assumptions"
        CORROBORATION = 11, "Corroboration"
        STRUCTURED_ANALYTICAL_TECHNIQUE = 12, "Structured Ananlytical Technique"
        CONSENSUS = 13, "Consensus"
        REPRODUCIBILITY = 14, "Reproducibility"
        CLEARLY_ARTICULATED_RESULT = 15, "Clearly Articulated Result"
        LEVEL_OF_CONFIDENCE = 16, "Level Of Confidence"
        ILLUSTRATION = 17, "Illustration"
        SOURCED_DATA_EVIDENCE = 18, "Sourced data and evidence"
        CLEARLY_STATED_OUTLIERS = 19, "Clearly stated outliers"

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
        ISSUE_UNMET_NEEDS_ARE_DETAILED = 0, 'Issues/unmet needs are detailed'
        ISSUE_UNMET_NEEDS_ARE_PRIOTIZED_RANKED = 1, 'Issues/unmet needs are priotized/ranked'
        CAUSES_OR_UNDERLYING_MECHANISMS_BEHIND_ISSUES_UNMET_NEEDS_ARE_DETAILED = 2,\
            'Causes or underlying mechanisms behind issues/unmet needs are detailed'
        CAUSES_OR_UNDERLYING_MECHANISMS_BEHIND_ISSUES_UNMET_NEEDS_ARE_PRIOTIZED_RANKED = 3,\
            'Causes or underlying mechanisms behind issues/unmet needs are priotized/ranked'
        SEVERITY_OF_SOME_ALL_ISSUE_UNMET_NEEDS_IS_DETAILED = 4,\
            'Severity of some/all issues/unmet_needs_is_detailed'
        FUTURE_ISSUES_UNMET_NEEDS_ARE_DETAILED = 5, 'Future issues/unmet needs are detailed'
        FUTURE_ISSUES_UNMET_NEEDS_ARE_PRIOTIZED_RANKED = 6, 'Future issues/unmet needs are priotized/ranked'
        SEVERITY_OF_SOME_ALL_FUTURE_ISSUE_UNMET_NEEDS_IS_DETAILED = 7,\
            'Severity of some/all future issues/unmet_needs_is_detailed'
        RECOMMENDATIONS_INTERVENTIONS_ARE_DETAILED = 8, 'Recommnedations/interventions are detailed'
        RECOMMENDATIONS_INTERVENTIONS_ARE_PRIOTIZED_RANKED = 9,\
            'Recommnedations/interventions are priotized/ranked'

    class FigureProvidedByAssessement(models.IntegerChoices):
        TOTAL_POP_IN_THE_ASSESSED_AREAS = 0, 'Total population in the assessed areas'
        TOTAL_POP_EXPOSED_TO_THE_SHOCK_EVENT = 1, 'Total population exposed to the shock/event'
        TOTAL_POP_AFFECTED_LIVING_IN_THE_AFFECTED_AREAS = 2,\
            'Total populaiton affected/living in the affected area'
        TOTAL_POP_FACING_HUMANITARIAN_ACCESS_CONSTRAINTS = 3, 'Total population facing humanitarian access constraints'
        TOTAL_POP_IN_NEED = 4, 'Total populaiton in need'
        TOTAL_POP_IN_CRITICAL_NEED = 5, 'Total population in critical need'
        TOTAL_POP_IN_SEVERE_NEED = 6, 'Total population in severe need'
        TOTAL_POP_IN_MODERATE_NEED = 7, 'Total population in moderate need'
        TOTAL_POP_AT_RISK_VULNERABLE = 9, 'Total population at risk/vulnerable'
        TOTAL_POP_REACHED_BY_ASSISTANCE = 10, 'Total population reached by assistance'

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='analytical_density'
    )
    sector = models.IntegerField(choices=AssessmentRegistry.SectorType.choices)
    analysis_level_covered = ArrayField(models.IntegerField(choices=AnalysisLevelCovered.choices), default=list)
    figure_provided = ArrayField(models.IntegerField(choices=FigureProvidedByAssessement.choices), default=list)


class Question(UserResource):
    class QuestionSector(models.IntegerChoices):
        RELEVANCE = 0, 'Relevance'
        COMPREHENSIVENESS = 1, 'Comprehensiveness'
        ETHICS = 2, 'Ethics'
        METHODOLOGICAL_RIGOR = 3, 'Methodological rigor'
        ANALYTICAL_VALUE = 4, 'Analytical value'
        TIMELINESS = 5, 'Timeliness'
        EFFECTIVE_COMMUNICATION = 6, 'Effective Communication'
        USE = 7, 'Use',
        PEOPLE_CENTERED_AND_INCLUSIVE = 8, 'People-centered and inclusive'
        ACCOUNTABILITY_TO_AFFECTED_POPULATIONS = 9, 'Accountability to affected populations'
        DO_NOT_HARM = 10, 'Do not harm'
        DESIGNED_WITH_PURPOSE = 11, 'Designed with a purpose'
        COMPETENCY_AND_CAPACITY = 12, 'Competency and capacity'
        IMPARTIALITY = 13, 'Impartiality'
        COORDINATION_AND_DATA_MINIMIZATION = 14, 'Coordination and data minimization'
        JOINT_ANALYSIS = 15, 'Joint Analysis'
        ACKNOWLEDGE_DISSENTING_VOICES_IN_JOINT_NEEDS_ANALYSIS = 16, 'Acknowledge dissenting voices in joint needs analysis'
        IFORMED_CONSENT_CONFIDENTIALITY_AND_DATA_SECURITY = 17, 'Informed consent, confidentiality and data security'
        SHARING_RESULTS = 18, 'Sharing results (data and analysis)'
        TRANSPARENCY_BETWEEN_ACTORS = 19, 'Tranparency between actors'
        MINIMUM_TECHNICAL_STANDARDS = 20, 'Minimum technical standards'

    class QuestionSubSector(models.IntegerChoices):
        RELEVANCE = 0, 'Relevance'
        GEOGRAPHIC_COMPREHENSIVENESS = 1, 'Geographic comprehensiveness'
        SECTORAL_COMPREHENSIVENESS = 2, 'Sectoral comprehensiveness'
        AFFECTED_AND_VULNERABLE_GROUPS_COMPREHENSIVENESS = 3, 'Affected and vulnerabel groups comprehensiveness'
        SAFETY_AND_PROTECTION = 4, 'Safety and protection'
        HUMANITARIAN_PRINCIPLES = 5, 'Humanitarian Principles'
        CONTRIBUTION = 6, 'Contribution'
        TRANSPARENCY = 7, 'Transparency'
        MITIGATING_BIAS = 8, 'Mitigating Bias'
        PARTICIPATION = 9, 'Participation'
        CONTEXT_SPECIFICITY = 10, 'Context specificity'
        ANALYTICAL_STANDARDS = 11, 'Ananlytical standards'
        DESCRIPTIONS = 12, 'Descriptions'
        EXPLANATION = 13, 'Explanation'
        INTERPRETATION = 14, 'Interpretation'
        ANTICIPATION = 15, 'Anticipation'
        TIMELINESS = 16, 'Timeliness'
        USER_FRIENDLY_PRESENTATION = 17, 'User-friendly presentation'
        ACTIVE_DISSEMINATION = 18, 'Active dissemination'
        USE_FOR_COLLECTIVE_PLANNING = 19, 'Use for collective planning'
        BUY_IN_AND_USE_BY_HUMANITARIAN_CLUSTERS_SECTORS = 20, 'Buy-in and use by humanitarian clusters/sectors'
        BUY_IN_AND_USE_BY_UN_AGENCIES = 21, 'Buy-in and use by UN agencies'
        BUY_IN_AND_USE_BY_INTERNATIONAL_NGO = 22, 'Buy-in and use by international non-governmental organizations (NGOs)'
        BUY_IN_AND_USE_BY_LOCAL_NGO = 23, 'Buy-in and use by local non-governmental organization (local NGOs)'
        BUY_IN_AND_USE_BY_MEMBER_OF_RED_CROSS_RED_CRESENT_MOVEMENT = 24, \
            'Buy-in and use by member of Red Cross/Red Cresent Movement'
        BUY_IN_AND_USE_BY_DONORS = 25, 'Buy-in and use by donors'
        BUY_IN_AND_USE_BY_NATIONAL_AND_LOCAL_GOVERNMENT_AGENCIES = 26, \
            'Buy-in and use by naional and local government agencies'
        BUY_IN_AND_USE_BY_DEVELOPMENT_AND_STABILIZATION_ACTORS = 27, 'Buy-in and use by development and stabilization actors'

    sector = models.IntegerField(choices=QuestionSector.choices)
    sub_sector = models.IntegerField(choices=QuestionSubSector.choices)
    question = models.CharField(max_length=500)

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


class Summary(UserResource):
    class Pillar(models.IntegerChoices):
        CONTEXT = 0, 'Context'
        EVENT_SHOCK = 1, 'Event/Shock'
        DISPLACEMENT = 2, 'Displacement'
        INFORMATION_AND_COMMUNICATION = 3, 'Information & Communication'
        HUMANITARIAN_ACCESS = 4, 'Humanitarian Access'

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='summary'
    )
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
    order = models.IntegerField(blank=True, null=True)
    lead_preview_text_ref = models.JSONField(default=None, blank=True, null=True)


class SummaryFocus(UserResource):
    class Dimmension(models.IntegerChoices):
        IMPACT = 0, 'Impact'
        HUMANITARIAN_CONDITIONS = 1, 'Humanitarian Conditions'
        PRIORITIES_AND_PREFERENCES = 2, 'Priorities & Preferences'
        CONCLUSIONS = 3, 'Conclusions'
        HUMANITARIAN_POPULATION_FIGURES = 4, 'Humanitarian Population Figures'

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='summary_focus'
    )
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
    total_pop_assessed = models.IntegerField(null=True, blank=True)
    total_not_affected = models.IntegerField(null=True, blank=True)
    total_affected = models.IntegerField(null=True, blank=True)
    total_people_in_need = models.IntegerField(null=True, blank=True)
    total_people_moderately_in_need = models.IntegerField(null=True, blank=True)
    total_people_severly_in_need = models.IntegerField(null=True, blank=True)
    total_people_critically_in_need = models.IntegerField(null=True, blank=True)


class SummaryIssue(models.Model):
    class SubPillar(models.IntegerChoices):
        POLITICS = 0, 'Politics'
        DEMOGRAPHY = 1, 'Demography'
        SOCIO_CULTURAL = 2, 'Socio-Cultural'
        ENVIRONMENT = 3, 'Environment'
        SECURITY_AND_STABILITY = 4, 'Security & Stability'
        ECONOMICS = 5, 'Economics'
        CHARACTERISTICS = 6, 'Characteristics'
        DRIVERS_AND_AGGRAVATING_FACTORS = 7, 'Drivers and Aggravating Factors'
        MITIGATING_FACTORS = 8, 'Mitigating Factors'
        HAZARDS_AND_THREATS = 9, 'Hazards & Threats'
        DISPLACEMENT_CHARACTERISTICS = 10, 'Characteristics'
        PUSH_FACTORS = 11, 'Push Factors'
        PULL_FACTORS = 12, 'Pull Factors'
        INTENTIONS = 13, 'Intentions'
        LOCAL_INTREGATIONS = 14, 'Local Integrations'
        SOURCE_AND_MEANS = 15, 'Source & Means'
        CHALLANGES_AND_BARRIERS = 16, 'Challanges & Barriers'
        KNOWLEDGE_AND_INFO_GAPS_HUMAN = 17, 'Knowledge & Info Gaps (Humanitarian)'
        KNOWLEDGE_AND_INFO_GAPS_POP = 18, 'Knowledge & Info Gaps (Population)'
        POPULATION_TO_RELIEF = 19, 'Population To Relief'
        RELIEF_TO_POPULATION = 20, 'Relief To Population'
        PHYSICAL_AND_SECURITY = 21, 'Physical & Security'

    class SubDimmension(models.IntegerChoices):
        DRIVERS = 0, 'Drivers'
        IMPACT_ON_PEOPLE = 1, 'Impact on People'
        IMPACT_ON_SYSTEM = 2, 'Impact On System, Network And Services'
        LIVING_STANDARDS = 3, 'Living Standards'
        COPING_MECHANISMS = 4, 'Coping Mechanisms'
        PHYSICAL_AND_MENTAL_WELL_BEING = 5, 'Physical And Mental Well Being'
        NEEDS_POP = 6, 'Needs (Population)'
        NEEDS_HUMAN = 7, 'Needs (Humanitarian)'
        INTERVENTIONS_POP = 8, 'Interventions (Population)'
        INTERVENTIONS_HUMAN = 9, 'Interventions (Humanitarian)'
        DEMOGRAPHIC_GROUPS = 10, 'Demographic Groups'
        GROUPS_WITH_SPECIFIC_NEEDS = 11, 'Groups With Specific Needs'
        GEOGRAPHICAL_AREAS = 12, 'Geographical Areas'
        PEOPLE_AT_RISKS = 13, 'People At Risks'
        FOCAL_ISSUES = 14, 'Focal Issues'

    sub_pillar = models.IntegerField(choices=SubPillar.choices, blank=True, null=True)
    sub_dimmension = models.IntegerField(choices=SubDimmension.choices, blank=True, null=True)
    parent = models.ForeignKey(
        'SummaryIssue',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    label = models.CharField(max_length=220)
    full_label = models.CharField(max_length=220, blank=True)


class SummaryFocusSubSectorIssue(UserResource):
    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='summary_focus_subsector_issue_ary'
    )
    focus = models.IntegerField(choices=AssessmentRegistry.SectorType.choices)
    summary_issue = models.ForeignKey(
        SummaryIssue,
        on_delete=models.CASCADE,
        related_name='summary_focus_subsector_issue'
    )
    text = models.TextField(blank=True)
    order = models.IntegerField(blank=True, null=True)
    lead_preview_text_ref = models.JSONField(default=None, blank=True, null=True)
