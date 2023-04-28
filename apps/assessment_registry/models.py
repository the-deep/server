from django.db import models
from django.contrib.postgres.fields import ArrayField

from user_resource.models import UserResource
from geo.models import Region
from organization.models import Organization
from gallery.models import File


class AssessmentRegistry(UserResource):
    class CrisisType(models.IntegerChoices):  # NOTE: Here the values are selected as per the pk value in deep data to make it easier during data migration
        EARTH_QUAKE = 1, 'Earth Quake'
        GROUND_SHAKING = 2, 'Ground Shaking'
        TSUNAMI = 3, 'Tsunami'
        VOLCANO = 4, 'Volcano'
        VOLCANIC_ERUPTION = 5, 'Volcanic Eruption'
        MASS_MOMENT_DRY = 6, 'Mass Movement (Dry)'
        ROCK_FALL = 7, 'Rockfall'
        AVALANCE = 8, 'Avalance'
        LANDSLIDE = 9, 'Landslide'
        SUBSIDENCE = 10, 'Subsidence'
        # EXTRA_TROPICAL_CYCLONE = 11, 'Extra Tropical Cyclone'
        TROPICAL_CYCLONE = 12, 'Tropical Cyclone'
        LOCAL_STROM = 13, 'Local/Convective Strom'
        EXTRA_TROPICAL_CYCLONE = 14, 'Extra Tropical Cyclone'
        FLOOD_RAIN = 15, 'Flood/Rain'
        GENERAL_RIVER_FLOOD = 16, 'General River Flood'
        FLASH_FLOOD = 17, 'Flash flood'
        STROM_SURGE_FLOOD = 18, 'Strom Surge/Coastal Flood'
        MASS_MOVEMENT_WET = 19, 'Mass Movement (Wet)'
        EXTREME_TEMPERATURE = 20, 'Extreme Temperature'
        HEAT_WAVE = 21, 'Heat Wave'
        COLD_WAVE = 22, 'Cold Wave'
        EXTREME_WEATHER_CONDITION = 23, 'Extreme Weather Condition'
        DROUGHT = 24, 'Drought'
        WILDFIRE = 25, 'Wildfire'
        POPULATION_DISPLACEMENT = 112, 'Population Displacement'
        CONFLICT = 79, 'Conflict'

    class PreparednessType(models.IntegerChoices):
        WITH_PREPAREDNESS = 26, 'With Preparedness'
        WITHOUT_PREPAREDNESS = 27, 'Without Preparedness'

    class ExternalSupportType(models.IntegerChoices):
        EXTERNAL_SUPPORT_RECIEVED = 29, 'External Support Received'
        NO_EXTERNAL_SUPPORT_RECEIVED = 30, 'No External Support Received'

    class CoordinationType(models.IntegerChoices):
        COORDINATED = 37, 'Coordinated Joint'
        HARMONIZED = 38, 'Coordinated Harmonized'
        UNCOORDINATED = 39, 'Uncoordinated'

    class Type(models.IntegerChoices):
        INITIAL = 67, 'Initial'
        RAPID = 65, 'Rapid'
        IN_DEPTH = 64, 'In depth'
        MONITORING = 68, 'Monitoring'
        OTHER = 72, 'Other'

    class FamilyType(models.IntegerChoices):
        DISPLACEMENT_TRAKING_MATRIX = 74, 'Displacement Traking Matrix'
        MULTI_CLUSTER_INITIAL_AND_RAPID_ASSESSMENT = 75, 'Multi Cluster Initial and Rapid Assessment (MIRA)'
        MULTI_SECTORIAL_NEEDS_ASSESSMENT = 76, 'Multi sectorial Needs Assessment (MSNA)'
        EMERGENCY_FOOD_SECURITY_ASSESSMENT = 77, 'Emergency Food Security Assessment (EFSA)'
        COMPREHENSIVE_FOOD_SECURITY_AND_VULNERABILITY_ANALYSIS = \
            78, 'Comprehensive Food Security and Vulnerability Analysis(CFSVA)'
        PROTECTION_MONITORING = 113, 'Protection Monitoring'
        HUMANITARIAN_NEEDS_OVERVIEW = 145, 'Humanitarian Needs Overview (HNO)'
        BRIEFING_NOTE = 147, 'Briefing note'
        REGISTRATION = 149, 'Registration'
        IDP_PROFILING_EXERCISE = 178, 'IDPs profiling exercise'
        CENSUS = 179, 'Census'
        REFUGEE_AND_MIGRANT_RESPONSE_PLAN = 212, 'Refugee and Migrant Response Plan (RMRP)'
        RUFUGEE_RESPONSE_PLAN = 213, 'Refugee Response Plan (RRP)'
        SMART_NUTRITION_SURVEY = 214, 'Smart Nutrition Survey'
        OTHER = 277, 'Other'

    class FrequencyType(models.IntegerChoices):
        ONE_OFF = 56, 'One off'
        REGULAR = 57, 'Regular'

    class ConfidentialityType(models.IntegerChoices):
        UNPROTECTED = 58, 'Unprotected'
        CONFIDENTIAL = 73, 'Confidential'

    class Language(models.IntegerChoices):
        ENGLISH = 61, 'English'
        FRENCH = 62, 'French'
        SPANISH = 63, 'Spanish'
        PORTUGESE = 146, 'Portugese'
        ARABIC = 66, 'Arabic'

    class FocusType(models.IntegerChoices):
        CONTEXT = 74, 'Context'
        SHOCK_EVENT = 75, 'Shock/Event'
        DISPLACEMENT = 42, 'Displacement'
        HUMANITERIAN_ACCESS = 8, 'Humaniterian Access'
        INFORMATION_AND_COMMUNICATION = 41, 'Information and Communication'
        IMPACT = 9, 'Impact (Scope and Scale)'
        HUMANITARIAN_CONDITIONS = 10, 'Humanitarian Conditions'
        RESPONSE_AND_CAPACITIES = 11, 'Response and Capacities'
        CURRENT_AND_FORECASTED_PRIORITIES = 76, 'Current and Forecasted Priorities'
        COVID_19_CONTAINMENT_MEASURES = 107, 'Covid 19 Conntainment Measures'

    # Metadata Group
    # Background Fields
    bg_countries = models.ManyToManyField(Region)
    bg_crisis_type = models.IntegerField(choices=CrisisType.choices)
    bg_crisis_start_date = models.DateField()
    bg_preparedness = models.IntegerField(choices=PreparednessType.choices)
    external_support = models.IntegerField(choices=ExternalSupportType.choices)
    coordinated_joint = models.IntegerField(choices=CoordinationType.choices)
    cost_estimates_usd = models.IntegerField(null=True, blank=True)

    # Details Field
    detials_type = models.IntegerField(choices=Type.choices)
    family = models.IntegerField(choices=FamilyType.choices)
    frequency = models.IntegerField(choices=FrequencyType.choices)
    confidentiality = models.IntegerField(choices=ConfidentialityType.choices)
    language = ArrayField(models.IntegerField(choices=Language.choices))
    no_of_pages = models.IntegerField(null=True, blank=True)

    # Dates
    data_collection_start_date = models.DateField(null=True, blank=True)
    data_collection_end_date = models.DateField(null=True, blank=True)
    publishcation_date = models.DateField(null=True, blank=True)

    # Stakeholders
    lead_organization = models.ManyToManyField(Organization, related_name='lead_org_assessment_reg')
    international_partners = models.ManyToManyField(Organization, related_name='int_partners_assessment_reg')
    donor = models.ManyToManyField(Organization, related_name='donor_assessment_reg')
    national_partners = models.ManyToManyField(Organization, related_name='national_partner_assessment_reg')
    government = models.ManyToManyField(Organization, related_name='gov_assessment_reg')

    # Focus
    # Focus Sectors
    # focuses = models.IntegerField(choices=FocusType.choices)
    # sectors = models.IntegerField(choices=SectorType.choices)
    # protection_info_mgmt = models.IntegerField(choices=ProtectionInfoType.choices)
    # affected_group = models.IntegerField(choices=AffectedGroupType.choices)
    location = models.ManyToManyField(Region, related_name='focus_location_assessment_reg')


class AdditionalDocument(UserResource):
    class DocumentType(models.IntegerChoices):
        EXECUTIVE_SUMMARY = 1000, 'Executive summary'
        ASSESSMENT_DATABASE = 1001, 'Assessment database'
        QUESTIONAIRE = 1002, 'Questionaire'
        MISCELLANESOUS = 1003, 'Miscellaneous'

    assessment_registry = models.ForeignKey(
        AssessmentRegistry,
        on_delete=models.CASCADE,
        related_name='assessment_reg_add_document',
    )
    document_type = models.IntegerField(choices=DocumentType.choices)
    file = models.ForeignKey(
        File,
        on_delete=models.SET_NULL,
        related_name='assessment_reg_file',
        null=True, blank=True
    )
    external_link = models.TextField(blank=True)


