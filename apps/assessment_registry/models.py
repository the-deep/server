from django.db import models
from apps.user_resource.models import UserResource
from apps.geo.models import Region
from apps.organization.models import Organization
# Create your models here.


class Assessment_Registry(UserResource):
    class CrisisType(models.IntegerChoice):
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
        EXTRA_TROPICAL_CYCLONE = 11, 'Extra Tropical Cyclone'
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

    class PreparednessType(models.IntegerChoice):
        WITH_PREPAREDNESS = 26, 'With Preparedness'
        WITHOUT_PREPAREDNESS = 27, 'Without Preparedness'

    class ExternalSupportType(models.IntegerChoice):
        EXTERNAL_SUPPORT_RECIEVED = 29, 'External Support Received'
        NO_EXTERNAL_SUPPORT_RECEIVED = 30, 'No External Support Received'

    class CoordinationType(models.IntegerChoice):
        COORDINATED = 37, 'Coordinated Joint'
        HARMONIZED = 38, 'Coordinated Harmonized'
        UNCOORDINATED = 39, 'Uncoordinated'

    class Type(models.IntegerChoice):
        INITIAL = 67, 'Initial'
        RAPID = 65, 'Rapid'
        IN_DEPTH = 64, 'In depth'
        MONITORING = 68, 'Monitoring'
        OTHER = 72, 'Other'

    class FamilyType(models.IntegerChoice):
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

    class FrequencyType(models.IntegerChoice):
        ONE_OFF = 56, 'One off'
        REGULAR = 57, 'Regular'

    class ConfidentialityType(models.IntegerField):
        UNPROTECTED = 58, 'Unprotected'
        CONFIDENTIAL = 73, 'Confidential'

    class Language(models.IntegerChoice):
        ENGLISH = 61, 'English'
        FRENCH = 62, 'French'
        SPANISH = 63, 'Spanish'
        PORTUGESE = 146, 'Portugese'
        ARABIC = 66, 'Arabic'

    # Metadata
    # Metadata
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
    language = models.ArrayField(choices=Language.choices)
    no_of_pages = models.IntegerField(null=True, blank=True)

    # Dates
    data_collection_start_date = models.DateField(null=True, blank=True)
    data_collection_end_date = models.DateField(null=True, blank=True)
    publishcation_date = models.DateField(null=True, blank=True)

    # Stakeholders
    lead_organization = models.ManyToManyField(Organization)
    international_partners = models.ManyToManyField(Organization)
    donor = models.ManyToManyField(Organization)
    national_partners = models.ManyToManyField(Organization)
    government = models.ManyToManyField(Organization)
