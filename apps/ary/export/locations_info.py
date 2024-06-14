default_values = {}


def is_point_data(x):
    return isinstance(x, dict) and x["geo_json"]["geometry"]["type"] == "Point"


def is_polygon_data(x):
    return isinstance(x, dict) and x["geo_json"]["geometry"]["type"] == "Polygon"


def get_title_from_geo_json_data(x):
    return x.get("geo_json") and x["geo_json"].get("properties") and x["geo_json"]["properties"].get("title")


def get_locations_info(assessment):
    geo_areas = assessment.locations.all()
    data = []

    if not geo_areas:
        return {"locations": data}

    # Region is the region of the first geo area
    region = geo_areas[0].admin_level.region
    region_geos = {x["key"]: x for x in region.geo_options}

    for area in geo_areas:
        geo_info = region_geos.get(str(area.id))
        if geo_info is None:
            continue
        level = geo_info["admin_level"]
        key = f"Admin {level}"

        admin_levels = {f"Admin {x}": None for x in range(7)}
        admin_levels[key] = area.title
        # Now add parents as well
        while level - 1:
            level -= 1
            parent_id = geo_info["parent"]

            if parent_id is None:
                break

            geo_info = region_geos.get(str(parent_id))
            if not geo_info:
                break

            key = f"Admin {level}"
            admin_levels[key] = geo_info["title"]

        data.append(admin_levels)

    return {
        "locations": data,
    }
