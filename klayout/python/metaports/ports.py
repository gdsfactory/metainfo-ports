# $description: Python function to show kfactory style ports
import json
from dataclasses import dataclass, field
from pathlib import Path
from time import sleep
from typing import Optional

import pya

app = pya.Application.instance()
mw = app.main_window()

_path = Path(__file__).parents[2]
poff = str(_path / "PortOff.png")
pon = str(_path / "PortOn.png")
with (_path / "settings.json").open("rb") as settings_file:
    settings = json.load(settings_file)


polygon_dict = {}
dpolygon_dict = {}
shapes_shown = {}

prefix = "kfactory:ports:"


def toggle_ports(action):
    lv = mw.current_view()
    lvx = mw.current_view_index
    acv = pya.CellView.active()
    idx = acv.index()
    cell = acv.cell

    _format = settings["format"]

    cell_toggle_ports(lvx, idx, cell)
    update_icon(action)


def cell_toggle_ports(lvx, idx, cell):
    if cell is not None:
        cidx = cell.cell_index()
        layout = cell.layout()

        if lvx not in shapes_shown:
            shapes_shown[lvx] = {}

        if idx not in shapes_shown[lvx]:
            shapes_shown[lvx][idx] = {}

        if cidx in shapes_shown[lvx][idx]:
            shapes = shapes_shown[lvx][idx][cidx]
            for layer, shapes in shapes_shown[lvx][idx][cidx].items():
                lidx = cell.layout().layer(layer)
                for shape in shapes:
                    if cell.shapes(lidx).is_valid(shape):
                        cell.shapes(lidx).erase(shape)
                # del shapes_shown[idx][cidx][lidx]
            del shapes_shown[lvx][idx][cidx]
        else:
            shapes_shown[lvx][idx][cidx] = {}
            ports = portdict_from_meta(cell)
            for port in ports.values():
                shapes = show_port(port, cell, layout)
                if port["layer"] not in shapes_shown[lvx][idx][cidx]:
                    shapes_shown[lvx][idx][cidx][port["layer"]] = []

                shapes_shown[lvx][idx][cidx][port["layer"]].extend(shapes)


def cell_toggle_ports_state(lvx, idx, cell, state):
    if cell is not None:
        cidx = cell.cell_index()
        layout = cell.layout()

        if lvx not in shapes_shown:
            shapes_shown[lvx] = {}

        if idx not in shapes_shown[lvx]:
            shapes_shown[lvx][idx] = {}

        has_shapes = cidx in shapes_shown[lvx][idx]

        if has_shapes and not state:
            shapes = shapes_shown[lvx][idx][cidx]
            for layer, shapes in shapes_shown[lvx][idx][cidx].items():
                lidx = cell.layout().layer(layer)
                for shape in shapes:
                    if cell.shapes(lidx).is_valid(shape):
                        cell.shapes(lidx).erase(shape)
                # del shapes_shown[idx][cidx][lidx]
            del shapes_shown[lvx][idx][cidx]
        elif not has_shapes and state:
            shapes_shown[lvx][idx][cidx] = {}
            ports = portdict_from_meta(cell)
            for port in ports.values():
                shapes = show_port(port, cell, layout)
                if port["layer"] not in shapes_shown[lvx][idx][cidx]:
                    shapes_shown[lvx][idx][cidx][port["layer"]] = []

                shapes_shown[lvx][idx][cidx][port["layer"]].extend(shapes)


def update_icon(action):
    acv = pya.CellView.active()
    idx = acv.index()
    cell = acv.cell
    lvx = mw.current_view_index
    if cell is not None:
        cidx = cell.cell_index()
    if (
        lvx in shapes_shown
        and idx in shapes_shown[lvx]
        and cidx in shapes_shown[lvx][idx]
    ):
        action.icon = pon
        action.icon_text = "Hide Ports"
        action.tool_tip = "Current Status: Shown"
    else:
        action.icon = poff
        action.icon_text = "Show Ports"
        action.tool_tip = "Current Status: Hidden"


def portdict_from_meta(cell):
    ports = {}
    _format = settings["format"]
    if _format == "default":
        for meta in cell.each_meta_info():
            if meta.name.startswith(prefix):
                name = meta.name.removeprefix(prefix)
                index, _type = name.split(":", 1)
                if index not in ports:
                    ports[index] = {}

                if _type == "width":
                    ports[index]["width"] = meta.value
                elif _type == "trans":
                    ports[index]["trans"] = meta.value
                elif _type == "dcplx_trans":
                    ports[index]["dcplx_trans"] = meta.value
                elif _type == "layer":
                    ports[index]["layer"] = meta.value
                elif _type == "name":
                    ports[index]["name"] = meta.value
    elif _format == "legacy":
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


def show_port(port, cell, layout):
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
                get_polygon(port["width"]).to_dtype(layout.dbu).transformed(trans)
            )
        ]
        if "name" in port:
            shapes.append(cell.shapes(lidx).insert(trans.trans(pya.DText(port["name"], pya.DTrans()))))
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
