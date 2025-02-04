from .export_base import NetworkInfoExportBase
import numpy as np
import math
import os.path
from sys import platform

class NetworkInfoExportToFigureBase(NetworkInfoExportBase):
    def __init__(self):
        super().__init__()
        self.compartment_layer = 0
        self.compartment_text_layer = 1
        self.species_reference_layer = 2
        self.line_ending_layer = 3
        self.reaction_layer = 4
        self.reaction_text_layer = 6
        self.species_layer = 5
        self.species_text_layer = 6
        self.additional_graphical_object_layer = 7
        self.additional_graphical_object_text_layer = 8

    def reset(self):
        super().reset()

    def set_background(self, graph_info):
        self.draw_background_canvas(graph_info.background_color)

    def add_compartment(self, compartment):
        # compartment
        if 'features' in list(compartment.keys()):
            self.add_graphical_shape_to_scene(compartment['features'], layer=self.compartment_layer)
        # compartment text
        if 'texts' in list(compartment.keys()):
            for text in compartment['texts']:
                if 'features' in list(text.keys()):
                    self.add_text_to_scene(text['features'], layer=self.compartment_text_layer)

    def add_species(self, species):
        # species
        if 'features' in list(species.keys()):
            self.add_graphical_shape_to_scene(species['features'], layer=self.species_layer)
        # species text
        if 'texts' in list(species.keys()):
            for text in species['texts']:
                if 'features' in list(text.keys()):
                    self.add_text_to_scene(text['features'], layer=self.species_text_layer)

    def add_reaction(self, reaction):
        # reaction
        if 'features' in list(reaction.keys()):
            # reaction curve
            if 'curve' in list(reaction['features']):
                self.add_curve_to_scene(reaction['features'], offset_x=0.0, offset_y=0.0, slope=0.0, layer=self.reaction_layer, sublayer=0)
            # reaction graphical shape
            elif 'boundingBox' in list(reaction['features']):
                self.add_graphical_shape_to_scene(reaction['features'], layer=self.reaction_layer)
        # reaction text
        if 'texts' in list(reaction.keys()):
            for text in reaction['texts']:
                if 'features' in list(text.keys()):
                    self.add_text_to_scene(text['features'], layer=self.reaction_text_layer)

        # species references
        if 'speciesReferences' in list(reaction.keys()):
            for sr in reaction['speciesReferences']:
                self.add_species_reference(sr)

    def add_species_reference(self, species_reference):
        if 'features' in list(species_reference.keys()):
            # species reference
            self.add_curve_to_scene(species_reference['features'], offset_x=0.0, offset_y=0.0, slope=0.0, layer=self.species_reference_layer, sublayer=0)

            # line endings
            self.add_line_endings_to_scene(species_reference['features'])

    def add_additional_graphical_object(self, additional_graphical_object):
        # additional graphical object
        if 'features' in list(additional_graphical_object.keys()):
            self.add_graphical_shape_to_scene(additional_graphical_object['features'], layer=self.additional_graphical_object_layer)
        # additional graphical object text
        if 'texts' in list(additional_graphical_object.keys()):
            for text in additional_graphical_object['texts']:
                if 'features' in list(text.keys()):
                    self.add_text_to_scene(text['features'], layer=self.additional_graphical_object_text_layer)

    def add_graphical_shape_to_scene(self, features, offset_x=0.0, offset_y=0.0, slope=0.0, layer=0):
        if 'boundingBox' in list(features.keys()):
            if (offset_x or offset_y) and slope:
                offset_x += 1.5 * math.cos(slope)
                offset_y += 1.5 * math.sin(slope)
            bbox_x = features['boundingBox']['x']
            bbox_y = features['boundingBox']['y']
            bbox_width = features['boundingBox']['width']
            bbox_height = features['boundingBox']['height']

            # default features
            stroke_color = 'black'
            stroke_width = 1.0
            stroke_dash_array = tuple()
            fill_color = 'white'
            if 'graphicalShape' in list(features.keys()):
                if 'strokeColor' in list(features['graphicalShape'].keys()):
                    stroke_color = features['graphicalShape']['strokeColor']
                if 'strokeWidth' in list(features['graphicalShape'].keys()):
                    stroke_width = features['graphicalShape']['strokeWidth']
                if 'strokeDashArray' in list(features['graphicalShape'].keys()):
                    stroke_dash_array = features['graphicalShape']['strokeDashArray']
                if 'fillColor' in list(features['graphicalShape'].keys()):
                    fill_color = features['graphicalShape']['fillColor']

                if 'geometricShapes' in list(features['graphicalShape'].keys()):
                    for gs_index in range(len(features['graphicalShape']['geometricShapes'])):
                        if 'strokeColor' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                            stroke_color = features['graphicalShape']['geometricShapes'][gs_index]['strokeColor']
                        if 'strokeWidth' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                            stroke_width = features['graphicalShape']['geometricShapes'][gs_index]['strokeWidth']
                        if 'strokeDashArray' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                            stroke_dash_array = features['graphicalShape']['geometricShapes'][gs_index]['strokeDashArray']
                        if 'fillColor' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                            fill_color = features['graphicalShape']['geometricShapes'][gs_index]['fillColor']

                        # draw an image
                        if features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'image':
                            image_x = bbox_x
                            image_y = bbox_y
                            image_width = bbox_width
                            image_height = bbox_height
                            if 'x' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                image_x += features['graphicalShape']['geometricShapes'][gs_index]['x']['abs'] + \
                                              0.01 * features['graphicalShape']['geometricShapes'][gs_index]['x']['rel'] * image_width
                            if 'y' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                image_y += features['graphicalShape']['geometricShapes'][gs_index]['y']['abs'] + \
                                              0.01 * features['graphicalShape']['geometricShapes'][gs_index]['y']['rel'] * image_height
                            if 'width' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                image_width = features['graphicalShape']['geometricShapes'][gs_index]['width']['abs'] + \
                                                  0.01 * features['graphicalShape']['geometricShapes'][gs_index]['width']['rel'] * image_width
                            if 'height' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                image_height = features['graphicalShape']['geometricShapes'][gs_index]['height']['abs'] + \
                                               0.01 * features['graphicalShape']['geometricShapes'][gs_index]['height']['rel'] * image_height
                            if 'href' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                self.draw_image(href, image_x, image_y, image_width, image_height,
                                            offset_x, offset_y, slope, layer, gs_index)

                        # draw a render curve
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'renderCurve':
                            curve_features = {'graphicalCurve': {'strokeColor': stroke_color,
                                                                 'strokeWidth': stroke_width,
                                                                 'strokeDashArray': stroke_dash_array}}

                            # add a render curve to plot
                            if 'vertices' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                curve_features['curve'] = []
                                for v_index in range(len(features['graphicalShape']['geometricShapes'][gs_index]['vertices']) - 1):
                                    element_ = {'startX': features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['renderPointX']['abs'] +
                                                          0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['renderPointX'][
                                                              'rel'] * bbox_width + bbox_x,
                                                'startY': features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['renderPointY']['abs'] +
                                                          0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['renderPointY'][
                                                              'rel'] * bbox_height + bbox_y,
                                                'endX': features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index + 1]['renderPointX']['abs'] +
                                                        0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index + 1]['renderPointX'][
                                                            'rel'] * bbox_width + bbox_x,
                                                'endY': features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index + 1]['renderPointY']['abs'] +
                                                        0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index + 1]['renderPointY'][
                                                            'rel'] * bbox_height + bbox_y}

                                    if 'basePoint1X' in list(features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index].keys()):
                                        element_ = {
                                            'basePoint1X': features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['basePoint1X']['abs'] +
                                                           0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['basePoint1X'][
                                                               'rel'] * bbox_width + bbox_x,
                                            'basePoint1Y': features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['basePoint1Y']['abs'] +
                                                           0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['basePoint1Y'][
                                                               'rel'] * bbox_height + bbox_y,
                                            'basePoint2X': features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['basePoint2X']['abs'] +
                                                           0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['basePoint2X'][
                                                               'rel'] * bbox_width + bbox_x,
                                            'basePoint2Y': features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['basePoint2Y']['abs'] +
                                                           0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]['basePoint2Y'][
                                                               'rel'] * bbox_height + bbox_y}
                                    curve_features['curve'].append(element_)
                                self.add_curve_to_scene(curve_features, offset_x, offset_y, slope, layer, gs_index)

                        # draw a rounded rectangle
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'rectangle':
                            position_x = bbox_x
                            position_y = bbox_y
                            dimension_width = bbox_width
                            dimension_height = bbox_height
                            corner_radius_x = 0.0
                            corner_radius_y = 0.0

                            if 'x' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                position_x += features['graphicalShape']['geometricShapes'][gs_index]['x']['abs'] + \
                                              0.01 * features['graphicalShape']['geometricShapes'][gs_index]['x']['rel'] * bbox_width
                            if 'y' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                position_y += features['graphicalShape']['geometricShapes'][gs_index]['y']['abs'] + \
                                              0.01 * features['graphicalShape']['geometricShapes'][gs_index]['y']['rel'] * bbox_height
                            if 'width' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                dimension_width = features['graphicalShape']['geometricShapes'][gs_index]['width']['abs'] + \
                                                  0.01 * features['graphicalShape']['geometricShapes'][gs_index]['width']['rel'] * bbox_width
                            if 'height' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                dimension_height = features['graphicalShape']['geometricShapes'][gs_index]['height']['abs'] + \
                                                   0.01 * features['graphicalShape']['geometricShapes'][gs_index]['height']['rel'] * bbox_height
                            if 'ratio' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()) and \
                                    features['graphicalShape']['geometricShapes'][gs_index]['ratio'] > 0.0:
                                if (bbox_width / bbox_height) <= features['graphicalShape']['geometricShapes'][gs_index]['ratio']:
                                    dimension_width = bbox_width
                                    dimension_height = bbox_width / features['graphicalShape']['geometricShapes'][gs_index]['ratio']
                                    position_y += 0.5 * (bbox_height - dimension_height)
                                else:
                                    dimension_height = bbox_height
                                    dimension_width = features['graphicalShape']['geometricShapes'][gs_index]['ratio'] * bbox_height
                                    position_x += 0.5 * (bbox_width - dimension_width)
                            if 'rx' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                corner_radius_x = features['graphicalShape']['geometricShapes'][gs_index]['rx']['abs'] + \
                                                0.01 * features['graphicalShape']['geometricShapes'][gs_index]['rx']['rel'] * 0.5 * (bbox_width + bbox_height)
                            elif 'ry' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                corner_radius_y = features['graphicalShape']['geometricShapes'][gs_index]['ry']['abs'] + \
                                                0.01 * features['graphicalShape']['geometricShapes'][gs_index]['ry']['rel'] * 0.5 * (bbox_width + bbox_height)

                            self.draw_rounded_rectangle(position_x, position_y, dimension_width, dimension_height,
                                                        stroke_color, stroke_width, stroke_dash_array, fill_color,
                                                        corner_radius_x, corner_radius_y, offset_x, offset_y, slope, layer, gs_index)

                        # draw an ellipse
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'ellipse':
                            position_cx = bbox_x
                            position_cy = bbox_y
                            dimension_rx = 0.5 * bbox_width
                            dimension_ry = 0.5 * bbox_height

                            if 'cx' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                position_cx += features['graphicalShape']['geometricShapes'][gs_index]['cx']['abs'] +\
                                               0.01 * features['graphicalShape']['geometricShapes'][gs_index]['cx']['rel'] * bbox_width
                            if 'cy' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                position_cy += features['graphicalShape']['geometricShapes'][gs_index]['cy']['abs'] +\
                                               0.01 * features['graphicalShape']['geometricShapes'][gs_index]['cy']['rel'] * bbox_height
                            if 'rx' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                dimension_rx = features['graphicalShape']['geometricShapes'][gs_index]['rx']['abs'] +\
                                               0.01 * features['graphicalShape']['geometricShapes'][gs_index]['rx']['rel'] * bbox_width
                            if 'ry' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                dimension_ry = features['graphicalShape']['geometricShapes'][gs_index]['ry']['abs'] + \
                                               0.01 * features['graphicalShape']['geometricShapes'][gs_index]['ry']['rel'] * bbox_height
                            if 'ratio' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()) and features['graphicalShape']['geometricShapes'][gs_index]['ratio'] > 0.0:
                                if (bbox_width / bbox_height) <= features['graphicalShape']['geometricShapes'][gs_index]['ratio']:
                                    dimension_rx = 0.5 * bbox_width
                                    dimension_ry = (0.5 * bbox_width / features['graphicalShape']['geometricShapes'][gs_index]['ratio'])
                                else:
                                    dimension_ry = 0.5 * bbox_height
                                    dimension_rx = features['graphicalShape']['geometricShapes'][gs_index]['ratio'] * 0.5 * bbox_height
                            self.draw_ellipse(position_cx, position_cy, dimension_rx, dimension_ry,
                                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                                              offset_x, offset_y, slope, layer, gs_index)

                        # draw a polygon
                        elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'polygon':
                            if 'vertices' in list(features['graphicalShape']['geometricShapes'][gs_index].keys()):
                                vertices = np.empty((0, 2))
                                origin_x = bbox_x
                                origin_y = bbox_y
                                for v_index in range(len(features['graphicalShape']['geometricShapes'][gs_index]['vertices'])):
                                    vertices = np.append(vertices,
                                                         np.array([[features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]
                                                                    ['renderPointX']['abs'] +
                                                                    0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]
                                                                    ['renderPointX']['rel'] * bbox_width + origin_x,
                                                                    features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]
                                                                    ['renderPointY']['abs'] +
                                                                    0.01 * features['graphicalShape']['geometricShapes'][gs_index]['vertices'][v_index]
                                                                    ['renderPointY']['rel'] * bbox_height + origin_y]]), axis=0)
                                self.draw_polygon(vertices,
                                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                                              offset_x, offset_y, slope, layer, gs_index)

                else:
                    self.draw_simple_rectangle(features['graphicalShape']['geometricShapes'][gs_index],
                                               bbox_x, bbox_y, bbox_width, bbox_height,
                                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                                               offset_x, offset_y, slope, layer, 0)

    def add_curve_to_scene(self, features, offset_x, offset_y, slope, layer, sublayer):
        if 'curve' in list(features.keys()):
            # default features
            stroke_color = 'black'
            stroke_width = 1.0
            stroke_dash_array = 'solid'

            if 'graphicalCurve' in list(features.keys()):
                if 'strokeColor' in list(features['graphicalCurve'].keys()):
                    stroke_color = features['graphicalCurve']['strokeColor']
                if 'strokeWidth' in list(features['graphicalCurve'].keys()):
                    stroke_width = features['graphicalCurve']['strokeWidth']
                if 'strokeDashArray' in list(features['graphicalCurve'].keys()) \
                        and not features['graphicalCurve']['strokeDashArray'] == 'solid':
                    stroke_dash_array = features['graphicalCurve']['strokeDashArray']

            self.draw_curve(features['curve'], stroke_color, stroke_width, stroke_dash_array, offset_x, offset_y, slope, layer, sublayer)

    def add_text_to_scene(self, features, layer, sublayer = 0):
        if 'plainText' in list(features.keys()) and 'boundingBox' in list(features.keys()):
            plain_text = features['plainText']
            bbox_x = features['boundingBox']['x']
            bbox_y = features['boundingBox']['y']
            bbox_width = features['boundingBox']['width']
            bbox_height = features['boundingBox']['height']

            # default features
            font_color = 'black'
            font_family = 'monospace'
            font_size = 12.0
            font_style = 'normal'
            font_weight = 'normal'
            h_text_anchor = 'center'
            v_text_anchor = 'center'

            if 'graphicalText' in list(features.keys()):
                if 'strokeColor' in list(features['graphicalText'].keys()):
                    font_color = self.graph_info.find_color_value(features['graphicalText']['strokeColor'], False)
                if 'fontFamily' in list(features['graphicalText'].keys()):
                    font_family = features['graphicalText']['fontFamily']
                if 'fontSize' in list(features['graphicalText'].keys()):
                    font_size = features['graphicalText']['fontSize']['abs'] + \
                                0.01 * features['graphicalText']['fontSize']['rel'] * bbox_width
                if 'fontStyle' in list(features['graphicalText'].keys()):
                    font_style = features['graphicalText']['fontStyle']
                if 'fontWeight' in list(features['graphicalText'].keys()):
                    font_weight = features['graphicalText']['fontWeight']
                if 'hTextAnchor' in list(features['graphicalText'].keys()):
                    if features['graphicalText']['hTextAnchor'] == 'start':
                        h_text_anchor = 'left'
                    elif features['graphicalText']['hTextAnchor'] == 'middle':
                        h_text_anchor = 'center'
                    elif features['graphicalText']['hTextAnchor'] == 'end':
                        h_text_anchor = 'right'
                if 'vTextAnchor' in list(features['graphicalText'].keys()):
                    if features['graphicalText']['vTextAnchor'] == 'middle':
                        v_text_anchor = 'center'
                    else:
                        v_text_anchor = features['graphicalText']['vTextAnchor']

                # get geometric shape features
                if 'geometricShapes' in list(features['graphicalText'].keys()):
                    for gs_index in range(len(features['graphicalText']['geometricShapes'])):
                        position_x = bbox_x
                        position_y = bbox_y

                        if 'x' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            position_x += features['graphicalText']['geometricShapes'][gs_index]['x']['abs'] + \
                                          0.01 * features['graphicalText']['geometricShapes'][gs_index]['x']['rel'] \
                                          * bbox_width
                        if 'y' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            position_y += features['graphicalText']['geometricShapes'][gs_index]['y']['abs'] + \
                                          0.01 * features['graphicalText']['geometricShapes'][gs_index]['y']['rel'] \
                                          * bbox_height
                        if 'strokeColor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_color = self.graph_info.find_color_value(features['graphicalText']
                                                                          ['geometricShapes'][gs_index]['strokeColor'],
                                                                          False)
                        if 'fontFamily' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_family = features['graphicalText']['geometricShapes'][gs_index]['fontFamily']
                        if 'fontSize' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_size = features['graphicalText']['geometricShapes'][gs_index]['fontSize']['abs'] + \
                                        0.01 * features['graphicalText']['geometricShapes'][gs_index]['fontSize']['rel'] \
                                        * bbox_width
                        if 'fontStyle' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_style = features['graphicalText']['geometricShapes'][gs_index]['fontStyle']
                        if 'fontWeight' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            font_weight = features['graphicalText']['geometricShapes'][gs_index]['fontWeight']
                        if 'hTextAnchor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            if features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'start':
                                h_text_anchor = 'left'
                            elif features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'middle':
                                h_text_anchor = 'center'
                            elif features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'end':
                                h_text_anchor = 'right'
                        if 'vTextAnchor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                            if features['graphicalText']['geometricShapes'][gs_index]['vTextAnchor'] == 'middle':
                                v_text_anchor = 'center'
                            else:
                                v_text_anchor = features['graphicalText']['geometricShapes'][gs_index]['vTextAnchor']

                        self.draw_text(position_x, position_y, bbox_width, bbox_height,
                                       plain_text, font_color, font_family, font_size, font_style, font_weight,
                                       v_text_anchor, h_text_anchor, layer, sublayer)
                else:
                    self.draw_text(bbox_x, bbox_y, bbox_width, bbox_height,
                                   plain_text, font_color, font_family, font_size, font_style, font_weight,
                                   v_text_anchor, h_text_anchor, layer, sublayer)

    def add_line_endings_to_scene(self, features):
        if 'graphicalCurve' in list(features.keys()) and 'heads' in list(features['graphicalCurve'].keys()):
            # draw start head
            if 'start' in list(features['graphicalCurve']['heads'].keys()):
                line_ending = self.graph_info.find_line_ending(features['graphicalCurve']['heads']['start'])
                if line_ending and 'features' in list(line_ending.keys()):
                    if 'enableRotation' in list(line_ending['features'].keys()) \
                            and not line_ending['features']['enableRotation']:
                        self.add_graphical_shape_to_scene(line_ending['features'],
                                                          offset_x=features['startPoint']['x'],
                                                          offset_y=features['startPoint']['y'], layer=self.line_ending_layer)
                    else:
                        self.add_graphical_shape_to_scene(line_ending['features'],
                                                          offset_x=features['startPoint']['x'],
                                                          offset_y=features['startPoint']['y'],
                                                          slope=features['startSlope'], layer=self.line_ending_layer)

            # draw end head
            if 'end' in list(features['graphicalCurve']['heads'].keys()):
                line_ending = self.graph_info.find_line_ending(features['graphicalCurve']['heads']['end'])
                if line_ending and 'features' in list(line_ending.keys()):
                    if 'enableRotation' in list(line_ending['features'].keys()) \
                            and not line_ending['features']['enableRotation']:
                        self.add_graphical_shape_to_scene(ax, line_ending['features'],
                                                          offset_x=features['endPoint']['x'],
                                                          offset_y=features['endPoint']['y'], layer=self.line_ending_layer)
                    else:
                        self.add_graphical_shape_to_scene(line_ending['features'],
                                                          offset_x=features['endPoint']['x'],
                                                          offset_y=features['endPoint']['y'],
                                                          slope=features['endSlope'], layer=self.line_ending_layer)

    def draw_background_canvas(self, background_color):
        pass

    def draw_image(self, x, y, width, height,
                   offset_x, offset_y, slope, layer, sublayer):
        pass

    def draw_rounded_rectangle(self, x, y, width, height,
                               stroke_color, stroke_width, stroke_dash_array, fill_color,
                               corner_radius_x, corner_radius_y, offset_x, offset_y, slope, layer, sublayer):
        pass

    def draw_simple_rectangle(self, bbox_x, bbox_y, bbox_width, bbox_height,
                              stroke_color, stroke_width, stroke_dash_array, fill_color,
                              offset_x, offset_y, slope, layer, sublayer):
        pass

    def draw_ellipse(self, cx, cy, rx, ry,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, layer, sublayer):
        pass

    def draw_polygon(self, vertices,
                     stroke_color, stroke_width, stroke_dash_array, fill_color,
                     offset_x, offset_y, slope, layer, sublayer):
        pass

    def draw_curve(self, curve_points, stroke_color, stroke_width, stroke_dash_array, offset_x, offset_y, slope, layer, sublayer):
        pass

    def draw_text(self, position_x, position_y, bbox_width, bbox_height,
                  plain_text, font_color, font_family, font_size, font_style, font_weight,
                  v_text_anchor, h_text_anchor, layer, sublayer):
        pass

    @staticmethod
    def get_output_name(self, file_directory, file_name, file_format):
        if not os.path.isdir(file_directory):
            if os.path.isfile(file_directory):
                if not file_name:
                    if len(os.path.basename(file_directory).split('.')) == 2:
                        file_name = os.path.basename(file_directory).split('.')[0]
                    else:
                        file_name = os.path.basename(file_directory)
                if not file_format \
                        and len(file_directory.split('.')) == 2 \
                        and file_directory.split('.')[1] in [".pdf", ".svg", ".png", "jpg"]:
                    file_format = file_directory.split('.')[1]
                file_directory = os.path.dirname(file_directory)
            else:
                file_directory = "."
        if not file_name:
            file_name = "network"
        if file_format not in ["pdf", "svg", "png", "jpg"]:
            file_format = "png"

        if platform == "win32":
            return file_directory + "\\" + file_name + "." + file_format
        else:
            return file_directory + "/" + file_name + "." + file_format
