import json
from dataclasses import dataclass, field
from pathlib import Path
from time import sleep
from typing import Optional

import pya

_path = Path(__file__).parent.parent
poff = str(_path / "PortOff.png")
pon = str(_path / "PortOn.png")


polygon_dict = {}
dpolygon_dict = {}
shapes_shown = {}

prefix = "kfactory:ports:"


def toggle_ports(action):
    acv = pya.CellView.active()
    idx = acv.index()
    cell = acv.cell

    if cell is not None:
        cidx = cell.cell_index()
        layout = acv.layout()

        if idx not in shapes_shown:
            shapes_shown[idx] = {}

        if cidx in shapes_shown[idx]:
            shapes = shapes_shown[idx][cidx]
            for layer, shapes in shapes_shown[idx][cidx].items():
                lidx = cell.layout().layer(layer)
                for shape in shapes:
                    if cell.shapes(lidx).is_valid(shape):
                        cell.shapes(lidx).erase(shape)
                # del shapes_shown[idx][cidx][lidx]
            del shapes_shown[idx][cidx]
            update_icon(action)
        else:
            shapes_shown[idx][cidx] = {}
            ports = portdict_from_meta(cell)
            for port in ports.values():
                shapes = show_port(port, cell)
                if port["layer"] not in shapes_shown[idx][cidx]:
                    shapes_shown[idx][cidx][port["layer"]] = []

                shapes_shown[idx][cidx][port["layer"]].extend(shapes)
            update_icon(action)


def update_icon(action):
    acv = pya.CellView.active()
    idx = acv.index()
    cell = acv.cell
    if cell is not None:
        cidx = cell.cell_index()
    if idx in shapes_shown and cidx in shapes_shown[idx]:
        action.icon = pon
        action.icon_text = "Hide Ports"
        action.tool_tip = "Current Status: Shown"
    else:
        action.icon = poff
        action.icon_text = "Show Ports"
        action.tool_tip = "Current Status: Hidden"


def portdict_from_meta(cell):
    ports = {}
    for meta in cell.each_meta_info():
        if meta.name.startswith(prefix):
            name = meta.name.removeprefix(prefix)
            index, _type = name.split(":", 1)
            if index not in ports:
                ports[index] = {}

            if _type == "width":
                ports[index]["width"] = meta.value
            elif _type == "trans":
                ports[index]["trans"] = pya.Trans.from_s(meta.value)
            elif _type == "dcplx_trans":
                ports[index]["dcplx_trans"] = pya.DCplx_Trans.from_s(meta.value)
            elif _type == "layer":
                ports[index]["layer"] = pya.LayerInfo.from_string(meta.value)
            elif _type == "name":
                ports[index]["name"] = meta.value

    return ports


def show_port(port, cell):
    if "width" in port and "layer" in port and "trans" in port:
        lidx = cell.layout().layer(port["layer"])
        trans = pya.Trans(port["trans"])
        shapes = [
            cell.shapes(lidx).insert(get_polygon(port["width"]).transformed(trans))
        ]
        if "name" in port:
            shapes.append(cell.shapes(lidx).insert(pya.Text(port["name"], trans)))
        return shapes
    elif "width" in port and "layer" in port and "dcplx_trans" in port:
        lidx = cell.layout().layer(port["layer"])
        trans = pya.DCplxTrans(port["dcplx_trans"])
        shape = shapes = [
            cell.shapes(lidx).insert(
                get_polygon(port["width"]).to_dtype(layout.dbu).transformed()
            )
        ]
        if "name" in port:
            shapes.append(cell.shapes(lidx).insert(pya.DText(port["name"], trans)))
        return shapes


def get_polygon(width):
    if width in polygon_dict:
        return polygon_dict[width]
    else:
        poly = pya.Polygon(
            [
                pya.Point(0, width // 2),
                pya.Point(0, -width // 2),
                pya.Point(width // 2, 0),
            ]
        )

        hole = pya.Region(poly).sized(-int(width * 0.05) or -1)
        hole -= pya.Region(pya.Box(0, 0, width // 2, -width // 2))

        poly.insert_hole(list(list(hole.each())[0].each_point_hull()))
        polygon_dict[width] = poly
        return poly
