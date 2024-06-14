import json
import re

import reversion
from analysis_framework.models import AnalysisFramework, Exportable, Filter, Widget
from deep_migration.models import (
    AnalysisFrameworkMigration,
    ProjectMigration,
    UserMigration,
)
from deep_migration.utils import MigrationCommand, get_source_url, request_with_auth


def get_user(old_user_id):
    migration = UserMigration.objects.filter(old_id=old_user_id).first()
    return migration and migration.user


def get_project(project_id):
    migration = ProjectMigration.objects.filter(old_id=project_id).first()
    return migration and migration.project


def snap(x, default=16):
    if isinstance(x, str):
        x = int(re.sub(r"[^\d-]+", "", x))
    return round(x / default) * default


class Command(MigrationCommand):
    def run(self):
        if self.kwargs.get("data_file"):
            with open(self.kwargs["data_file"]) as f:
                frameworks = json.load(f)
        else:
            query = self.kwargs.get("query_str", "")
            frameworks = request_with_auth(get_source_url("entry-templates", "v1", query))

        if not frameworks:
            print("Couldn't find AF data at")

        with reversion.create_revision():
            new_frameworks_file = open("new_afs.txt", "a")
            for framework in frameworks:
                self.import_framework(framework, new_frameworks_file)
            new_frameworks_file.close()

    def import_framework(self, data, file):
        print("------------")
        print("Migrating analysis framework")

        old_id = data["id"]
        title = data["name"]

        print("{} - {}".format(old_id, title))

        migration, _ = AnalysisFrameworkMigration.objects.get_or_create(
            old_id=old_id,
        )

        if not migration.analysis_framework:
            framework = AnalysisFramework.objects.create(
                title=title,
            )
            migration.analysis_framework = framework
            file.write("{}\n".format(framework.id))
            migration.save()
        else:
            return migration.analysis_framework

        framework = migration.analysis_framework

        framework.created_by = get_user(data["created_by"])
        framework.modified_by = framework.created_by

        framework.save()
        AnalysisFramework.objects.filter(id=framework.id).update(created_at=data["created_at"])

        projects = data["projects"]
        for project_id in projects:
            project = get_project(project_id)
            if project:
                project.analysis_framework = framework
                project.save()

        # Let's start migrating widgets

        elements = data["elements"]
        for element in elements:
            self.migrate_widget(framework, element)

        return framework

    def migrate_widget(self, framework, element):
        print("Migrating widget {}".format(element["id"]))

        type_method_map = {
            "pageOneExcerptBox": self.migrate_excerpt,
            "pageTwoExcerptBox": self.migrate_excerpt,
            "matrix1d": self.migrate_matrix1d,
            "matrix2d": self.migrate_matrix2d,
            "number-input": self.migrate_number,
            "date-input": self.migrate_date,
            "scale": self.migrate_scale,
            "organigram": self.migrate_organigram,
            "multiselect": self.migrate_multiselect,
            "geolocations": self.migrate_geo,
            "number2d": self.migrate_number_matrix,
        }

        method = type_method_map.get(element["type"])
        if method:
            method(framework, element)

    def migrate_excerpt(self, framework, element):
        widget, _ = Widget.objects.get_or_create(
            widget_id="excerptWidget",
            analysis_framework=framework,
            defaults={
                "title": (element.get("label") or element.get("excerptLabel") or "Excerpt"),
                "key": element["id"],
                "properties": {},
            },
        )

        if element["id"] == "page-one-excerpt":
            widget.properties.update(
                {
                    "overview_grid_layout": self.get_layout(element),
                }
            )
        elif element["id"] == "page-two-excerpt":
            widget.properties.update(
                {
                    "list_grid_layout": self.get_layout(element),
                }
            )
        widget.save()

    def migrate_number(self, framework, element):
        title = element["label"] or "Number"
        widget, _ = Widget.objects.get_or_create(
            widget_id="numberWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "list_grid_layout": self.get_layout(element),
                },
            },
        )

        filter, _ = Filter.objects.get_or_create(
            key=element["id"],
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": title,
                "filter_type": "number",
                "properties": {
                    "type": "number",
                },
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": {"excel": {"title": title}},
            },
        )

    def migrate_date(self, framework, element):
        title = element["label"] or "Date"
        widget, _ = Widget.objects.get_or_create(
            widget_id="dateWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "list_grid_layout": self.get_layout(element),
                },
            },
        )

        filter, _ = Filter.objects.get_or_create(
            key=element["id"],
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": title,
                "filter_type": "number",
                "properties": {
                    "type": "date",
                },
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": {"excel": {"title": title}},
            },
        )

    def migrate_scale(self, framework, element):
        title = element["label"] or "Scale"
        widget, _ = Widget.objects.get_or_create(
            widget_id="scaleWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "list_grid_layout": self.get_layout(element),
                    "data": {
                        "scale_units": self.convert_scale_values(element["scaleValues"]),
                        "value": self.get_default_scale_value(element["scaleValues"]),
                    },
                },
            },
        )

        filter, _ = Filter.objects.get_or_create(
            key=element["id"],
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "type": "multiselect-range",
                    "options": self.convert_scale_filter_values(element["scaleValues"]),
                },
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": {"excel": {"title": title}},
            },
        )

    def convert_scale_values(self, values):
        return [
            {
                "title": v["name"],
                "color": v["color"],
                "key": v["id"],
                "default": v["default"],
            }
            for v in values
        ]

    def get_default_scale_value(self, values):
        return next((v["id"] for v in values if v["default"]), None)

    def convert_scale_filter_values(self, values):
        return [
            {
                "label": v["name"],
                "key": v["id"],
            }
            for v in values
        ]

    def migrate_organigram(self, framework, element):
        title = element["label"] or "Organigram"
        widget, _ = Widget.objects.get_or_create(
            widget_id="organigramWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "list_grid_layout": self.get_layout(element),
                    "data": self.convert_organigram(element["nodes"]),
                },
            },
        )

        filter, _ = Filter.objects.get_or_create(
            key=element["id"],
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "type": "multiselect",
                    "options": self.get_organigram_filter_nodes(element["nodes"]),
                },
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": {"excel": {"title": title}},
            },
        )

    def convert_organigram(self, nodes):
        parent_nodes = self.get_organigram_nodes(nodes, "")
        return parent_nodes and parent_nodes[0]

    def get_organigram_nodes(self, nodes, parent):
        return [
            {
                "key": node["id"],
                "title": node["name"],
                "organs": self.get_organigram_nodes(nodes, node["id"]),
            }
            for node in nodes
            if node["parent"] == parent
        ]

    def get_organigram_filter_nodes(self, nodes, parent="", prefix=""):
        values = []
        for node in nodes:
            title = "{}{}".format(prefix, node["name"])
            if node["parent"] == parent:
                values.append(
                    {
                        "key": node["id"],
                        "label": title,
                    }
                )

                values.extend(
                    self.get_organigram_filter_nodes(
                        nodes,
                        node["id"],
                        "{} / ".format(title),
                    )
                )
        return values

    def migrate_multiselect(self, framework, element):
        title = element["label"] or "Groups"
        widget, _ = Widget.objects.get_or_create(
            widget_id="multiselectWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "list_grid_layout": self.get_layout(element),
                    "data": {
                        "options": self.convert_multiselect(element["options"]),
                    },
                },
            },
        )

        filter, _ = Filter.objects.get_or_create(
            key=element["id"],
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "type": "multiselect",
                    "options": self.convert_multiselect(element["options"]),
                },
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": {"excel": {"title": title}},
            },
        )

    def convert_multiselect(self, options):
        return [
            {
                "key": option["id"],
                "label": option["text"],
            }
            for option in options
        ]

    def migrate_geo(self, framework, element):
        title = element["label"] or "Geo"
        widget, _ = Widget.objects.get_or_create(
            widget_id="geoWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "list_grid_layout": self.get_layout(element),
                },
            },
        )

        filter, _ = Filter.objects.get_or_create(
            key=element["id"],
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": title,
                "properties": {
                    "type": "geo",
                },
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": {"excel": {"type": "geo"}},
            },
        )

    def migrate_number_matrix(self, framework, element):
        widget, _ = Widget.objects.get_or_create(
            widget_id="numberMatrixWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": element["title"],
                "properties": {
                    "overview_grid_layout": self.get_layout(element),
                    "list_grid_layout": self.get_layout(element.get("list")),
                    "data": self.convert_number_matrix(element["rows"], element["columns"]),
                },
            },
        )

        filter, _ = Filter.objects.get_or_create(
            key=element["id"],
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": element["title"],
                "properties": {
                    "type": "number-2d",
                },
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": self.convert_number_matrix_export(element["rows"], element["columns"]),
            },
        )

    def convert_number_matrix(self, rows, columns):
        row_headers = []
        column_headers = []
        for row in rows:
            row_headers.append({"key": row["id"], "title": row["title"]})
        for column in columns:
            column_headers.append({"key": column["id"], "title": column["title"]})

        return {
            "row_headers": row_headers,
            "column_headers": column_headers,
        }

    def convert_number_matrix_export(self, rows, columns):
        titles = []
        for row in rows:
            for column in columns:
                titles.append("{}-{}".format(row["title"], column["title"]))

        return {
            "excel": {
                "type": "multiple",
                "titles": titles,
            },
        }

    def migrate_matrix1d(self, framework, element):
        widget, _ = Widget.objects.get_or_create(
            widget_id="matrix1dWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": element["title"],
                "properties": {
                    "overview_grid_layout": self.get_layout(element),
                    "list_grid_layout": self.get_layout(element.get("list")),
                    "data": {
                        "rows": self.convert_matrix1d_rows(element["pillars"]),
                    },
                },
            },
        )

        filter, _ = Filter.objects.get_or_create(
            key=element["id"],
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": element["title"],
                "properties": {"type": "multiselect", "options": self.convert_matrix1d_filter(element["pillars"])},
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": self.convert_matrix1d_export(element["pillars"]),
            },
        )

    def convert_matrix1d_rows(self, pillars):
        return [
            {
                "key": pillar["id"],
                "title": pillar["name"],
                "color": pillar["color"],
                "tooltip": pillar["tooltip"],
                "cells": self.convert_matrix1d_cells(pillar["subpillars"]),
            }
            for pillar in pillars
        ]

    def convert_matrix1d_cells(self, subpillars):
        return [
            {
                "key": subpillar["id"],
                "value": subpillar["name"],
            }
            for subpillar in subpillars
        ]

    def convert_matrix1d_filter(self, pillars):
        options = []
        for pillar in pillars:
            options.append(
                {
                    "key": pillar["id"],
                    "label": pillar["name"],
                }
            )

            for subpillar in pillar["subpillars"]:
                options.append(
                    {
                        "key": subpillar["id"],
                        "label": "{} / {}".format(
                            pillar["name"],
                            subpillar["name"],
                        ),
                    }
                )
        return options

    def convert_matrix1d_export(self, pillars):
        excel = {
            "titles": ["Dimension", "Subdimension"],
            "type": "multiple",
        }

        levels = []
        for pillar in pillars:
            sublevels = [
                {
                    "id": subpillar["id"],
                    "title": subpillar["name"],
                }
                for subpillar in pillar["subpillars"]
            ]
            levels.append(
                {
                    "id": pillar["id"],
                    "title": pillar["name"],
                    "sublevels": sublevels,
                }
            )

        report = {"levels": levels}

        return {
            "excel": excel,
            "report": report,
        }

    def migrate_matrix2d(self, framework, element):
        widget, _ = Widget.objects.get_or_create(
            widget_id="matrix2dWidget",
            analysis_framework=framework,
            key=element["id"],
            defaults={
                "title": element["title"],
                "properties": {
                    "overview_grid_layout": self.get_layout(element),
                    "list_grid_layout": self.get_layout(element.get("list")),
                    "data": {
                        "dimensions": self.convert_matrix2d_dimensions(element["pillars"]),
                        "sectors": self.convert_matrix2d_sectors(element["sectors"]),
                    },
                },
            },
        )

        filter1, _ = Filter.objects.get_or_create(
            key="{}-dimensions".format(element["id"]),
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": "{} Dimensions".format(element["title"]),
                "properties": {"type": "multiselect", "options": self.convert_matrix2d_filter1(element["pillars"])},
            },
        )

        filter2, _ = Filter.objects.get_or_create(
            key="{}-sectors".format(element["id"]),
            analysis_framework=framework,
            widget_key=element["id"],
            defaults={
                "title": "{} Sectors".format(element["title"]),
                "properties": {"type": "multiselect", "options": self.convert_matrix2d_filter2(element["sectors"])},
            },
        )

        exportable, _ = Exportable.objects.get_or_create(
            widget_key=element["id"],
            analysis_framework=framework,
            defaults={
                "data": self.convert_matrix2d_export(element),
            },
        )

    def convert_matrix2d_dimensions(self, pillars):
        return [
            {
                "id": pillar["id"],
                "title": pillar["title"],
                "color": pillar["color"],
                "tooltip": pillar["tooltip"],
                "subdimensions": self.convert_matrix2d_subdimensions(pillar["subpillars"]),
            }
            for pillar in pillars
            if pillar.get("id")
        ]

    def convert_matrix2d_subdimensions(self, subpillars):
        return [
            {
                "id": subpillar["id"],
                "title": subpillar["title"],
                "tooltip": subpillar["tooltip"],
            }
            for subpillar in subpillars
            if subpillar.get("id")
        ]

    def convert_matrix2d_sectors(self, sectors):
        return [
            {"id": sector["id"], "title": sector["title"], "subsectors": self.convert_matrix2d_subsectors(sector["subsectors"])}
            for sector in sectors
            if sector.get("id")
        ]

    def convert_matrix2d_subsectors(self, subsectors):
        return [
            {
                "id": subsector["id"],
                "title": subsector["title"],
            }
            for subsector in subsectors
            if subsector.get("id")
        ]

    def convert_matrix2d_filter1(self, pillars):
        options = []
        for pillar in pillars:
            if not pillar.get("id"):
                continue
            options.append(
                {
                    "key": pillar["id"],
                    "label": pillar["title"],
                }
            )

            for subpillar in pillar["subpillars"]:
                options.append(
                    {
                        "key": subpillar["id"],
                        "label": "{} / {}".format(
                            pillar["title"],
                            subpillar["title"],
                        ),
                    }
                )
        return options

    def convert_matrix2d_filter2(self, sectors):
        options = []
        for sector in sectors:
            if not sector.get("id"):
                continue
            options.append(
                {
                    "key": sector["id"],
                    "label": sector["title"],
                }
            )

            for subsector in sector["subsectors"]:
                options.append(
                    {
                        "key": subsector["id"],
                        "label": "{} / {}".format(
                            sector["title"],
                            subsector["title"],
                        ),
                    }
                )
        return options

    def convert_matrix2d_export(self, element):
        excel = {
            "type": "multiple",
            "titles": ["Dimension", "Subdimension", "Sector", "Subsectors"],
        }

        levels = []
        for sector in element["sectors"]:
            if not sector.get("id"):
                continue
            sublevels = []

            for pillar in element["pillars"]:
                if not pillar.get("id"):
                    continue
                subsublevels = []

                for subpillar in pillar["subpillars"]:
                    if not subpillar.get("id"):
                        continue
                    subsublevels.append(
                        {
                            "id": subpillar["id"],
                            "title": subpillar["title"],
                        }
                    )

                sublevels.append(
                    {
                        "id": pillar["id"],
                        "title": pillar["title"],
                        "sublevels": subsublevels,
                    }
                )

            levels.append(
                {
                    "id": sector["id"],
                    "title": sector["title"],
                    "sublevels": sublevels,
                }
            )

        report = {
            "levels": levels,
        }

        return {
            "excel": excel,
            "report": report,
        }

    def get_layout(self, element):
        if not element:
            element = {}
        default_size = {
            "width": element.get("width") or 240,
            "height": element.get("height") or 240,
        }
        default_position = {
            "left": element.get("left") or 0,
            "top": element.get("top") or 0,
        }
        layout = {
            **(element.get("size") or default_size),
            **(element.get("position") or default_position),
        }

        return {key: snap(value) for key, value in layout.items()}
