import os

from qgis.core import QgsProject, QgsMapLayer


def saveLeafletMap(with_slider_range):
    print("Save leaflet")
    project = QgsProject.instance()
    dir = project.readEntry("qgis2web", "Exportfolder")[0]
    print(dir)
    root, dirs, files = next(os.walk(dir))
    latest_subdir = max((os.path.getctime(os.path.join(root, f)), f) for f in dirs)
    index = os.path.join(dir, latest_subdir[1], 'index.html')
    html = open(index, 'r').read()
    html = addLeafletHeader(html, with_slider_range)
    html = changeLeafletStyles(html)
    index_time = os.path.join(dir, latest_subdir[1], 'index_time.html')
    f = open(index_time, 'w')
    f.write(html)
    f.close()


def addLeafletHeader(html, with_slider_range):
    project = QgsProject.instance()
    mintime = project.readEntry("qgis2web", "Min")[0]
    maxtime = project.readEntry("qgis2web", "Max")[0]

    header = '<script src="http://code.jquery.com/jquery-1.11.1.min.js"></script>\n'
    header += '<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.2/themes/smoothness/jquery-ui.css" />\n'
    header += '<script src="https://code.jquery.com/ui/1.10.2/jquery-ui.js"></script>\n'
    header += '<div style="position: fixed; top: 10px; left: 70px;"><div id="slider-range" style="width:300px"></div>\n'
    header += '<p><input id="datefrom"/>   <input id="dateto"/> </p>\n'
    header += '</div>\n'

    header += "<script>\n"
    header += "function getDateString(d) {\n"
    header += "m = d.getMonth() + 1;\n"
    header += "month = String('0' + m).slice(-2);\n"
    header += "day = String('0' + d.getDate()).slice(-2);\n"
    header += "return d.getFullYear() + '-' + month + '-' + day;\n"
    header += "}\n"
    header += "$(document).ready(function() {\n"
    header += "$( '#slider-range' ).slider({\n"
    if with_slider_range:
        header += "range: true,\n"
    else:
        header += "range: false,\n"
    header += "range: true,\n"
    header += "min: new Date('" + mintime + "').getTime() / 1000,\n"
    header += "max: new Date('" + maxtime + "').getTime() / 1000,\n"
    header += "step: 86400,\n"
    header += "values: [ new Date('" + mintime + "').getTime() / 1000, new Date('" + maxtime + "').getTime() / 1000 ],\n"
    header += "slide: function( event, ui ) {\n"
    header += "var from = new Date(ui.values[0] *1000);\n"
    header += "var to = new Date(ui.values[1] *1000);\n"
    header += "$( '#datefrom' ).val(getDateString(new Date(ui.values[0] *1000)));\n"
    if with_slider_range:
        header += "$( '#dateto' ).val(getDateString(new Date(ui.values[1] *1000)));\n"
    else:
        header += "$( '#dateto' ).val(getDateString(new Date(ui.values[0] *1000)));\n"
    header += "setVisibility();\n"
    header += "}\n"
    header += "});\n"

    header += "var from = new Date($('#slider-range').slider('values', 0)*1000);\n"
    header += "var to = new Date($('#slider-range').slider('values', 1)*1000);\n"
    header += "$( '#datefrom' ).val(getDateString(from));\n"
    header += "$( '#dateto' ).val(getDateString(to));\n"
    header += "});\n"

    html = html.replace("<script>", header)
    return html


def changeLeafletStyles(html):
    root_node = QgsProject.instance().layerTreeRoot()
    tree_layers = root_node.findLayers()
    layerid = len(tree_layers) - 1
    layernames = []
    for tree_layer in tree_layers:
        layer = tree_layer.layer()
        if layer.type() == QgsMapLayer.VectorLayer:
            if (layer.customProperty("qgis2web/Time from") is not None and
                    layer.customProperty("qgis2web/Time to") is not None and
                    layer.customProperty("qgis2web/Time from") is not None and
                    layer.customProperty("qgis2web/Time to") is not None):
                start = html.find("function style_" + layer.name())
                flen = len("function style_") + len(layer.name())
                layeridstr = html[start + flen:start + flen + 2]
                layernames.append(layer.name() + layeridstr)
                start2 = html.find("{", start + 1)
                end = html.find("}", start + 1)
                style = html[start2 + 1:end]
                style = style.replace("return", "s = ") + "\n};"
                end = html.find("}", end + 1)
                style = "function style_" + layer.name() + layeridstr + "_0(feature) {" + "\n" + style

                field_from = layer.fields()[int(layer.customProperty("qgis2web/Time from")) - 1].name()
                field_to = layer.fields()[int(layer.customProperty("qgis2web/Time to")) - 1].name()

                style += "var featuredatefrom = String(feature.properties." + field_from + ");\n"
                style += "var featuredateto = String(feature.properties." + field_to + ");\n"
                style += "if (featuredatefrom.length == 4) { featuredatefrom = featuredatefrom + '-01-01'; }\n"
                style += "if (featuredatefrom.length == 7) { featuredatefrom = featuredatefrom + '-01'; }\n"
                style += "if (featuredateto.length == 4) { featuredateto = featuredateto + '-01-01'; }\n"
                style += "if (featuredateto.length == 7) { featuredateto = featuredateto + '-01'; }\n"
                style += "if (\n"
                style += "(featuredatefrom <= $('#datefrom').val() && featuredateto <= $('#datefrom').val())\n"
                style += "||\n"
                style += "(featuredatefrom >= $('#dateto').val() && featuredateto >= $('#dateto').val())\n"
                style += ") {\n"
                style += "s['opacity'] = 0.0;\n"
                style += "s['fillOpacity'] = 0.0;\n"
                style += "}\n"

                style += "return s;\n"
                style += "}\n"

                style += "function setVisibility" + layer.name() + layeridstr + "() {\n"
                style += "for (var row=0; row<1000; row++) {\n"
                style += "if ( typeof(layer_" + layer.name() + layeridstr + "._layers[row])=='undefined') continue;\n"
                style += "  s = style_" + layer.name() + layeridstr + "_0(layer_" + layer.name() + layeridstr + "._layers[row].feature);\n"
                style += "  layer_" + layer.name() + layeridstr + "._layers[row].setStyle(s);\n"
                style += " }\n"
                style += "}\n"
                html = html[:start] + style + html[end+1:]
                start = html.find("function doPointToLayer" + layer.name())
                if start != -1:
                    start = html.find("(", start + 1)
                    start = html.find("(", start + 1)
                    start = html.find("(", start + 1)
                    html = html[:start] + "(feature" + html[start+1:]
            layerid -= 1
    fvisibility = "function setVisibility() {\n"
    for layername in layernames:
        fvisibility += "setVisibility" + layername + "();\n"
    fvisibility += "}\n"
    html = html.replace("setBounds();", fvisibility + "setBounds();")
    return html


def saveOLMap(with_slider_range):
    print("Save OL")
    project = QgsProject.instance()
    dir = project.readEntry("qgis2web", "Exportfolder")[0]
    if dir == "":
        if os.path.isdir("/tmp/qgis2web"):
            dir = "/tmp/qgis2web"
        if os.path.isdir("C:\\TEMP\\qgis2web"):
            dir = "C:\\TEMP\\qgis2web"
    print(dir)
    root, dirs, files = next(os.walk(dir))
    latest_subdir = max((os.path.getctime(os.path.join(root, f)), f) for f in dirs)

    index = os.path.join(dir, latest_subdir[1], 'index.html')
    html = open(index, 'r').read()

    layernames = changeOLStyles(os.path.join(dir, latest_subdir[1], 'styles'))

    fvisibility = "function setVisibility() {\n"
    for layername in layernames:
        fvisibility += "lyr_" + layername + ".getSource().changed();\n"
    fvisibility += "}</script>\n"

    html = html.replace("_style.js", "_style_time.js")

    mintime = project.readEntry("qgis2web", "Min")[0]
    maxtime = project.readEntry("qgis2web", "Max")[0]
    header = '<head>\n<script src="http://code.jquery.com/jquery-1.11.1.min.js"></script>\n'
    header += '<script>\n'

    header += "function getDateString(d) {\n"
    header += "m = d.getMonth() + 1;\n"
    header += "month = String('0' + m).slice(-2);\n"
    header += "day = String('0' + d.getDate()).slice(-2);\n"
    header += "return d.getFullYear() + '-' + month + '-' + day;\n"
    header += "}\n"

    header += "$(document).ready(function() {\n"
    header += "$( '#slider-range' ).slider({\n"
    if with_slider_range:
        header += "range: true,\n"
    else:
        header += "range: false,\n"
    header += "range: true,\n"
    header += "min: new Date('" + mintime + "').getTime() / 1000,\n"
    header += "max: new Date('" + maxtime + "').getTime() / 1000,\n"
    header += "step: 86400,\n"
    header += "values: [ new Date('" + mintime + "').getTime() / 1000, new Date('" + maxtime + "').getTime() / 1000 ],\n"
    header += "slide: function( event, ui ) {\n"
    header += "var from = new Date(ui.values[0] *1000);\n"
    header += "var to = new Date(ui.values[1] *1000);\n"
    header += "$( '#datefrom' ).val(getDateString(new Date(ui.values[0] *1000)));\n"
    if with_slider_range:
        header += "$( '#dateto' ).val(getDateString(new Date(ui.values[1] *1000)));\n"
    else:
        header += "$( '#dateto' ).val(getDateString(new Date(ui.values[0] *1000)));\n"
    header += "setVisibility();\n"
    header += "}\n"
    header += "});\n"
    header += "var from = new Date($('#slider-range').slider('values', 0)*1000);\n"
    header += "var to = new Date($('#slider-range').slider('values', 1)*1000);\n"
    header += "$( '#datefrom' ).val(getDateString(from));\n"
    header += "$( '#dateto' ).val(getDateString(to));\n"
    header += "});\n"

    header += fvisibility
    html = html.replace("<head>", header)

    header = '<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.2/themes/smoothness/jquery-ui.css" />\n'
    header += '<script src="https://code.jquery.com/ui/1.10.2/jquery-ui.js"></script>\n'
    header += '<div style="position: fixed; top: 10px; left: 70px;"><div id="slider-range" style="width:300px"></div>\n'
    header += '<p><input id="datefrom"/>   <input id="dateto"/> </p>\n'
    header += '</div>\n'
    html = html.replace("</body>", header)

    index_time = os.path.join(dir, latest_subdir[1], 'index_time.html')
    f = open(index_time, 'w')
    f.write(html)
    f.close()


def changeOLStyles(path):
    root_node = QgsProject.instance().layerTreeRoot()
    tree_layers = root_node.findLayers()
    layerid = len(tree_layers) - 1
    layernames = []

    for tree_layer in tree_layers:
        layer = tree_layer.layer()
        if layer.type() == QgsMapLayer.VectorLayer:
            if (layer.customProperty("qgis2web/Time from") is not None and
                    layer.customProperty("qgis2web/Time to") is not None and
                    layer.customProperty("qgis2web/Time from") is not None and
                    layer.customProperty("qgis2web/Time to") is not None):
                stylefile = os.path.join(path, layer.name() + unicode(layerid) + "_style.js")
                styletimefile = os.path.join(path, layer.name() + unicode(layerid) + "_style_time.js")
                if not os.path.exists(stylefile):
                    stylefile = os.path.join(path, layer.name() + "_style.js")
                    styletimefile = os.path.join(path, layer.name() + "_style_time.js")
                else:
                    layernames.append(layer.name() + unicode(layerid))
                if not os.path.exists(stylefile):
                    stylefile = os.path.join(path, layer.name() + "_" + unicode(layerid) + "_style.js")
                    styletimefile = os.path.join(path, layer.name() + "_" + unicode(layerid) + "_style_time.js")
                    layernames.append(layer.name() + "_" + unicode(layerid))
                else:
                    layernames.append(layer.name())
                style = open(stylefile, 'r').read()
                start = style.find("var style =")
                end = style.find(";", start)
                styledef = style[start + 4:end + 1]
                field_from = layer.fields()[int(layer.customProperty("qgis2web/Time from")) - 1].name()
                field_to = layer.fields()[int(layer.customProperty("qgis2web/Time to")) - 1].name()
                stylevis = "var featuredatefrom = String(feature.get('" + field_from + "'));\n"
                stylevis += "var featuredateto = String(feature.get('" + field_to + "'));\n"
                stylevis += "if (featuredatefrom.length == 4) { featuredatefrom = featuredatefrom + '-01-01'; }\n"
                stylevis += "if (featuredatefrom.length == 7) { featuredatefrom = featuredatefrom + '-01'; }\n"
                stylevis += "if (featuredateto.length == 4) { featuredateto = featuredateto + '-01-01'; }\n"
                stylevis += "if (featuredateto.length == 7) { featuredateto = featuredateto + '-01'; }\n"
                stylevis += "if (\n"
                stylevis += "(featuredatefrom <= $('#datefrom').val() && featuredateto <= $('#datefrom').val())\n"
                stylevis += "||\n"
                stylevis += "(featuredatefrom >= $('#dateto').val() && featuredateto >= $('#dateto').val())\n"
                stylevis += ") {\n"
                stylevis += styledef.replace("1.0", "0.0") + "\n"
                stylevis += "}\n"
                style = style[:end + 1] + stylevis + style[end + 2:]
                f = open(styletimefile, 'w')
                f.write(style)
                f.close()
            layerid -= 1
    return layernames
