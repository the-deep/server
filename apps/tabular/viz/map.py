import json
import logging

from geo.models import AdminLevel, GeoArea, Region

from utils.common import create_plot_image, make_colormap

logger = logging.getLogger(__name__)


try:
    import geopandas as gpd
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt
    from shapely.geometry import shape
except ImportError as e:
    logger.warning(f"ImportError: {e}")


def get_geoareas(selected_geoareas, admin_levels=None, regions=None):
    if admin_levels or regions:
        if admin_levels:
            geoareas = GeoArea.objects.filter(
                admin_level__level__in=admin_levels,
            )
        if regions:
            geoareas = GeoArea.objects.filter(
                admin_level__region__in=regions,
            )
    else:
        geoareas = GeoArea.objects.filter(
            admin_level__level__in=AdminLevel.objects.filter(
                geoarea__in=selected_geoareas,
            )
            .distinct()
            .values_list("level", flat=True),
            admin_level__region__in=Region.objects.filter(
                adminlevel__geoarea__in=selected_geoareas,
            )
            .distinct()
            .values_list("pk", flat=True),
        )
    return geoareas


@create_plot_image
def plot(*args, **kwargs):
    # NOTE: this are admin_level.level list not pk or admin_levels objects
    admin_levels = kwargs.get("admin_levels")
    # NOTE: this are region pks/objects
    regions = kwargs.get("regions")
    df = kwargs.get("data").rename(columns={"value": "geoarea_id"})

    shapes = []
    geoareas = get_geoareas(
        df["geoarea_id"].values.tolist(),
        admin_levels,
        regions,
    )

    if len(geoareas) == 0:
        logger.warning("Empty geoareas found")
        return

    for geoarea in geoareas:
        s = shape(json.loads(geoarea.polygons.geojson))
        shapes.append({"geoarea_id": geoarea.id, "geometry": s})
    shapes_frame = gpd.GeoDataFrame(shapes, geometry="geometry")
    data = shapes_frame.merge(df, on="geoarea_id", how="outer").fillna(0)

    c = mcolors.ColorConverter().to_rgb
    rvb = make_colormap([c("white"), c("teal")])

    data.plot(
        column="count",
        cmap=rvb,
        legend=True,
        linewidth=0.4,
        edgecolor="0.5",
    )
    plt.axis("off")
