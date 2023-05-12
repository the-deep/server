# Generated by Django 3.2.17 on 2023-05-16 10:33

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('geo', '0041_geoarea_centroid'),
        ('lead', '0048_auto_20230228_0810'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('gallery', '0020_merge_0019_auto_20210120_0443_0019_auto_20210503_0431'),
        ('project', '0002_projectchangelog'),
        ('organization', '0012_organization_popularity'),
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
                ('focuses', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, choices=[(0, 'Context'), (1, 'Shock/Event'), (2, 'Displacement'), (3, 'Humaniterian Access'), (4, 'Information and Communication'), (5, 'Impact (Scope and Scale)'), (6, 'Humanitarian Conditions'), (7, 'Response and Capacities'), (8, 'Current and Forecasted Priorities'), (9, 'Covid 19 Conntainment Measures')], null=True), size=None)),
                ('sectors', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, choices=[(0, 'Food'), (1, 'Heath'), (2, 'Shelter'), (3, 'Wash'), (4, 'Protection'), (5, 'Nutrition'), (6, 'Livelihood'), (7, 'Education'), (8, 'Child protection'), (9, 'Gender Based Violence')], null=True), size=None)),
                ('protection_info_mgmts', django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, choices=[(0, 'Protection Monitoring'), (1, 'Protection Needs Assessment'), (2, 'Case Management'), (3, 'Population Data'), (4, 'Protection Response M&E'), (5, 'Communicating with(in) Affected Communities'), (6, 'Security & Situational Awareness'), (7, 'Sectoral System/Other')], null=True), size=None)),
                ('affected_groups', models.IntegerField(blank=True, choices=[(0, 'All'), (1, 'All/Affected'), (2, 'All/Not Affected'), (3, 'All/Affected/Not Displaced'), (4, 'All/Affected/Displaced'), (5, 'All/Affected/Displaced/In Transit'), (6, 'All/Affected/Displaced/Migrants'), (7, 'All/Affected/Displaced/IDPs'), (8, 'All/Affected/Displced/Asylum Seeker'), (9, 'All/Affected/Displaced/Other of concerns'), (10, 'All/Affected/Displaced/Returnees'), (11, 'All/Affected/Displaced/Refugees'), (12, 'All/Affected/Displaced/Migrants/In transit'), (13, 'All/Affected/Displaced/Migrants/Permanents'), (14, 'All/Affected/Displaced/Migrants/Pendular'), (15, 'All/Affected/Not Displaced/No Host'), (16, 'All/Affected/Not Displaced/Host')], null=True)),
                ('bg_countries', models.ManyToManyField(to='geo.Region')),
                ('created_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assessmentregistry_created', to=settings.AUTH_USER_MODEL)),
                ('donors', models.ManyToManyField(related_name='donor_assessment_reg', to='organization.Organization')),
                ('governments', models.ManyToManyField(related_name='gov_assessment_reg', to='organization.Organization')),
                ('international_partners', models.ManyToManyField(related_name='int_partners_assessment_reg', to='organization.Organization')),
                ('lead', models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='lead.lead')),
                ('lead_group', models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='lead.leadgroup')),
                ('lead_organizations', models.ManyToManyField(related_name='lead_org_assessment_reg', to='organization.Organization')),
                ('locations', models.ManyToManyField(related_name='focus_location_assessment_reg', to='geo.Region')),
                ('modified_by', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assessmentregistry_modified', to=settings.AUTH_USER_MODEL)),
                ('national_partners', models.ManyToManyField(related_name='national_partner_assessment_reg', to='organization.Organization')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project')),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
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
    ]
