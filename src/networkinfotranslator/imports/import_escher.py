from .import_base import NetworkInfoImportBase

import json
import math


class NetworkInfoImportFromEscher(NetworkInfoImportBase):
    def __init__(self):
        super().__init__()
        self._primary_nodoes = []

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

    def _extract_metabolite_node(self, node_info, node_id):
        sbml_node = self._extract_sbml_node(node_info, node_id)
        sbml_node['texts'] = self._extract_sbml_node_texts(node_info, sbml_node['features'], node_id)
        sbml_node['compartment'] = self._get_default_compartment_id()
        self.species.append(sbml_node)

    def _extract_midmarker_node(self, node_info, node_id):
        sbml_node = self._extract_sbml_node(node_info, node_id)
        self.reactions.append(sbml_node)

    def _extract_reactions(self, reactions):
        for reaction_id in reactions:
            self._extract_sbml_reaction(reactions[reaction_id], reaction_id)

    def _extract_sbml_node(self, node_info, node_id):
        sbml_node = {'id': node_id}
        if 'bigg_id' in list(node_info.keys()):
            sbml_node['referenceId'] = node_info['bigg_id']
        sbml_node['features'] = self._extract_sbml_node_features(node_info)
        self._add_to_primary_node_list(node_info, node_id)
        return sbml_node

    def _add_to_primary_node_list(self, node_info, node_id):
        if 'node_is_primary' in list(node_info.keys()) and node_info['node_is_primary'] == True:
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
            return self._get_default_species_width()
        elif node_type == 'midmarker':
            return self._get_default_reaction_width()

        return 0

    def _extract_sbml_node_height(self, node_info, node_type):
        if 'height' in list(node_info.keys()):
            return node_info['height']
        if node_type == 'metabolite':
            return self._get_default_species_height()
        elif node_type == 'midmarker':
            return self._get_default_reaction_height()

        return 0

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
            text = {'id': node_id + "_TextGlyph_1"}
            text['features'] = self._extract_sbml_node_text_features(node_info, node_features)
            texts.append(text)

        return texts

    def _extract_sbml_node_text_features(self, node_info, node_features):
        bounding_box = {}
        bounding_box['width'] = self._extract_sbml_node_text_width(node_features)
        bounding_box['height'] = self._extract_sbml_node_text_height(node_features)
        bounding_box['x'] = self._extract_sbml_node_text_x(node_info, node_features)
        bounding_box['y'] = self._extract_sbml_node_text_y(node_info, node_features)
        return {'plainText': node_info['name'], 'boundingBox': bounding_box}

    @staticmethod
    def _extract_sbml_node_text_width(node_features):
        return node_features['boundingBox']['width']

    @staticmethod
    def _extract_sbml_node_text_height(node_features):
        return node_features['boundingBox']['height']

    def _extract_sbml_node_text_x(self, node_info, node_features):
        if 'label_x' in list(node_info.keys()):
            return node_info['label_x'] - 0.5 * node_features['boundingBox']['width'] - self._get_text_horizontal_padding()

        return 0.0

    def _extract_sbml_node_text_y(self, node_info, node_features):
        if 'label_y' in list(node_info.keys()):
            return node_info['label_y'] - 0.5 * node_features['boundingBox']['height'] - self._get_text_vertical_padding()

        return 0.0

    def _extract_sbml_reaction(self, reaction_info, reaction_id):
        for sbml_reaction in self.reactions:
            if sbml_reaction['id'] == reaction_id:
                if 'bigg_id' in list(reaction_info.keys()):
                    sbml_reaction['referenceId'] = reaction_info['bigg_id']
                sbml_reaction['texts'] = self._extract_sbml_node_texts(reaction_info, sbml_reaction['features'], reaction_id)
                sbml_reaction['speciesReferences'] = self._extract_sbml_reaction_species_references(reaction_info,
                                                                                               reaction_id)

    def _extract_sbml_reaction_species_references(self, reaction_info, reaction_id):
        if 'segments' in list(reaction_info.keys()):
            segments = reaction_info['segments']
            species_references = []
            for segment_id in segments:
                species_reference = self._extract_sbml_reaction_species_reference(segments[segment_id], reaction_id)
                if species_reference:
                    species_references.append(species_reference)

            return species_references

    def _extract_sbml_reaction_species_reference(self, segment, reaction_id):
        species_reference = {}
        if 'from_node_id' in list(segment.keys()) and 'to_node_id' in list(segment.keys()):
            from_node = self._find_sbml_node(segment['from_node_id'])
            to_node = self._find_sbml_node(segment['to_node_id'])
            if from_node is not None and to_node is not None:
                species_reference = self._initialize_species_reference(reaction_id, from_node, to_node)
                species_reference['features'] = self._extract_sbml_reaction_species_reference_features(
                    from_node, to_node, segment)

        return species_reference

    @staticmethod
    def _get_species_reference_reaction_node(reaction_id, from_node, to_node):
        if from_node['id'] == reaction_id:
            return from_node
        elif to_node['id'] == reaction_id:
            return to_node

        return None

    @staticmethod
    def _get_species_reference_species_node(reaction_id, from_node, to_node):
        if from_node['id'] == reaction_id:
            return to_node
        elif to_node['id'] == reaction_id:
            return from_node

        return None

    def _get_species_reference_role(self, reaction_id, from_node, to_node):
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
        reaction = self._get_species_reference_reaction_node(reaction_id, from_node, to_node)
        species = self._get_species_reference_species_node(reaction_id, from_node, to_node)
        identification_features = {'role': self._get_species_reference_role(reaction_id, from_node, to_node),
                                   'reaction': reaction['referenceId'], 'reactionGlyphId': reaction['id'],
                                   'reactionGlyphIndex': 0, 'species': species['referenceId'],
                                   'speciesGlyphId': species['id'], 'speciesReferenceGlyphIndex': 0,
                                   'id': reaction['id'] + "_" + species['id'],
                                   'referenceId': reaction['referenceId'] + "_" + species['referenceId']}
        return identification_features


    def _extract_sbml_reaction_species_reference_features(self, from_go, to_go, segment):
        features = {'startPoint': self._get_species_reference_start_point(from_go),
                    'startSlope': self._get_species_reference_start_slope(from_go, to_go, segment),
                    'endPoint': self._get_species_reference_end_point(to_go),
                    'endSlope': self._get_species_reference_end_slope(from_go, to_go, segment),
                    'curve': self._get_curve(from_go, to_go, segment)}
        return features

    def _get_curve(self, from_go, to_go, segment):
        curve = []
        start_point = self._get_species_reference_start_point(from_go)
        end_point = self._get_species_reference_end_point(to_go)
        base_point1 = self._get_species_reference_base_point1(from_go, segment)
        base_point2 = self._get_species_reference_base_point2(to_go, segment)
        curve.append({'startX': start_point['x'], 'startY': start_point['y'],
                      'endX': end_point['x'], 'endY': end_point['y'],
                      'basePoint1X': base_point1['x'], 'basePoint1Y': base_point1['y'],
                      'basePoint2X': base_point2['x'], 'basePoint2Y': base_point2['y']})
        return curve

    def _get_species_reference_start_point(self, go):
        # todo for now we just assume the center of the graphical obejct is the point species reference connects to a graphical object
        return self._get_center_point(go)

    def _get_species_reference_end_point(self, go):
        # todo for now we just assume the center of the graphical obejct is the point species reference connects to a graphical object
        return self._get_center_point(go)

    def _get_species_reference_base_point1(self, go, segment):
        if 'b1' in list(segment.keys()):
            return segment['b1']

        return self._get_species_reference_start_point(go)

    def _get_species_reference_base_point2(self, go, segment):
        if 'b2' in list(segment.keys()):
            return segment['b2']

        return self._get_species_reference_end_point(go)

    def _get_species_reference_start_slope(self, from_go, to_go, segment):
        if 'b1' in list(segment.keys()):
            first_point = segment['b1']
        else:
            first_point = self._get_species_reference_end_point(to_go)
        second_point = self._get_species_reference_start_point(from_go)

        return self._calculate_slope(first_point, second_point)

    def _get_species_reference_end_slope(self, from_go, to_go, segment):
        if 'b2' in list(segment.keys()):
            first_point = segment['b2']
        else:
            first_point = self._get_species_reference_start_point(from_go)
        second_point = self._get_species_reference_end_point(to_go)

        return self._calculate_slope(first_point, second_point)

    @staticmethod
    def _get_center_point(go):
        bounding_box = go['features']['boundingBox']
        return {'x': bounding_box['x'] + 0.5 * bounding_box['width'],
                'y': bounding_box['y'] + bounding_box['height']}

    @staticmethod
    def _calculate_slope(point1, point2):
        if point1['x'] == point2['x']:
            return 0.0

        return math.atan2(point2['y'] - point1['y'], point2['x'] - point1['x'])

    def _create_default_compartment(self):
        compartment = {'id': self._get_default_compartment_id() + "_glyph1",
                       'referenceId': self._get_default_compartment_id(), 'index': 0,
                       'features': {'boundingBox': {'x': self.extents['minX'] + self._get_compartment_extent_padding(),
                                                    'y': self.extents['minY'] + self._get_compartment_extent_padding(),
                                                    'width': self.extents['maxX'] - self.extents[
                                                        'minX'] - 2 * self._get_compartment_extent_padding(),
                                                    'height': self.extents['maxY'] - self.extents[
                                                        'minY'] - 2 * self._get_compartment_extent_padding()}},
                       'texts': []}
        return compartment

    @staticmethod
    def _get_default_compartment_id():
        return 'default_compartment'

    @staticmethod
    def _get_default_species_width():
        return 50

    @staticmethod
    def _get_default_species_height():
        return 50

    @staticmethod
    def _get_default_reaction_width():
        return 10

    @staticmethod
    def _get_default_reaction_height():
        return 10

    @staticmethod
    def _get_compartment_extent_padding():
        return 20

    @staticmethod
    def _get_text_horizontal_padding():
        return 20

    @staticmethod
    def _get_text_vertical_padding():
        return -20

    def _find_sbml_node(self, node_id):
        for species in self.species:
            if species['id'] == node_id:
                return species
        for reaction in self.reactions:
            if reaction['id'] == node_id:
                return reaction
        return None

    def extract_species_features(self, species):
        pass

    def extract_reaction_features(self, reaction):
        pass


