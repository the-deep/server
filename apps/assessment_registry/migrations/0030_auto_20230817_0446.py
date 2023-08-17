# Generated by Django 3.2.17 on 2023-08-17 04:46

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment_registry', '0029_auto_20230814_0609'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentregistry',
            name='affected_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'All'), (2, 'All/Affected'), (3, 'All/Not Affected'), (4, 'All/Affected/Not Displaced'), (5, 'All/Affected/Displaced'), (6, 'All/Affected/Displaced/In Transit'), (7, 'All/Affected/Displaced/Migrants'), (8, 'All/Affected/Displaced/IDPs'), (9, 'All/Affected/Displced/Asylum Seeker'), (10, 'All/Affected/Displaced/Other of concerns'), (11, 'All/Affected/Displaced/Returnees'), (12, 'All/Affected/Displaced/Refugees'), (13, 'All/Affected/Displaced/Migrants/In transit'), (14, 'All/Affected/Displaced/Migrants/Permanents'), (15, 'All/Affected/Displaced/Migrants/Pendular'), (16, 'All/Affected/Not Displaced/No Host'), (17, 'All/Affected/Not Displaced/Host')]), default=list, size=None),
        ),
        migrations.AlterField(
            model_name='assessmentregistry',
            name='bg_crisis_type',
            field=models.IntegerField(choices=[(1, 'Earth Quake'), (2, 'Ground Shaking'), (3, 'Tsunami'), (4, 'Volcano'), (5, 'Volcanic Eruption'), (6, 'Mass Movement (Dry)'), (7, 'Rockfall'), (8, 'Avalance'), (9, 'Landslide'), (10, 'Subsidence'), (11, 'Extra Tropical Cyclone'), (12, 'Tropical Cyclone'), (13, 'Local/Convective Strom'), (14, 'Flood/Rain'), (15, 'General River Flood'), (16, 'Flash flood'), (17, 'Strom Surge/Coastal Flood'), (18, 'Mass Movement (Wet)'), (19, 'Extreme Temperature'), (20, 'Heat Wave'), (21, 'Cold Wave'), (22, 'Extreme Weather Condition'), (23, 'Drought'), (24, 'Wildfire'), (25, 'Population Displacement'), (26, 'Conflict')]),
        ),
        migrations.AlterField(
            model_name='assessmentregistry',
            name='family',
            field=models.IntegerField(choices=[(1, 'Displacement Traking Matrix'), (2, 'Multi Cluster Initial and Rapid Assessment (MIRA)'), (3, 'Multi sectorial Needs Assessment (MSNA)'), (4, 'Emergency Food Security Assessment (EFSA)'), (5, 'Comprehensive Food Security and Vulnerability Analysis(CFSVA)'), (6, 'Protection Monitoring'), (7, 'Humanitarian Needs Overview (HNO)'), (8, 'Briefing note'), (9, 'Registration'), (10, 'IDPs profiling exercise'), (11, 'Census'), (12, 'Refugee and Migrant Response Plan (RMRP)'), (13, 'Refugee Response Plan (RRP)'), (14, 'Smart Nutrition Survey'), (15, 'Other')]),
        ),
        migrations.AlterField(
            model_name='assessmentregistry',
            name='focuses',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Context'), (2, 'Shock/Event'), (3, 'Displacement'), (4, 'Casualties'), (5, 'Information and Communication'), (6, 'Humaniterian Access'), (7, 'Impact'), (8, 'Humanitarian Conditions'), (9, 'People at risk'), (10, 'Priorities & Preferences'), (11, 'Response and Capacities')]), default=list, size=None),
        ),
        migrations.AlterField(
            model_name='assessmentregistry',
            name='protection_info_mgmts',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Protection Monitoring'), (2, 'Protection Needs Assessment'), (3, 'Case Management'), (4, 'Population Data'), (5, 'Protection Response M&E'), (6, 'Communicating with(in) Affected Communities'), (7, 'Security & Situational Awareness'), (8, 'Sectoral System/Other')]), blank=True, default=list, size=None),
        ),
        migrations.AlterField(
            model_name='assessmentregistry',
            name='sectors',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Food Security'), (2, 'Heath'), (3, 'Shelter'), (4, 'Wash'), (5, 'Protection'), (6, 'Nutrition'), (7, 'Livelihood'), (8, 'Education'), (9, 'Logistics'), (10, 'Inter/Cross Sector')]), default=list, size=None),
        ),
        migrations.AlterField(
            model_name='methodologyattribute',
            name='data_collection_technique',
            field=models.IntegerField(blank=True, choices=[(1, 'Secondary Data Review'), (2, 'Key Informant Interview'), (3, 'Direct Observation'), (4, 'Community Group Discussion'), (5, 'Focus Group Discussion'), (6, 'Household Interview'), (7, 'Individual Interview'), (8, 'Satellite Imagery')], null=True),
        ),
        migrations.AlterField(
            model_name='methodologyattribute',
            name='unit_of_analysis',
            field=models.IntegerField(blank=True, choices=[(1, 'Crisis'), (2, 'Country'), (3, 'Region'), (4, 'Province/governorate/prefecture'), (5, 'Department/District'), (6, 'Sub-District/Country'), (7, 'Municipality'), (8, 'Neighborhood/Quartier'), (9, 'Community/Site'), (10, 'Affected group'), (11, 'Household'), (12, 'Individual')], null=True),
        ),
        migrations.AlterField(
            model_name='methodologyattribute',
            name='unit_of_reporting',
            field=models.IntegerField(blank=True, choices=[(1, 'Crisis'), (2, 'Country'), (3, 'Region'), (4, 'Province/governorate/prefecture'), (5, 'Department/District'), (6, 'Sub-District/Country'), (7, 'Municipality'), (8, 'Neighborhood/Quartier'), (9, 'Community/Site'), (10, 'Affected group'), (11, 'Household'), (12, 'Individual')], null=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='sector',
            field=models.IntegerField(choices=[(1, 'Relevance'), (2, 'Comprehensiveness'), (3, 'Ethics'), (4, 'Methodological rigor'), (5, 'Analytical value'), (6, 'Timeliness'), (7, 'Effective Communication'), (8, 'Use'), (9, 'People-centered and inclusive'), (10, 'Accountability to affected populations'), (11, 'Do not harm'), (12, 'Designed with a purpose'), (13, 'Competency and capacity'), (14, 'Impartiality'), (15, 'Coordination and data minimization'), (16, 'Joint Analysis'), (17, 'Acknowledge dissenting voices in joint needs analysis'), (18, 'Informed consent, confidentiality and data security'), (19, 'Sharing results (data and analysis)'), (20, 'Tranparency between actors'), (21, 'Minimum technical standards')]),
        ),
        migrations.AlterField(
            model_name='question',
            name='sub_sector',
            field=models.IntegerField(choices=[(1, 'Relevance'), (2, 'Geographic comprehensiveness'), (3, 'Sectoral comprehensiveness'), (4, 'Affected and vulnerabel groups comprehensiveness'), (5, 'Safety and protection'), (6, 'Humanitarian Principles'), (7, 'Contribution'), (8, 'Transparency'), (9, 'Mitigating Bias'), (10, 'Participation'), (11, 'Context specificity'), (12, 'Ananlytical standards'), (13, 'Descriptions'), (14, 'Explanation'), (15, 'Interpretation'), (16, 'Anticipation'), (17, 'Timeliness'), (18, 'User-friendly presentation'), (19, 'Active dissemination'), (20, 'Use for collective planning'), (21, 'Buy-in and use by humanitarian clusters/sectors'), (22, 'Buy-in and use by UN agencies'), (23, 'Buy-in and use by international non-governmental organizations (NGOs)'), (24, 'Buy-in and use by local non-governmental organization (local NGOs)'), (25, 'Buy-in and use by member of Red Cross/Red Cresent Movement'), (26, 'Buy-in and use by donors'), (27, 'Buy-in and use by naional and local government agencies'), (28, 'Buy-in and use by development and stabilization actors')]),
        ),
        migrations.AlterField(
            model_name='scoreanalyticaldensity',
            name='analysis_level_covered',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Issues/unmet needs are detailed'), (2, 'Issues/unmet needs are priotized/ranked'), (3, 'Causes or underlying mechanisms behind issues/unmet needs are detailed'), (4, 'Causes or underlying mechanisms behind issues/unmet needs are priotized/ranked'), (5, 'Severity of some/all issues/unmet_needs_is_detailed'), (6, 'Future issues/unmet needs are detailed'), (7, 'Future issues/unmet needs are priotized/ranked'), (8, 'Severity of some/all future issues/unmet_needs_is_detailed'), (9, 'Recommnedations/interventions are detailed'), (10, 'Recommnedations/interventions are priotized/ranked')]), default=list, size=None),
        ),
        migrations.AlterField(
            model_name='scoreanalyticaldensity',
            name='figure_provided',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Total population in the assessed areas'), (2, 'Total population exposed to the shock/event'), (3, 'Total populaiton affected/living in the affected area'), (4, 'Total population facing humanitarian access constraints'), (5, 'Total populaiton in need'), (6, 'Total population in critical need'), (7, 'Total population in severe need'), (8, 'Total population in moderate need'), (9, 'Total population at risk/vulnerable'), (10, 'Total population reached by assistance')]), default=list, size=None),
        ),
        migrations.AlterField(
            model_name='scoreanalyticaldensity',
            name='sector',
            field=models.IntegerField(choices=[(1, 'Food Security'), (2, 'Heath'), (3, 'Shelter'), (4, 'Wash'), (5, 'Protection'), (6, 'Nutrition'), (7, 'Livelihood'), (8, 'Education'), (9, 'Logistics'), (10, 'Inter/Cross Sector')]),
        ),
        migrations.AlterField(
            model_name='scorerating',
            name='score_type',
            field=models.IntegerField(choices=[(1, 'Relevance'), (2, 'Comprehensiveness'), (3, 'Timeliness'), (4, 'Granularity'), (5, 'Comparability'), (6, 'Source reability'), (7, 'Methods'), (8, 'Triangulation'), (9, 'Plausibility'), (10, 'Inclusiveness'), (11, 'Assumptions'), (12, 'Corroboration'), (13, 'Structured Ananlytical Technique'), (14, 'Consensus'), (15, 'Reproducibility'), (16, 'Clearly Articulated Result'), (17, 'Level Of Confidence'), (18, 'Illustration'), (19, 'Sourced data and evidence'), (20, 'Clearly stated outliers')]),
        ),
        migrations.AlterField(
            model_name='summaryfocus',
            name='focus',
            field=models.IntegerField(choices=[(1, 'Food Security'), (2, 'Heath'), (3, 'Shelter'), (4, 'Wash'), (5, 'Protection'), (6, 'Nutrition'), (7, 'Livelihood'), (8, 'Education'), (9, 'Logistics'), (10, 'Inter/Cross Sector')]),
        ),
        migrations.AlterField(
            model_name='summaryissue',
            name='sub_dimmension',
            field=models.IntegerField(blank=True, choices=[(1, 'Drivers'), (2, 'Impact on People'), (3, 'Impact On System, Network And Services'), (4, 'Living Standards'), (5, 'Coping Mechanisms'), (6, 'Physical And Mental Well Being'), (7, 'Needs (Population)'), (8, 'Needs (Humanitarian)'), (9, 'Interventions (Population)'), (10, 'Interventions (Humanitarian)'), (11, 'Demographic Groups'), (12, 'Groups With Specific Needs'), (13, 'Geographical Areas'), (14, 'People At Risks'), (15, 'Focal Issues')], null=True),
        ),
        migrations.AlterField(
            model_name='summaryissue',
            name='sub_pillar',
            field=models.IntegerField(blank=True, choices=[(1, 'Politics'), (2, 'Demography'), (3, 'Socio-Cultural'), (4, 'Environment'), (5, 'Security & Stability'), (6, 'Economics'), (7, 'Characteristics'), (8, 'Drivers and Aggravating Factors'), (9, 'Mitigating Factors'), (10, 'Hazards & Threats'), (11, 'Characteristics'), (12, 'Push Factors'), (13, 'Pull Factors'), (14, 'Intentions'), (15, 'Local Integrations'), (16, 'Source & Means'), (17, 'Challanges & Barriers'), (18, 'Knowledge & Info Gaps (Humanitarian)'), (19, 'Knowledge & Info Gaps (Population)'), (20, 'Population To Relief'), (21, 'Relief To Population'), (22, 'Physical & Security')], null=True),
        ),
        migrations.AlterField(
            model_name='summarysubdimmensionissue',
            name='focus',
            field=models.IntegerField(choices=[(1, 'Food Security'), (2, 'Heath'), (3, 'Shelter'), (4, 'Wash'), (5, 'Protection'), (6, 'Nutrition'), (7, 'Livelihood'), (8, 'Education'), (9, 'Logistics'), (10, 'Inter/Cross Sector')]),
        ),
    ]
