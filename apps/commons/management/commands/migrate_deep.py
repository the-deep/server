import json
from django.db import connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = 'Dump Database into a file'

    def handle(self, *args, **kwargs):
        self.execute_sql()

    def custom_sql(self):
        # migrate all the associated thing related to the project
        sql_project = "SELECT project_project.id, project_project.created_at, project_project.modified_at,\
                       project_project.created_by_id, project_project.modified_by_id, project_project.client_id,\
                       project_project.title, project_project.description, project_project.start_date,\
                       project_project.end_date, project_project.analysis_framework_id,\
                       project_project.category_editor_id, project_project.assessment_template_id, \
                       project_project.data, project_project.is_default, project_project.is_private,\
                       project_project.is_visualization_enabled, project_project.status, \
                       project_project.stats_cache FROM project_project WHERE project_project.id = 2 \
                       ORDER BY project_project.created_at DESC"
        # TODO: how to retrieve the members(m2m2 field) in the analysis_framework
        sql_project_memberships = "SELECT projectproject_membership.id,\
                                   project_projectmembership.member_id,\
                                   project_projectmembership.project_id,\
                                   project_projectmembership.role_id,\
                                   project_projectmembership.linked_group_id,\
                                   project_projectmembership.joined_at,\
                                   project_projectmembership.added_by_id\
                                   FROM project_projectmembership WHERE project_projectmembership.project_id=2"
        sql_project_role = "SELECT project_projectrole.id,\
                            project_projectrole.title,\
                            project_projectrole.lead_permissions,\
                            project_projectrole.entry_permissions,\
                            project_projectrole.setup_permissions,\
                            project_projectrole.assessement_permissions,\
                            project_projectrole.level,\
                            project_projectrole.is_creator_role,\
                            project_projectrole.is_default_role,\
                            project_projectrole.description\
                            FROM project_projectrole"
        sql_project_orgnization = "SELECT project_projectorganization.id,\
                                   project_projectorganization.organization_type,\
                                   project_projectorganization.organization_id,\
                                   project_projectorganization.project_id\
                                   FROM project_projectorganization WHERE project_projecorganization.project_id=2"
        # check for the s3 bucket in the organization logo
        sql_organization = "SELECT organaization_projectorganization.id,\
                            organization_organization.creted_at,\
                            organization_organization.modified_at,\
                            organization_organization.created_by_id,\
                            organization_organization.modified_by_id,\
                            organization_organization.parent_id,\
                            organization_organization.title,\
                            organization_organization.short_name,\
                            organization_organization.long_name,\
                            organization_organization.url,\
                            organization_organization.relief_web_id,\
                            organization_organization.logo_id,\
                            organization_organization.organization_type_id,\
                            organization_organization.verified,\
                            FROM organization_organization"

        sql_geo_region = " SELECT geo_region.id,\
                            geo_region.created_at,\
                            geo_region.modified_at,\
                            geo_region.created_by_id,\
                            geo_region.modified_by_id,\
                            geo_region.code,\
                            geo_region.title,\
                            geo_region.public,\
                            geo_region.regional_groups,\
                            geo_region.key_figures,\
                            geo_region.population_data,\
                            geo_region.media_sources,\
                            geo_region.geo_options \
                            from  geo_region"
        sql_geo_areas = "select  geo_geoarea.id,\
                         geo_geoarea.admin_level_id,\
                         geo_geoarea.parent_id,\
                         geo_geoarea.title,\
                         geo_geoarea.code,\
                         geo_geoarea.data\
                         from  geo_geoarea"
        # keep track for the geojson_file and bounds_file in s3 bucket
        sql_geo_admin = "SELECT geo_adminlevel.id,\
                        geo_adminlevel.region_id,\
                        geo_adminlevel.parent_id ,\
                        geo_adminlevel.title,\
                        geo_adminlevel.level,\
                        geo_adminlevel.name_prop,\
                        geo_adminlevel.code_prop,\
                        geo_adminlevel.parent_name_prop,\
                        geo_adminlevel.parent_code_prop,\
                        geo_adminlevel.geo_shape_file_id,\
                        geo_adminlevel.tolerance,\
                        geo_adminlevel.stale_geo_areas,\
                        geo_adminlevel.geojson_file,\
                        geo_adminlevel.bounds_file,\
                        geo_adminlevel.geo_area_titles\
                        from  geo_adminlevel"
        sql_analysis_framework = "SELECT analysis_framework_analysisframework.id,\
                                  analysis_framework_analysisframework.created_at,\
                                  analysis_framework_analysisframework.modified_at,\
                                  analysis_framework_analysisframework.created_by_id,\
                                  analysis_framework_analysisframework.modified_by_id,\
                                  analysis_framework_analysisframework.client_id,\
                                  analysis_framework_analysisframework.title,\
                                  analysis_framework_analysisframework.description,\
                                  analysis_framework_analysisframework.is_private,\
                                  analysis_framework_analysisframework.properties\
                                  FROM analysis_framework_analysisframework\
                                  ORDER BY analysis_framework_analysisframework.created_at DESC"
        sql_analysis_framework_widgets = "SELECT analysis_framework_widget.id,\
                                          analysis_framework_widget.analysis_framework_id,\
                                          analysis_framework_widget.key,\
                                          analysis_framework_widget.widget_id,\
                                          analysis_famework_widget.title,\
                                          analysis_framework_widget.properties FROM analysis_framework_widget"
        sql_analysis_framework_filter = "SELECT analysis_framework_filter.id,\
                                         analysis_framework_filter.analysis_framework_id,\
                                         analysis_framework_filter.key,\
                                         analysis_framework_filter.widget_key,\
                                         analysis_framework_filter.title,\
                                         analysis_framework_filter.properties,\
                                         analysis_framework_filter.filter_type FROM analysis_framework_filter"
        sql_analysis_framework_exportable = "SELECT analysis_framework_exportable.id,\
                                             analysis_framework_exportable.analysis_framework_id,\
                                             analysis_framework_exportable.widget_key,\
                                             anlysis_framework_exportble.inline,\
                                             analysis_framework_exportable.order,\
                                             analysis_framework_exportable.data,\
                                             FROM analysis_framework_exportable"
        sql_category_editor = "SELECT category_editor_categoryeditor.id,\
                               category_editor_categoryeditor.created_at,\
                               category_editor_categoryeditor.modified_at,\
                               category_editor_categoryeditor.created_by_id,\
                               category_editor_categoryeditor.modified_by_id,\
                               category_editor_categoryeditor.client_id,\
                               category_editor_categoryeditor.title,\
                               category_editor_categoryeditor.data\
                               FROM category_editor_categoryeditor\
                               ORDER BY category_editor_categoryeditor.created_at DESC"
        sql_assessment_template = "SELECT ary_assessmenttemplate.id, ary_assessmenttemplate.created_at,\
                                   ary_assessmenttemplate.modified_at, ary_assessmenttemplate.created_by_id,\
                                   ary_assessmenttemplate.modified_by_id, ary_assessmenttemplate.client_id,\
                                   ary_assessmenttemplate.title FROM ary_assessmenttemplate\
                                   ORDER BY ary_assessmenttemplate.created_at DESC"
        sql_user = "SELECT auth_user.id, auth_user.password,auth_user.is_superuser, auth_user.username,\
                    auth_user.first_name, auth_user.last_name, auth_user.email, auth_user.is_staff,\
                    auth_user.is_active, auth_user.date_joined FROM auth_user"

        # TODO: here keep track for the s3 bucket for the display_picture in
        sql_usergroup = "SELECT user_group_usergroup.id, user_group_usergroup.title,\
                        user_group_usergroup.description, user_group_usergroup.display_picture_id,\
                        user_group_usergroup.global_crisis_monitoring,user_group_usergroup.custom_project_fields\
                        FROM user_group_usergroup"
        # TODO: here keep track for the s3 bucket for attachment that is fk
        sql_lead = "SELECT lead_lead.id, lead_lead.created_at, lead_lead.modified_at,\
                    lead_lead.created_by_id, lead_lead.modified_by_id, lead_lead.client_id,\
                    lead_lead.lead_group_id, lead_lead.project_id, lead_lead.title,\
                    lead_lead.author_id, lead_lead.source_id, lead_lead.author_raw,\
                    lead_lead.source_raw, lead_lead.source_type, lead_lead.priority,\
                    lead_lead.confidentiality, lead_lead.status, lead_lead.published_on,\
                    lead_lead.text, lead_lead.url, lead_lead.website, lead_lead.attachment_id\
                    FROM lead_lead WHERE lead_lead.project_id = 2 ORDER BY lead_lead.created_at DESC"
        sql_lead_group = "SELECT lead_leadgroup.id, lead_leadgroup.created_at, lead_leadgroup.modified_at,\
                          lead_leadgroup.created_by_id, lead_leadgroup.modified_by_id, lead_leadgroup.client_id,\
                          lead_leadgroup.title, lead_leadgroup.project_id FROM lead_leadgroup\
                          WHERE lead_leadgroup.project_id = 2 ORDER BY lead_leadgroup.created_at DESC"
        # TODO: here keep track of the file field for the s3 bucket
        sql_lead_attachment = "SELECT gallery_file.id, gallery_file.created_at, gallery_file.modified_at,\
                              gallery_file.created_by_id, gallery_file.modified_by_id, gallery_file.client_id,\
                              gallery_file.uuid, gallery_file.title, gallery_file.file, gallery_file.mime_type,\
                              gallery_file.metadata, gallery_file.is_public FROM gallery_file\
                              INNER JOIN gallery_file_projects ON (gallery_file.id = gallery_file_projects.file_id)\
                              WHERE gallery_file_projects.project_id IN (2) ORDER BY gallery_file.created_at DESC"
        sql_lead_preview = "SELECT lead_leadpreview.id, lead_leadpreview.lead_id, lead_leadpreview.text_extract,\
                            lead_leadpreview.thumbnail, lead_leadpreview.thumbnail_height,\
                            lead_leadpreview.thumbnail_width, lead_leadpreview.word_count,\
                            lead_leadpreview.page_count, lead_leadpreview.classified_doc_id,\
                            lead_leadpreview.classification_status FROM lead_leadpreview\
                            INNER JOIN lead_lead ON (lead_leadpreview.lead_id = lead_lead.id)\
                            WHERE lead_lead.project_id = 2"
        # TODO: here keep track for the previewimage file in the s3 bucket
        sql_lead_preview_image = "SELECT lead_leadpreviewimage.id, lead_leadpreviewimage.lead_id,\
                                  lead_leadpreviewimage.file FROM lead_leadpreviewimage\
                                  INNER JOIN lead_lead ON (lead_leadpreviewimage.lead_id = lead_lead.id)\
                                  WHERE lead_lead.project_id = 2"
        sql_for_entry = "SELECT entry_entry.id, entry_entry.created_at, entry_entry.modified_at,\
                         entry_entry.created_by_id, entry_entry.modified_by_id, entry_entry.client_id,\
                         entry_entry.lead_id, entry_entry.project_id, entry_entry.order,\
                         entry_entry.analysis_framework_id, entry_entry.information_date,\
                         entry_entry.entry_type, entry_entry.excerpt, entry_entry.image,\
                         entry_entry.tabular_field_id, entry_entry.dropped_excerpt,\
                         entry_entry.highlight_hidden, entry_entry.verified,\
                         entry_entry.verification_last_changed_by_id FROM entry_entry\
                         WHERE entry_entry.project_id = 2 \
                         ORDER BY entry_entry.order ASC, entry_entry.created_at DESC"
        sql_for_entry_attribute = "SELECT entry_attribute.id, entry_attribute.entry_id,\
                                   entry_attribute.widget_id, entry_attribute.data\
                                   FROM entry_attribute INNER JOIN entry_entry\
                                   ON (entry_attribute.entry_id = entry_entry.id)\
                                   WHERE entry_entry.project_id = 2"
        sql_for_entry_filter_data = "SELECT entry_filterdata.id, entry_filterdata.entry_id,\
                                     entry_filterdata.filter_id, entry_filterdata.values,\
                                     entry_filterdata.number, entry_filterdata.from_number,\
                                     entry_filterdata.to_number, entry_filterdata.text\
                                     FROM entry_filterdata INNER JOIN entry_entry ON\
                                     (entry_filterdata.entry_id = entry_entry.id)\
                                     WHERE entry_entry.project_id = 2"
        sql_for_entry_export_data = "SELECT entry_exportdata.id, entry_exportdata.entry_id,\
                                     entry_exportdata.exportable_id, entry_exportdata.data\
                                     FROM entry_exportdata INNER JOIN entry_entry ON\
                                     (entry_exportdata.entry_id = entry_entry.id)\
                                     WHERE entry_entry.project_id = 2"
        sql_for_entry_entrycomment = "SELECT entry_entrycomment.id, entry_entrycomment.entry_id,\
                                      entry_entrycomment.created_by_id, entry_entrycomment.is_resolved,\
                                      entry_entrycomment.resolved_at, entry_entrycomment.parent_id\
                                      FROM entry_entrycomment INNER JOIN entry_entry\
                                      ON (entry_entrycomment.entry_id = entry_entry.id)\
                                      WHERE entry_entry.project_id = 2"
        sql_for_entry_entrycommenttext = "SELECT entry_entrycommenttext.id, entry_entrycommenttext.comment_id,\
                                          entry_entrycommenttext.created_at, entry_entrycommenttext.text\
                                          FROM entry_entrycommenttext INNER JOIN entry_entrycomment\
                                          ON (entry_entrycommenttext.comment_id = entry_entrycomment.id)\
                                          INNER JOIN entry_entry ON\
                                          (entry_entrycomment.entry_id = entry_entry.id)\
                                          WHERE entry_entry.project_id = 2"
        sql_for_entry_projectentrylabel = "SELECT entry_projectentrylabel.id,\
                                                entry_projectentrylabel.created_at,\
                                                entry_projectentrylabel.modified_at,\
                                                entry_projectentrylabel.created_by_id,\
                                                entry_projectentrylabel.modified_by_id,\
                                                entry_projectentrylabel.client_id,\
                                                entry_projectentrylabel.project_id,\
                                                entry_projectentrylabel.title,\
                                                entry_projectentrylabel.order,\
                                                entry_projectentrylabel.color\
                                                FROM entry_projectentrylabel WHERE\
                                                entry_projectentrylabel.project_id = 2\
                                                ORDER BY entry_projectentrylabel.created_at DESC"
        sql_for_entry_leadentrygroup = "SELECT entry_leadentrygroup.id,\
                                        entry_leadentrygroup.created_at,\
                                        entry_leadentrygroup.modified_at,\
                                        entry_leadentrygroup.created_by_id,\
                                        entry_leadentrygroup.modified_by_id,\
                                        entry_leadentrygroup.lead_id,\
                                        entry_leadentrygroup.title,\
                                        entry_leadentrygroup.order\
                                        FROM entry_leadentrygroup\
                                        INNER JOIN lead_lead ON (entry_leadentrygroup.lead_id = lead_lead.id)\
                                        WHERE lead_lead.project_id = 2 ORDER BY\
                                        entry_leadentrygroup.created_at DESC"
        sql_for_entrygrouplabel = "SELECT entry_entrygrouplabel.id, entry_entrygrouplabel.created_at,\
                                   entry_entrygrouplabel.modified_at, entry_entrygrouplabel.created_by_id,\
                                   entry_entrygrouplabel.modified_by_id, entry_entrygrouplabel.label_id,\
                                   entry_entrygrouplabel.group_id, entry_entrygrouplabel.entry_id\
                                   FROM entry_entrygrouplabel INNER JOIN entry_entry\
                                   ON (entry_entrygrouplabel.entry_id = entry_entry.id)\
                                   WHERE entry_entry.project_id = 2"
        return sql_lead

    def execute_sql(self):
        # serialize the sql here
        with connection.cursor() as cursor:
            cursor.execute(self.custom_sql())
            rows = cursor.fetchall()
            result = []
            keys = [col[0] for col in cursor.description]
            for row in rows:
                result.append(dict(zip(keys, row)))
            json_data = json.dumps(result, default=str)
            out = open('dump.json', 'w')
            out.write(json_data)  # serialize output
            out.close()