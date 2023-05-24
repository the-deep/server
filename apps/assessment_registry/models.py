from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator

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
        HUMANITERIAN_ACCESS = 3, 'Humaniterian Access'
        INFORMATION_AND_COMMUNICATION = 4, 'Information and Communication'
        IMPACT = 5, 'Impact (Scope and Scale)'
        HUMANITARIAN_CONDITIONS = 6, 'Humanitarian Conditions'
        RESPONSE_AND_CAPACITIES = 7, 'Response and Capacities'
        CURRENT_AND_FORECASTED_PRIORITIES = 8, 'Current and Forecasted Priorities'
        COVID_19_CONTAINMENT_MEASURES = 9, 'Covid 19 Containment Measures'

    class SectorType(models.IntegerChoices):
        F00D = 0, 'Food'
        HEALTH = 1, 'Heath'
        SHELTER = 2, 'Shelter'
        WASH = 3, 'Wash'
        PROTECTION = 4, 'Protection'
        NUTRITION = 5, 'Nutrition'
        LIVELIHOOD = 6, 'Livelihood'
        EDUCATION = 7, 'Education'
        CHILD_PROTECTION = 8, 'Child protection'
        GENDER_BASED_VIOLENCE = 9, 'Gender Based Violence'

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
        default=list
    )
    affected_groups = ArrayField(
        models.IntegerField(choices=AffectedGroupType.choices),
        default=list
    )

    locations = models.ManyToManyField(GeoArea, related_name='focus_location_assessment_reg', blank=True)

    # Score Fields
    matrix_score = models.IntegerField(default=0)
    final_score = models.IntegerField(default=0)


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
    class ScoreType(models.IntegerChoices):
        RELEVANCE = 0, "Fit for purpose -> Relevance"
        COMPREHENSIVENESS = 1, "Fit for purpose -> Comprehensiveness"
        TIMELINESS = 2, "Fit for purpose -> Timeliness"
        GRANULARITY = 3, "Fit for purpose -> Granularity"
        COMPARABILITY = 4, "Fit for purpose -> Comparability"
        SOURCE_REABILITY = 5, "Trustworthiness -> Source reability"
        METHODS = 6, "Trustworthiness -> Methods"
        TRIANGULATION = 7, "Trustworthiness -> Triangulation"
        PLAUSIBILITY = 8, "Trustworthiness -> Plausibility"
        INCLUSIVENESS = 9, "Trustworthiness - Inclusiveness"
        ASSUMPTIONS = 10, "Analytical rigor -> Assumptions"
        CORROBORATION = 11, "Analytical rigor -> Corroboration"
        STRUCTURED_ANALYTICAL_TECHNIQUE = 12, "Analytical rigor -> Structured Ananlytical Technique"
        CONSENSUS = 13, "Analytical rigor > Consensus"
        REPRODUCIBILITY = 14, "Analytical rigor -> Reproducibility"
        CLEARLY_ARTICULATED_RESULT = 15, "Analytical Writing -> Clearly Articulated Result"
        LEVEL_OF_CONFIDENCE = 16, "Analytical writing -> Level Of Confidence"
        ILLUSTRATION = 17, "Analytical writing -> Illustration"
        SOURCED_DATA_EVIDENCE = 18, "Analytical writing -> Sourced data and evidence"
        CLEARLY_STATED_OUTLIERS = 19, "Analytical writing -> Clearly stated outliers"

    class RatingType(models.IntegerChoices):
        VERY_POOR = 1, "Very poor"
        POOR = 2, "Poor"
        FAIR = 3, "Fair"
        GOOD = 4, "Good"
        VERY_GOOD = 5, "Very Good"

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='score_ratings',
    )
    score_type = models.IntegerField(choices=ScoreType.choices)
    rating = models.IntegerField(choices=RatingType.choices)
    reason = models.TextField(blank=True, null=True)


class ScoreAnalyticalDensity(UserResource):
    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='analytical_density'
    )
    sector = models.IntegerField(choices=AssessmentRegistry.SectorType.choices)
    value = models.IntegerField(validators=[MaxValueValidator(49), MinValueValidator(1)])


class Summary(UserResource):
    class SubSector(models.IntegerChoices):
        PRIORITY_HUMANITARIAN_ACCESS_ISSUES = 0, 'Priority humanitarian access issues'
        SETTINGS_FACING_MOST_HUMANITARIAN_ACCESS_ISSUES = 1, 'Settings facing most humanitarian access issues'

    class FocusColumn(models.IntegerChoices):
        POPULATION_IN_MODERATE_NEED_OF_ASSISTANCE = 0, 'Population in moderate need of assistance (not life threatning)'
        POPULATION_IN_SEVERE_NEED_OF_ASSISTANCE = 1, 'Population in severe need of assistance (life threatning)'
        POPULATION_IN_NEED_OF_ASSISTANCE = 3, 'Population in need of assistance'

    class Row(models.IntegerChoices):
        ONE = 1, 'One'
        TWO = 2, 'Two'
        THRE = 3, 'Three'

    class ValueType(models.IntegerChoices):
        RAW = 0, 'Raw'
        ENUM = 1, 'Enum'

    class SubFocus(models.IntegerChoices):
        MAIN_SECTORIAL_OUTCOMES = 0, 'Main sectorial outcomes'
        MAIN_SECTORIAL_UNDERLYING_FACTORS = 1, 'Main sectorial underlying factors'
        PRIORITY_AFFECTED_GROUPS = 2, 'Priority affected groups'
        PRIORITY_GROUP_WITH_SPECIFIC_NEEDS = 3, 'Priority group with specific needs'

    class SectorColumn(models.IntegerChoices):
        POPULATION_WITH_LIMITED_ACCESS = 0, 'Population with limited/interminent access'
        POPULATION_WITH_NO_ACCESS = 1, 'Population with no/restricted access'
        POPULATION_WITH_HUMANITARIAN_ACCESS_CONSTRAINTS = 2, 'Population with humanitarian access constraints'

    class SummaryFocusValue(models.IntegerChoices):
        # Focus ->  Main sectorial underlying factors
        AVAILABILITY = 100, 'Availability'
        AVAILABILITY_PRODUCTION = 101, 'Availability/Production'
        AVAILABILITY_TRADE = 102, 'Availability/Trade'
        AVAILABILITY_STOCK = 103, 'Availability/Stock'
        AVAILABILITY_TRANSFER = 104, 'Availability/Transfer'
        ACCESS = 105, 'Access'
        ACCESS_PHYSICAL = 106, 'Access/Physical'
        ACCESS_FINANCIAL = 107, 'Access/Financial'
        ACCESS_SECURITY = 108, 'Access/Security'
        ACCESS_SOCIAL_DISCRIMINATION = 109, 'Access/Social Discrimination'
        QUALITY = 110, 'Quality'
        QUALITY_HUMAN_RESOURCES = 111, 'Quality/Human resources'
        QUALITY_SAFETY = 112, 'Quality/Safety'
        QUALITY_RELIABILITY = 113, 'Quality/Reliability'
        QUALITY_DIVERSITY = 114, 'Quality/Diversity'
        QUALITY_DIGNITY = 115, 'Quality/Dignity'
        USE = 116, 'USE'
        USE_KNOWLEDGE = 117, 'Use/Knowledge'
        USE_ATTITUDE = 118, 'Use/Attitude'
        USE_PRACTICE = 119, 'Use/Practice'
        AWARENESS = 120, 'Awareness'
        AWARENESS_MESSAGE = 121, 'Awareness/Message'
        AWARENESS_CHANNEL = 122, 'Awareness/Channel'
        AWARENESS_FERQUENCY = 123, 'Awareness/Frequency'

        # Focus -> Priority affected groups
        ALL = 200, 'All'
        ALL_AFFECTED = 201, 'All/Affected'
        AFFECTED_DISPLACED = 202, 'Affected/Displaced'
        DISPLACED_REFUGEES = 203, 'Displaced Refugees'
        DISPLACED_RETURNEES = 204, 'Displaced Returnees'
        DISPLACED_OTHER_OF_CONCERNS = 205, 'Displaced/Other of concrens'
        DISPLACED_ASYLUM_SEEKERS = 206, 'Displaced/Asylum Seekers'
        DISPLACED_IDPS = 207, 'Displaced/IDPs'
        DISPLACED_MIGRANTS = 208, 'Displaced/Migrants'
        MIGRANTS_PENDULAR = 209, 'Migrants/Pendular'
        MIGRANTS_PERMANENTS = 210, 'Migrants/Permanents'
        MIGRANTS_IN_TRANSIT = 211, 'Migrants/In transit'
        DISPLACED_IN_TRANSIT = 212, 'Displaced/In Transit'
        AFFECTED_NOT_DISPLACED = 213, 'Affected/Not Displaced'
        NOT_DISPLACED_HOST = 214, 'Not Displaced/Host'
        NOT_DISPLACED_NOT_HOST = 215, 'Not Displaced/No Host'
        ALL_NOT_AFFECTED = 216, 'All/Not Affected'

        # Focus -> Priority groups with specific needs
        FEMALE_HEAD_OF_HOUSEHOLD = 300, 'Female Head of Household'
        CHILD_HEAD_OF_HOUSEHOLD = 301, 'Child Head of Household'
        ELDERLY_HEAD_OF_HOUSEHOLD = 302, 'Elderly Head of Household'
        SINGLE_WOMEN = 303, 'Single Women (including widows'
        CHRONICALLY_ILL = 304, 'Chronically Ill'
        UNNACOMPANIED_CHILDREN = 305, 'Unnacompanied Children (without caregivers)'
        SEPARATE_CHILDREN = 306, 'Separate children'
        MINORITIES = 307, 'Minorities'
        PERSON_WITH_DISABILITIES = 308, 'Person with Disabilities'
        PREGNANT_OR_LACTATING_WOMEN = 309, 'Pregnant or Lactationg Women'
        UNREGISTERED_REFUGEE = 310, 'Unregistered Refugee'

    class SummarySectorValue(models.IntegerChoices):
        # Sector -> Priority humanitarian access issues
        ACCESS_OF_HUMANITARIAN_ACTORS_TO_AFFECTED_POP = 400, 'Access of Humanitarian Actors to Affected Populations'
        ACCESS_OF_HUMANITARIAN_ACTORS_TO_AFFECTED_POP_IMPEDIMENTS_TO_ENTRY_INTO_COUNTRY = 401,\
            'Access of Humanitarian Actors to Affected Populations/Impediments to entry into country(bureaucratic and \
administrative)'
        ACCESS_OF_HUMANITARIAN_ACTORS_TO_AFFECTED_POP_RESTRICTION_OF_MOVEMENT = 402,\
            'Access of Humanitarian Actors to Affected Populations/Restriction of movement(\
impediments to freedom of movement and/or administrative restrictions)'
        ACCESS_OF_HUMANITARIAN_ACTORS_TO_AFFECTED_POP_INTERFERENCE_INTO_IMPLEMENTATION_OF_HUMANITARIAN_ACTIVITIES = 403,\
            'Access of Humanitarian Actors to Affected Populations/Interference\
into implementation of humanitarian activities'
        ACCESS_OF_HUMANITARIAN_ACTORS_TO_AFFECTED_POP_VIOLENCE_AGAINST_PERSONNEL_FACILITIES_ASSETS = 404,\
            'Access of Humanitarian Actors to Affected Populations/Violence against personnel, facilities and assets'
        ACCESS_OF_PEOPLE_IN_NEED_TO_AID = 405, 'Access of People in need to Aid'
        ACCESS_OF_PEOPLE_IN_NEED_T0_AID_DENIAL_OF_EXISTENCE_OF_HUMANITARIAN_NEEDS_OR_ENTITLEMENTS_TO_ASSISTANCE = 406,\
            'Access of People in need to Aid/Denial of existence of humanitarian needs or entitlements to assistance'
        ACCESS_OF_PEOPLE_IN_NEED_T0_AID_RESTRICTION_AND_OBSTRUCTION_OF_ACCESS_TO_SERVICES_AND_ASSISTANCE = 407,\
            'Access of People in need to Aid/Restriction and Obstruction of access to services and assistance'
        PHYSICAL_AND_SECURITY_CONSTRAINTS = 408, 'Physical and Security Constraints'
        PHYSICAL_AND_SECURITY_CONSTRAINTS_ONGOING_INSECURITY_HOSTILITIES_AFFECTING_HUMANITARIAN_ASSISTANCE = 409,\
            'Physical and Security Constraints/Ongoing insecurity/hostilities affecting humanitarian assistance'
        PHYSICAL_AND_SECIRITY_CONSTRAINTS_PRESENCE_OF_MINES_AND_IMPROVISED_EXPLOSIVE_DEVICE = 410,\
            'Physical and Security Constraints/Presence of mines and improvised explosive devices'
        PHYSICAL_AND_SECURITY_CONSTRAINTS_PHYSICAL_CONSTRAINTS_IN_THE_ENVIRONMENT = 411,\
            'Physical and Security Constraints/Physical constraints in the environment (\
obstacles related to terrain, climate, lack of infrastructure etc.)'

    summary_focus = models.IntegerField(choices=AssessmentRegistry.FocusType.choices)
    focus_data = models.JSONField(default=None, blank=True, null=True)
    summary_sector = models.IntegerField(choices=AssessmentRegistry.SectorType.choices)
    sector_data = models.JSONField(default=None, blank=True, null=True)
