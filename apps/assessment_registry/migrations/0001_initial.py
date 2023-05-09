# Generated by Django 3.2.17 on 2023-07-13 10:37

from django.conf import settings
import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('geo', '0041_geoarea_centroid'),
        ('organization', '0012_organization_popularity'),
        ('lead', '0048_auto_20230228_0810'),
        ('gallery', '0020_merge_0019_auto_20210120_0443_0019_auto_20210503_0431'),
        ('project', '0003_auto_20230508_0608'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssessmentRegistry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('bg_crisis_type', models.IntegerField(choices=[(0, 'Earth Quake'), (1, 'Ground Shaking'), (2, 'Tsunami'), (3, 'Volcano'), (4, 'Volcanic Eruption'), (5, 'Mass Movement (Dry)'), (6, 'Rockfall'), (7, 'Avalance'), (8, 'Landslide'), (9, 'Subsidence'), (10, 'Extra Tropical Cyclone'), (11, 'Tropical Cyclone'), (12, 'Local/Convective Strom'), (13, 'Flood/Rain'), (14, 'General River Flood'), (15, 'Flash flood'), (16, 'Strom Surge/Coastal Flood'), (17, 'Mass Movement (Wet)'), (18, 'Extreme Temperature'), (19, 'Heat Wave'), (20, 'Cold Wave'), (21, 'Extreme Weather Condition'), (22, 'Drought'), (23, 'Wildfire'), (24, 'Population Displacement'), (25, 'Conflict')])),
                ('bg_crisis_start_date', models.DateField()),
                ('bg_preparedness', models.IntegerField(choices=[(0, 'With Preparedness'), (1, 'Without Preparedness')])),
                ('external_support', models.IntegerField(choices=[(0, 'External Support Received'), (1, 'No External Support Received')])),
                ('coordinated_joint', models.IntegerField(choices=[(0, 'Coordinated Joint'), (1, 'Coordinated Harmonized'), (2, 'Uncoordinated')])),
                ('cost_estimates_usd', models.IntegerField(blank=True, null=True)),
                ('details_type', models.IntegerField(choices=[(0, 'Initial'), (1, 'Rapid'), (2, 'In depth'), (3, 'Monitoring'), (4, 'Other')])),
                ('family', models.IntegerField(choices=[(0, 'Displacement Traking Matrix'), (1, 'Multi Cluster Initial and Rapid Assessment (MIRA)'), (2, 'Multi sectorial Needs Assessment (MSNA)'), (3, 'Emergency Food Security Assessment (EFSA)'), (4, 'Comprehensive Food Security and Vulnerability Analysis(CFSVA)'), (5, 'Protection Monitoring'), (6, 'Humanitarian Needs Overview (HNO)'), (7, 'Briefing note'), (8, 'Registration'), (9, 'IDPs profiling exercise'), (10, 'Census'), (11, 'Refugee and Migrant Response Plan (RMRP)'), (12, 'Refugee Response Plan (RRP)'), (13, 'Smart Nutrition Survey'), (14, 'Other')])),
                ('frequency', models.IntegerField(choices=[(0, 'One off'), (1, 'Regular')])),
                ('confidentiality', models.IntegerField(choices=[(0, 'Unprotected'), (1, 'Confidential')])),
                ('language', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(0, 'English'), (1, 'French'), (2, 'Spanish'), (3, 'Portugese'), (4, 'Arabic')]), size=None)),
                ('no_of_pages', models.IntegerField(blank=True, null=True)),
                ('data_collection_start_date', models.DateField(blank=True, null=True)),
                ('data_collection_end_date', models.DateField(blank=True, null=True)),
                ('publication_date', models.DateField(blank=True, null=True)),
                ('objectives', models.TextField(blank=True, null=True)),
                ('data_collection_techniques', models.TextField(blank=True, null=True)),
                ('sampling', models.TextField(blank=True, null=True)),
                ('limitations', models.TextField(blank=True, null=True)),
                ('focuses', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, choices=[(0, 'Context'), (1, 'Shock/Event'), (2, 'Displacement'), (3, 'Casualties'), (4, 'Information and Communication'), (5, 'Humaniterian Access'), (6, 'Impact'), (7, 'Humanitarian Conditions'), (8, 'People at risk'), (9, 'Priorities & Preferences'), (10, 'Response and Capacities')], null=True), size=None)),
                ('sectors', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, choices=[(0, 'Food Security'), (1, 'Heath'), (2, 'Shelter'), (3, 'Wash'), (4, 'Protection'), (5, 'Nutrition'), (6, 'Livelihood'), (7, 'Education'), (8, 'Logistics'), (9, 'Inter/Cross Sector')], null=True), size=None)),
                ('protection_info_mgmts', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, choices=[(0, 'Protection Monitoring'), (1, 'Protection Needs Assessment'), (2, 'Case Management'), (3, 'Population Data'), (4, 'Protection Response M&E'), (5, 'Communicating with(in) Affected Communities'), (6, 'Security & Situational Awareness'), (7, 'Sectoral System/Other')], null=True), size=None)),
                ('affected_groups', models.IntegerField(blank=True, choices=[(0, 'All'), (1, 'All/Affected'), (2, 'All/Not Affected'), (3, 'All/Affected/Not Displaced'), (4, 'All/Affected/Displaced'), (5, 'All/Affected/Displaced/In Transit'), (6, 'All/Affected/Displaced/Migrants'), (7, 'All/Affected/Displaced/IDPs'), (8, 'All/Affected/Displced/Asylum Seeker'), (9, 'All/Affected/Displaced/Other of concerns'), (10, 'All/Affected/Displaced/Returnees'), (11, 'All/Affected/Displaced/Refugees'), (12, 'All/Affected/Displaced/Migrants/In transit'), (13, 'All/Affected/Displaced/Migrants/Permanents'), (14, 'All/Affected/Displaced/Migrants/Pendular'), (15, 'All/Affected/Not Displaced/No Host'), (16, 'All/Affected/Not Displaced/Host')], null=True)),
                ('matrix_score', models.IntegerField(default=0)),
                ('final_score', models.IntegerField(default=0)),
                ('bg_countries', models.ManyToManyField(to='geo.Region')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assessmentregistry_created', to=settings.AUTH_USER_MODEL)),
                ('donors', models.ManyToManyField(blank=True, related_name='donor_assessment_reg', to='organization.Organization')),
                ('governments', models.ManyToManyField(blank=True, related_name='gov_assessment_reg', to='organization.Organization')),
                ('international_partners', models.ManyToManyField(blank=True, related_name='int_partners_assessment_reg', to='organization.Organization')),
                ('lead', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='lead.lead')),
                ('lead_organizations', models.ManyToManyField(blank=True, related_name='lead_org_assessment_reg', to='organization.Organization')),
                ('locations', models.ManyToManyField(blank=True, related_name='focus_location_assessment_reg', to='geo.Region')),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assessmentregistry_modified', to=settings.AUTH_USER_MODEL)),
                ('national_partners', models.ManyToManyField(blank=True, related_name='national_partner_assessment_reg', to='organization.Organization')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='SummaryIssue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sub_sector', models.IntegerField(blank=True, choices=[(0, 'Politics'), (1, 'Demography'), (2, 'Socio-Cultural'), (3, 'Environment'), (4, 'Security & Stability'), (5, 'Economics'), (6, 'Characteristics'), (7, 'Drivers and Aggravating Factors'), (8, 'Mitigating Factors'), (9, 'Hazards & Threats'), (10, 'Characteristics'), (11, 'Push Factors'), (12, 'Pull Factors'), (13, 'Intentions'), (14, 'Local Integrations'), (15, 'Source & Means'), (16, 'Challanges & Barriers'), (17, 'Knowledge & Info Gaps (Humanitarian)'), (18, 'Knowledge & Info Gaps (Population)'), (19, 'Population To Relief'), (20, 'Relief To Population'), (21, 'Physical & Security')], null=True)),
                ('focus_sub_sector', models.IntegerField(blank=True, choices=[(0, 'Drivers'), (1, 'Impact on People'), (2, 'Impact On System, Network And Services'), (3, 'Living Standards'), (4, 'Coping Mechanisms'), (5, 'Physical And Mental Well Being'), (6, 'Needs (Population)'), (7, 'Needs (Humanitarian)'), (8, 'Interventions (Population)'), (9, 'Interventions (Humanitarian)'), (10, 'Demographic Groups'), (11, 'Groups With Specific Needs'), (12, 'Geographical Areas'), (13, 'People At Risks'), (14, 'Focal Issues')], null=True)),
                ('label', models.CharField(max_length=220)),
                ('full_label', models.CharField(blank=True, max_length=220)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='assessment_registry.summaryissue')),
            ],
        ),
        migrations.CreateModel(
            name='SummarySubSectorIssue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('text', models.TextField(blank=True)),
                ('order', models.IntegerField(blank=True, null=True)),
                ('lead_preview_text_ref', models.JSONField(blank=True, default=None, null=True)),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summary_sub_sector_issue_ary', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='summarysubsectorissue_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='summarysubsectorissue_modified', to=settings.AUTH_USER_MODEL)),
                ('summary_issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summary_subsector_issue', to='assessment_registry.summaryissue')),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SummaryFocusSubSectorIssue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('focus', models.IntegerField(choices=[(0, 'Food Security'), (1, 'Heath'), (2, 'Shelter'), (3, 'Wash'), (4, 'Protection'), (5, 'Nutrition'), (6, 'Livelihood'), (7, 'Education'), (8, 'Logistics'), (9, 'Inter/Cross Sector')])),
                ('text', models.TextField(blank=True)),
                ('order', models.IntegerField(blank=True, null=True)),
                ('lead_preview_text_ref', models.JSONField(blank=True, default=None, null=True)),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summary_focus_subsector_issue_ary', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='summaryfocussubsectorissue_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='summaryfocussubsectorissue_modified', to=settings.AUTH_USER_MODEL)),
                ('summary_issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summary_focus_subsector_issue', to='assessment_registry.summaryissue')),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SummaryFocus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('percentage_of_people_affected', models.IntegerField(blank=True, null=True)),
                ('total_people_affected', models.IntegerField(blank=True, null=True)),
                ('percentage_of_moderate', models.IntegerField(blank=True, null=True)),
                ('percentage_of_severe', models.IntegerField(blank=True, null=True)),
                ('percentage_of_critical', models.IntegerField(blank=True, null=True)),
                ('percentage_in_need', models.IntegerField(blank=True, null=True)),
                ('total_moderate', models.IntegerField(blank=True, null=True)),
                ('total_severe', models.IntegerField(blank=True, null=True)),
                ('total_critical', models.IntegerField(blank=True, null=True)),
                ('total_in_need', models.IntegerField(blank=True, null=True)),
                ('total_pop_assessed', models.IntegerField(blank=True, null=True)),
                ('total_not_affected', models.IntegerField(blank=True, null=True)),
                ('total_affected', models.IntegerField(blank=True, null=True)),
                ('total_people_in_need', models.IntegerField(blank=True, null=True)),
                ('total_people_moderately_in_need', models.IntegerField(blank=True, null=True)),
                ('total_people_severly_in_need', models.IntegerField(blank=True, null=True)),
                ('total_people_critically_in_need', models.IntegerField(blank=True, null=True)),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summary_focus', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='summaryfocus_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='summaryfocus_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Summary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('total_people_assessed', models.IntegerField(blank=True, null=True)),
                ('total_dead', models.IntegerField(blank=True, null=True)),
                ('total_injured', models.IntegerField(blank=True, null=True)),
                ('total_missing', models.IntegerField(blank=True, null=True)),
                ('total_people_facing_hum_access_cons', models.IntegerField(blank=True, null=True)),
                ('percentage_of_people_facing_hum_access_cons', models.IntegerField(blank=True, null=True)),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='summary', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='summary_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='summary_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ScoreRating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('score_type', models.IntegerField(choices=[(0, 'Fit for purpose -> Relevance'), (1, 'Fit for purpose -> Comprehensiveness'), (2, 'Fit for purpose -> Timeliness'), (3, 'Fit for purpose -> Granularity'), (4, 'Fit for purpose -> Comparability'), (5, 'Trustworthiness -> Source reability'), (6, 'Trustworthiness -> Methods'), (7, 'Trustworthiness -> Triangulation'), (8, 'Trustworthiness -> Plausibility'), (9, 'Trustworthiness - Inclusiveness'), (10, 'Analytical rigor -> Assumptions'), (11, 'Analytical rigor -> Corroboration'), (12, 'Analytical rigor -> Structured Ananlytical Technique'), (13, 'Analytical rigor > Consensus'), (14, 'Analytical rigor -> Reproducibility'), (15, 'Analytical Writing -> Clearly Articulated Result'), (16, 'Analytical writing -> Level Of Confidence'), (17, 'Analytical writing -> Illustration'), (18, 'Analytical writing -> Sourced data and evidence'), (19, 'Analytical writing -> Clearly stated outliers')])),
                ('rating', models.IntegerField(choices=[(1, 'Very poor'), (2, 'Poor'), (3, 'Fair'), (4, 'Good'), (5, 'Very Good')], default=3)),
                ('reason', models.TextField(blank=True, null=True)),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='score_ratings', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scorerating_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scorerating_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ScoreAnalyticalDensity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('sector', models.IntegerField(choices=[(0, 'Food Security'), (1, 'Heath'), (2, 'Shelter'), (3, 'Wash'), (4, 'Protection'), (5, 'Nutrition'), (6, 'Livelihood'), (7, 'Education'), (8, 'Logistics'), (9, 'Inter/Cross Sector')])),
                ('value', models.IntegerField(validators=[django.core.validators.MaxValueValidator(49), django.core.validators.MinValueValidator(1)])),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analytical_density', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scoreanalyticaldensity_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='scoreanalyticaldensity_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('sector', models.IntegerField(choices=[(0, 'Relevance'), (1, 'Comprehensiveness'), (2, 'Ethics'), (3, 'Methodological rigor'), (4, 'Analytical value'), (5, 'Timeliness'), (6, 'Effective Communication'), (7, 'Use'), (8, 'People-centered and inclusive'), (9, 'Accountability to affected populations'), (10, 'Do not harm'), (11, 'Designed with a purpose'), (12, 'Competency and capacity'), (13, 'Impartiality'), (14, 'Coordination and data minimization'), (15, 'Joint Analysis'), (16, 'Acknowledge dissenting voices in joint needs analysis'), (17, 'Informed consent, confidentiality and data security'), (18, 'Sharing results (data and analysis)'), (19, 'Tranparency between actors'), (20, 'Minimum technical standards')])),
                ('sub_sector', models.IntegerField(choices=[(0, 'Relevance'), (1, 'Geographic comprehensiveness'), (2, 'Sectoral comprehensiveness'), (3, 'Affected and vulnerabel groups comprehensiveness'), (4, 'Safety and protection'), (5, 'Humanitarian Principles'), (6, 'Contribution'), (7, 'Transparency'), (8, 'Mitigating Bias'), (9, 'Participation'), (10, 'Context specificity'), (11, 'Ananlytical standards'), (12, 'Descriptions'), (13, 'Explanation'), (14, 'Interpretation'), (15, 'Anticipation'), (16, 'Timeliness'), (17, 'User-friendly presentation'), (18, 'Active dissemination'), (19, 'Use for collective planning'), (20, 'Buy-in and use by humanitarian clusters/sectors'), (21, 'Buy-in and use by UN agencies'), (22, 'Buy-in and use by international non-governmental organizations (NGOs)'), (23, 'Buy-in and use by local non-governmental organization (local NGOs)'), (24, 'Buy-in and use by member of Red Cross/Red Cresent Movement'), (25, 'Buy-in and use by donors'), (26, 'Buy-in and use by naional and local government agencies'), (27, 'Buy-in and use by development and stabilization actors')])),
                ('question', models.CharField(max_length=500)),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='question_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='question_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='MethodologyAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('data_collection_technique', models.IntegerField(blank=True, choices=[(0, 'Secondary Data Review'), (1, 'Key Informant Interview'), (2, 'Direct Observation'), (3, 'Community Group Discussion'), (4, 'Focus Group Discussion'), (5, 'Household Interview'), (6, 'Individual Interview'), (7, 'Satellite Imagery')], null=True)),
                ('sampling_approach', models.IntegerField(blank=True, choices=[(0, 'Non-Random Selection'), (1, 'Random Selection'), (2, 'Full Enumeration')], null=True)),
                ('sampling_size', models.IntegerField(blank=True, null=True)),
                ('proximity', models.IntegerField(blank=True, choices=[(0, 'Face-to-Face'), (1, 'Remote'), (2, 'Mixed')], null=True)),
                ('unit_of_analysis', models.IntegerField(blank=True, choices=[(0, 'Crisis'), (1, 'Country'), (2, 'Region'), (3, 'Province/governorate/prefecture'), (4, 'Department/District'), (5, 'Sub-District/Country'), (6, 'Municipality'), (7, 'Neighborhood/Quartier'), (8, 'Community/Site'), (9, 'Affected group'), (10, 'Household'), (11, 'Individual')], null=True)),
                ('unit_of_reporting', models.IntegerField(blank=True, choices=[(0, 'Crisis'), (1, 'Country'), (2, 'Region'), (3, 'Province/governorate/prefecture'), (4, 'Department/District'), (5, 'Sub-District/Country'), (6, 'Municipality'), (7, 'Neighborhood/Quartier'), (8, 'Community/Site'), (9, 'Affected group'), (10, 'Household'), (11, 'Individual')], null=True)),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='methodology_attributes', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='methodologyattribute_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='methodologyattribute_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AdditionalDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('document_type', models.IntegerField(choices=[(0, 'Executive summary'), (1, 'Assessment database'), (2, 'Questionnaire'), (3, 'Miscellaneous')])),
                ('external_link', models.TextField(blank=True)),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_documents', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='additionaldocument_created', to=settings.AUTH_USER_MODEL)),
                ('file', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assessment_reg_file', to='gallery.file')),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='additionaldocument_modified', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('client_id', models.CharField(blank=True, default=None, max_length=128, null=True, unique=True)),
                ('answer', models.BooleanField()),
                ('assessment_registry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer', to='assessment_registry.assessmentregistry')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='answer_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='answer_modified', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assessment_registry.question')),
            ],
            options={
                'ordering': ['id'],
                'unique_together': {('assessment_registry', 'question')},
            },
        ),
    ]