from .import_base import NetworkInfoImportBase

import json
import math


class NetworkInfoImportFromEscher(NetworkInfoImportBase):
    def __init__(self):
        super().__init__()
        self._primary_nodoes = []
        self._multimarker_nodes = {}

    def extract_info(self, graph):
        super().extract_info(graph)

        with open(graph, 'r') as file:
            self.graph_info = json.load(file)
        self._extract_extents(self.graph_info)
        self._extract_entities(self.graph_info)

    def _extract_extents(self, graph_info):
        for item in graph_info:
            if 'canvas' in item:
                canvas = item['canvas']
                if 'x' in list(canvas.keys()):
                    self.extents['minX'] = canvas['x']
                if 'y' in list(canvas.keys()):
                    self.extents['minY'] = canvas['y']
                if 'width' in list(canvas.keys()):
                    self.extents['maxX'] = self.extents['minX'] + canvas['width']
                if 'height' in list(canvas.keys()):
                    self.extents['maxY'] = self.extents['minY'] + canvas['height']

    def _extract_entities(self, graph_info):
        self.compartments.append(self._create_default_compartment())
        for item in graph_info:
            if 'nodes' in item:
                self._extract_nodes(item['nodes'])
            if 'reactions' in item:
                self._extract_reactions(item['reactions'])

    def _extract_nodes(self, nodes):
        for node_id in nodes:
            if 'node_type' in list(nodes[node_id].keys()):
                self._extract_node(nodes[node_id], node_id)

    def _extract_node(self, node_info, node_id):
        node_type = node_info['node_type']
        if node_type == 'metabolite':
            self._extract_metabolite_node(node_info, node_id)
        elif node_type == 'midmarker':
            self._extract_midmarker_node(node_info, node_id)
        elif node_type == "multimarker":
            self._extract_multimarker_node(node_info, node_id)

    def _extract_metabolite_node(self, node_info, node_id):
        sbml_node = self._extract_sbml_node(node_info, node_id)
        sbml_node['texts'] = self._extract_sbml_node_texts(node_info, sbml_node['features'], node_id)
        sbml_node['compartment'] = self._get_default_compartment_id()
        self.species.append(sbml_node)

    def _extract_midmarker_node(self, node_info, node_id):
        sbml_node = self._extract_sbml_node(node_info, node_id)
        self.reactions.append(sbml_node)

    def _extract_multimarker_node(self, node_info, node_id):
        self._multimarker_nodes.update({self._get_sbml_sid_compatible_id(node_id): None})

    def _extract_reactions(self, reactions):
        for reaction_id in reactions:
            self._extract_sbml_reaction(reactions[reaction_id], reaction_id)

    def _extract_sbml_node(self, node_info, node_id):
        sbml_node = {'id': self._get_sbml_sid_compatible_id(node_id)}
        if 'bigg_id' in list(node_info.keys()):
            sbml_node['referenceId'] = self._get_sbml_sid_compatible_id(node_info['bigg_id'])
        sbml_node['features'] = self._extract_sbml_node_features(node_info)
        self._add_to_primary_node_list(node_info, node_id)
        return sbml_node

    def _add_to_primary_node_list(self, node_info, node_id):
        if self._is_primary_node(node_info):
            self._primary_nodoes.append(node_id)

    def _extract_sbml_node_features(self, node_info):
        features = {'boundingBox': {}}
        node_type = node_info['node_type']
        features['boundingBox']['width'] = self._extract_sbml_node_width(node_info, node_type)
        features['boundingBox']['height'] = self._extract_sbml_node_height(node_info, node_type)
        features['boundingBox']['x'] = self._extract_sbml_node_x(node_info, features['boundingBox']['width'])
        features['boundingBox']['y'] = self._extract_sbml_node_y(node_info, features['boundingBox']['height'])

        return features

    def _extract_sbml_node_width(self, node_info, node_type):
        if 'width' in list(node_info.keys()):
            return node_info['width']
        if node_type == 'metabolite':
            return self._get_default_metabolite_width(node_info)
        elif node_type == 'midmarker':
            return self._get_default_midmarker_width()

        return 0.0

    def _extract_sbml_node_height(self, node_info, node_type):
        if 'height' in list(node_info.keys()):
            return node_info['height']
        if node_type == 'metabolite':
            return self._get_default_metabolite_height(node_info)
        elif node_type == 'midmarker':
            return self._get_default_midmarker_height()

        return 0.0

    @staticmethod
    def _extract_sbml_node_x(node_info, width):
        if 'x' in list(node_info.keys()):
            return node_info['x'] - 0.5 * width

        return 0

    @staticmethod
    def _extract_sbml_node_y(node_info, height):
        if 'y' in list(node_info.keys()):
            return node_info['y'] - 0.5 * height

    def _extract_sbml_node_texts(self, node_info, node_features, node_id):
        texts = []
        if 'name' in list(node_info.keys()):
            texts.append({'id': self._get_sbml_sid_compatible_id(node_id) + "_TextGlyph_1",
                          'features': self._extract_sbml_node_text_features(node_info, node_features)})

        return texts

    def _extract_sbml_node_text_features(self, node_info, node_features):
        bounding_box = {'width': self._extract_sbml_node_text_width(node_features, node_info),
                        'height': self._extract_sbml_node_text_height(node_features, node_info),
                        'x': self._extract_sbml_node_text_x(node_info, node_features),
                        'y': self._extract_sbml_node_text_y(node_info, node_features)}
        # todo escher website examples show bigg_id as plainText, so we don't pass name as plainText (might need to be changed)
        return {'plainText': node_info['bigg_id'], 'boundingBox': bounding_box}

    def _extract_sbml_node_text_width(self, node_features, node_info):
        if 'node_type' in list(node_info.keys()) and node_info['node_type'] == 'metabolite':
            return node_features['boundingBox']['width']

        return self._get_default_reaction_text_width()

    def _extract_sbml_node_text_height(self, node_features, node_info):
        if 'node_type' in list(node_info.keys()) and node_info['node_type'] == 'metabolite':
            return node_features['boundingBox']['height']

        return self._get_default_reaction_text_height()

    def _extract_sbml_node_text_x(self, node_info, node_features):
        x = node_features['boundingBox']['x'] - 0.5 * node_features['boundingBox']['width']
        if 'label_x' in list(node_info.keys()):
            x = node_info['label_x'] - 0.5 * node_features['boundingBox']['width']
            if 'node_type' in list(node_info.keys()) and node_info['node_type'] == 'metabolite':
                x += self._get_species_text_horizontal_padding()
            else:
                x += self._get_reaction_text_horizontal_padding()

        return x

    def _extract_sbml_node_text_y(self, node_info, node_features):
        y = node_features['boundingBox']['y'] - 0.5 * node_features['boundingBox']['height']
        if 'label_y' in list(node_info.keys()):
            y = node_info['label_y'] - 0.5 * node_features['boundingBox']['height']
            if 'node_type' in list(node_info.keys()) and node_info['node_type'] == 'metabolite':
                y += self._get_species_text_vertical_padding()
            else:
                y += self._get_reaction_text_vertical_padding()

        return y

    def _extract_sbml_reaction(self, reaction_info, reaction_id):
        sbml_reaction = self._find_sbml_reaction(reaction_info, reaction_id)
        if sbml_reaction is not None:
            reaction_id = sbml_reaction['id']
            if 'bigg_id' in list(reaction_info.keys()):
                sbml_reaction['referenceId'] = self._get_sbml_sid_compatible_id(reaction_info['bigg_id'])
            sbml_reaction['texts'] = self._extract_sbml_node_texts(reaction_info, sbml_reaction['features'],
                                                                       reaction_id)
            sbml_reaction['speciesReferences'] = self._extract_sbml_reaction_species_references(reaction_info,
                                                                                                reaction_id)

    def _extract_sbml_reaction_species_references(self, reaction_info, reaction_id):
        species_references = []
        if 'segments' in list(reaction_info.keys()):
            segments = reaction_info['segments']
            self._set_multimarker_node_connected_midmarker(segments, reaction_id)
            for segment_id in segments:
                species_reference = self._extract_sbml_reaction_species_reference(segments[segment_id], reaction_id,
                                                                                  reaction_info)
                if species_reference:
                    species_references.append(species_reference)

        return species_references

    def _extract_sbml_reaction_species_reference(self, segment, reaction_id, reaction_info):
        species_reference = {}
        if 'from_node_id' in list(segment.keys()) and 'to_node_id' in list(segment.keys()):
            from_node = self._find_sbml_node(segment['from_node_id'])
            to_node = self._find_sbml_node(segment['to_node_id'])
            if from_node is not None and to_node is not None and from_node['id'] != to_node['id']:
                species_reference = self._initialize_species_reference(reaction_id, from_node, to_node)
                species_reference['features'] = self._extract_sbml_reaction_species_reference_features(
                    from_node, to_node, segment, reaction_id)

        return species_reference

    @staticmethod
    def _get_species_reference_reaction_node(from_node, to_node, reaction_id):
        if from_node['id'] == reaction_id:
            return from_node
        elif to_node['id'] == reaction_id:
            return to_node

        return None

    @staticmethod
    def _get_species_reference_species_node(from_node, to_node, reaction_id):
        if from_node['id'] == reaction_id:
            return to_node
        elif to_node['id'] == reaction_id:
            return from_node

        return None

    def _get_species_reference_role(self, from_node, to_node, reaction_id):
        if from_node['id'] == reaction_id:
            if to_node['id'] not in self._primary_nodoes:
                return "sideproduct"
            return "product"
        elif to_node['id'] == reaction_id:
            if from_node['id'] not in self._primary_nodoes:
                return "modifier"
            return "substrate"

        return ""

    def _initialize_species_reference(self, reaction_id, from_node, to_node):
        reaction = self._get_species_reference_reaction_node(from_node, to_node, reaction_id)
        species = self._get_species_reference_species_node(from_node, to_node, reaction_id)
        identification_features = {'role': self._get_species_reference_role(from_node, to_node, reaction_id),
                                   'reaction': reaction['referenceId'], 'reactionGlyphId': reaction['id'],
                                   'reactionGlyphIndex': 0, 'species': species['referenceId'],
                                   'speciesGlyphId': species['id'], 'speciesReferenceGlyphIndex': 0,
                                   'id': reaction['id'] + "_" + species['id'],
                                   'referenceId': reaction['referenceId'] + "_" + species['referenceId']}
        return identification_features

    def _extract_sbml_reaction_species_reference_features(self, from_go, to_go, segment, reaction_id):
        features = {'startPoint': self._get_species_reference_start_point(from_go, to_go, segment, reaction_id),
                    'startSlope': self._get_species_reference_start_slope(from_go, to_go, segment, reaction_id),
                    'endPoint': self._get_species_reference_end_point(from_go, to_go, segment, reaction_id),
                    'endSlope': self._get_species_reference_end_slope(from_go, to_go, segment, reaction_id),
                    'curve': self._get_curve(from_go, to_go, segment, reaction_id)}
        return features

    def _get_curve(self, from_go, to_go, segment, reaction_id):
        curve = []
        start_point = self._get_species_reference_start_point(from_go, to_go, segment, reaction_id)
        end_point = self._get_species_reference_end_point(from_go, to_go, segment, reaction_id)
        base_point1 = self._get_species_reference_base_point1(from_go, to_go, segment, reaction_id)
        base_point2 = self._get_species_reference_base_point2(from_go, to_go, segment, reaction_id)
        curve.append({'startX': start_point['x'], 'startY': start_point['y'],
                      'endX': end_point['x'], 'endY': end_point['y'],
                      'basePoint1X': base_point1['x'], 'basePoint1Y': base_point1['y'],
                      'basePoint2X': base_point2['x'], 'basePoint2Y': base_point2['y']})
        return curve

    def _get_species_reference_start_point(self, from_go, to_go, segment, reaction_id):
        start_node_center = self._get_center_point(from_go)
        base_point1 = self._get_species_reference_base_point1(from_go, to_go, segment, reaction_id)
        slope = self._calculate_slope(start_node_center, base_point1)
        radius = self._get_species_reference_start_node_radius(from_go, to_go, reaction_id)
        return {'x': start_node_center['x'] + radius * math.cos(slope),
                'y': start_node_center['y'] + radius * math.sin(slope)}

    def _get_species_reference_start_node_radius(self, from_go, to_go, reaction_id):
        species = self._get_species_reference_species_node(from_go, to_go, reaction_id)
        if 'id' in list(species.keys()) and species['id'] == from_go['id']:
            return self._get_default_species_radius(species)

        return 0.0

    def _get_species_reference_end_point(self, from_go, to_go, segment, reaction_id):
        end_node_center = self._get_center_point(to_go)
        base_point2 = self._get_species_reference_base_point2(from_go, to_go, segment, reaction_id)
        slope = self._calculate_slope(end_node_center, base_point2)
        radius = self._get_species_reference_end_node_radius(from_go, to_go, reaction_id)
        return {'x': end_node_center['x'] + radius * math.cos(slope),
                'y': end_node_center['y'] + radius * math.sin(slope)}

    def _get_species_reference_end_node_radius(self, from_go, to_go, reaction_id):
        species = self._get_species_reference_species_node(from_go, to_go, reaction_id)
        reaction = self._get_species_reference_reaction_node(from_go, to_go, reaction_id)
        if 'id' in list(species.keys()) and species['id'] == to_go['id']:
            return self._get_default_species_radius(species)
        # for modifiers, we want to set a distance between the end point and the reaction center
        elif species['id'] not in self._primary_nodoes and 'id' in list(reaction.keys()) and reaction['id'] == to_go[
            'id']:
            return 2 * self._get_default_reaction_radius()

        return 0.0

    def _get_species_reference_base_point1(self, from_go, to_go, segment, reaction_id):
        if 'b1' in list(segment.keys()):
            return segment['b1']

        return self._get_species_reference_start_point(from_go, to_go, segment, reaction_id)

    def _get_species_reference_base_point2(self, from_go, to_go, segment, reaction_id):
        if 'b2' in list(segment.keys()):
            return segment['b2']

        return self._get_species_reference_end_point(to_go, reaction_id)

    def _get_species_reference_start_slope(self, from_go, to_go, segment, reaction_id):
        if 'b1' in list(segment.keys()):
            first_point = segment['b1']
        else:
            first_point = self._get_species_reference_end_point(from_go, to_go, segment, reaction_id)
        second_point = self._get_species_reference_start_point(from_go, to_go, segment, reaction_id)

        return self._calculate_slope(first_point, second_point)

    def _get_species_reference_end_slope(self, from_go, to_go, segment, reaction_id):
        if 'b2' in list(segment.keys()):
            first_point = segment['b2']
        else:
            first_point = self._get_species_reference_start_point(from_go, to_go, segment, reaction_id)
        second_point = self._get_species_reference_end_point(from_go, to_go, segment, reaction_id)

        return self._calculate_slope(first_point, second_point)

    @staticmethod
    def _get_center_point(go):
        bounding_box = go['features']['boundingBox']
        return {'x': bounding_box['x'] + 0.5 * bounding_box['width'],
                'y': bounding_box['y'] + 0.5 * bounding_box['height']}

    @staticmethod
    def _calculate_slope(point1, point2):
        return math.atan2(point2['y'] - point1['y'], point2['x'] - point1['x'])

    def _set_multimarker_node_connected_midmarker(self, segments, reaction_id):
        reaction_id = self._get_sbml_sid_compatible_id(reaction_id)
        for segment_id in segments:
            if 'from_node_id' in list(segments[segment_id].keys()):
                from_node_id = self._get_sbml_sid_compatible_id(segments[segment_id]['from_node_id'])
                if from_node_id in list(self._multimarker_nodes.keys()):
                    self._multimarker_nodes[from_node_id] = reaction_id
            if 'to_node_id' in list(segments[segment_id].keys()):
                to_node_id = self._get_sbml_sid_compatible_id(segments[segment_id]['to_node_id'])
                if to_node_id in list(self._multimarker_nodes.keys()):
                    self._multimarker_nodes[to_node_id] = reaction_id

    def _create_default_compartment(self):
        compartment = {'id': self._get_default_compartment_id() + "_glyph1",
                       'referenceId': self._get_default_compartment_id(), 'index': 0,
                       'features': {'boundingBox': {'x': self.extents['minX'],
                                                    'y': self.extents['minY'],
                                                    'width': self.extents['maxX'] - self.extents[
                                                        'minX'],
                                                    'height': self.extents['maxY'] - self.extents[
                                                        'minY']}}}
        compartment['texts'] = self._create_default_compartment_texts(compartment['features'])
        return compartment

    def _create_default_compartment_texts(self, compartment_features):
        texts = []
        text = {'id': self._get_default_compartment_id() + "_TextGlyph_1",
                'features': self._create_default_compartment_text_features(compartment_features)}
        texts.append(text)
        return texts

    def _create_default_compartment_text_features(self, compartment_features):
        return {'plainText': self._get_default_compartment_id(), 'boundingBox': compartment_features['boundingBox']}

    @staticmethod
    def _get_default_compartment_id():
        return 'default_compartment'

    def _get_default_metabolite_width(self, node):
        if self._is_primary_node(node):
            return self._get_default_primary_node_width()

        return self._get_default_non_primary_node_width()

    def _get_default_metabolite_height(self, node):
        if self._is_primary_node(node):
            return self._get_default_primary_node_height()

        return self._get_default_non_primary_node_height()

    @staticmethod
    def _get_default_primary_node_width():
        # must be in line with libsbmlnetwork default species
        return 60

    @staticmethod
    def _get_default_primary_node_height():
        # must be in line with libsbmlnetwork default species height value
        return 36

    @staticmethod
    def _get_default_non_primary_node_width():
        return 40

    @staticmethod
    def _get_default_non_primary_node_height():
        return 24

    def _get_default_species_width(self, species):
        if species['id'] in self._primary_nodoes:
            return self._get_default_primary_node_width()

        return self._get_default_non_primary_node_width()

    def _get_default_species_height(self, species):
        if species['id'] in self._primary_nodoes:
            return self._get_default_primary_node_height()

        return self._get_default_non_primary_node_height()

    @staticmethod
    def _get_default_midmarker_width():
        return 10

    @staticmethod
    def _get_default_midmarker_height():
        return 10

    def _get_default_reaction_width(self):
        return self._get_default_midmarker_width()

    def _get_default_reaction_height(self):
        return self._get_default_midmarker_height()

    def _get_default_reaction_text_width(self):
        return 5 * self._get_default_reaction_width()

    def _get_default_reaction_text_height(self):
        return 5 * self._get_default_reaction_height()

    def _get_default_species_radius(self, species):
        return 0.5 * math.sqrt(
            math.pow(self._get_default_species_width(species), 2) + math.pow(self._get_default_species_height(species),
                                                                             2))

    def _get_default_reaction_radius(self):
        return 0.5 * math.sqrt(
            math.pow(self._get_default_reaction_width(), 2) + math.pow(self._get_default_reaction_height(), 2))

    @staticmethod
    def _get_species_text_horizontal_padding():
        return 20

    @staticmethod
    def _get_species_text_vertical_padding():
        return -20

    @staticmethod
    def _get_reaction_text_horizontal_padding():
        return 20

    @staticmethod
    def _get_reaction_text_vertical_padding():
        return -20

    @staticmethod
    def _is_primary_node(node):
        return 'node_is_primary' in list(node.keys()) and node['node_is_primary'] == True

    @staticmethod
    def _get_sbml_sid_compatible_id(id):
        if id[0].isdigit():
            return "_" + id

        return id

    def _find_sbml_node(self, node_id):
        node_id = self._get_sbml_sid_compatible_id(node_id)
        for species in self.species:
            if species['id'] == node_id:
                return species
        for reaction in self.reactions:
            if reaction['id'] == node_id:
                return reaction
        for multimarker_node in self._multimarker_nodes:
            if multimarker_node == node_id and self._multimarker_nodes[multimarker_node] is not None:
                return self._find_sbml_node(self._multimarker_nodes[multimarker_node])

        return None

    def _find_sbml_reaction(self, reaction_info, reaction_id):
        reaction_id = self._get_sbml_sid_compatible_id(reaction_id)
        for reaction in self.reactions:
            if reaction['id'] == reaction_id:
                return reaction

        for reaction in self.reactions:
            segments = reaction_info['segments']
            for segment in segments:
                if (self._get_sbml_sid_compatible_id(segments[segment]['from_node_id']) == reaction['id']
                        or self._get_sbml_sid_compatible_id(segments[segment]['to_node_id']) == reaction['id']):
                    return reaction

        return None

    def extract_species_features(self, species):
        pass

    def extract_reaction_features(self, reaction):
        pass
