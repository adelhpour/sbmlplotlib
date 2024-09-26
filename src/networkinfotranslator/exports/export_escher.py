from .export_base import NetworkInfoExportBase
import json
from pathlib import Path as pathlib


class NetworkInfoExportToEscher(NetworkInfoExportBase):
    def __init__(self):
        self.nodes = {}
        self.reactions = {}
        self.extra_texts = []
        super().__init__()

    def reset(self):
        super().reset()
        self.nodes = {}
        self.reactions = {}
        self.extra_texts = []

    def add_species(self, species):
        if self._is_valid_go(species):
            node = self._create_escher_node(species)
            self.nodes.update(node)

    def add_reaction(self, reaction):
        if self._is_valid_go(reaction):
            self.nodes.update(self._create_escher_midmarker_node(reaction))
            if self._has_start_multimarker(reaction):
                self.nodes.update(self._create_escher_start_multimarker_node(reaction))
            if self._has_end_multimarker(reaction):
                self.nodes.update(self._create_escher_end_multimarker_node(reaction))
            self.reactions.update(self._create_escher_reaction(reaction))
        self._tag_reaction_modifiers(reaction)

    def _create_escher_node(self, go):
        node_id = go['id']
        node = {node_id: {}}
        if 'referenceId' in list(go.keys()):
            node[node_id]['bigg_id'] = go['referenceId']
        # node are all set as primary nodes at this stage. Some are set to non-primary later when species references are processed
        node[node_id]['node_is_primary'] = True
        node[node_id]['node_type'] = "metabolite"
        node[node_id].update(self._get_escher_node_features(go))
        return node

    def _create_escher_midmarker_node(self, go):
        node_id = go['id']
        node = {node_id: {}}
        node[node_id]['node_type'] = "midmarker"
        node[node_id].update(self._get_escher_midmarker_node_features(go))
        return node

    def _create_escher_start_multimarker_node(self, go):
        node_id = go['id'] + ".start"
        node = {node_id: {}}
        node[node_id]['node_type'] = "multimarker"
        node[node_id].update(self._get_escher_start_multimarker_node_features(go))
        return node

    def _create_escher_end_multimarker_node(self, go):
        node_id = go['id'] + ".end"
        node = {node_id: {}}
        node[node_id]['node_type'] = "multimarker"
        node[node_id].update(self._get_escher_end_multimarker_node_features(go))
        return node

    def _create_escher_reaction(self, go):
        reaction_id = go['id']
        reaction = {reaction_id: {}}
        if 'referenceId' in list(go.keys()):
            reaction[reaction_id]['bigg_id'] = go['referenceId']
        reaction[reaction_id].update(self._extract_escher_reaction_features(go))
        return reaction

    def _get_escher_node_features(self, go):
        features = {}
        if 'features' in list(go.keys()):
            features['x'] = self._get_position_x(go['features'])
            features['y'] = self._get_position_y(go['features'])
            if 'texts' in list(go.keys()):
                text = go['texts'][0]
                if 'features' in list(text.keys()):
                    features['name'] = self._get_name(text['features'])
                    features['label_x'] = self._get_position_x(
                        text['features']) + self._get_text_horizontal_padding()
                    features['label_y'] = self._get_position_y(text['features']) + self._get_text_vertical_padding()

        return features

    def _get_escher_midmarker_node_features(self, go):
        features = {}
        if 'features' in list(go.keys()):
            features['x'] = self._get_position_x(go['features'])
            features['y'] = self._get_position_y(go['features'])

        return features

    def _get_escher_start_multimarker_node_features(self, go):
        features = {}
        if 'features' in list(go.keys()):
            features['x'] = self._get_position_x(go['features'])
            features['y'] = self._get_position_y(go['features'])

        return features

    def _get_escher_end_multimarker_node_features(self, go):
        features = {}
        if 'features' in list(go.keys()):
            features['x'] = self._get_position_x(go['features'])
            features['y'] = self._get_position_y(go['features'])

        return features

    def _extract_escher_reaction_features(self, go):
        features = {}
        if 'features' in list(go.keys()):
            features['reversibility'] = self._get_reversibility(go)
            features['metabolites'] = self._get_metabolites(go)
            features['genes'] = self._get_genes(go)
            features['segments'] = self._get_segments(go)
            if 'texts' in list(go.keys()):
                text = go['texts'][0]
                if 'features' in list(text.keys()):
                    features['name'] = self._get_name(text['features'])
                    features['label_x'] = self._get_position_x(text['features']) + self._get_text_horizontal_padding()
                    features['label_y'] = self._get_position_y(text['features']) + self._get_text_vertical_padding()

        return features

    def _get_metabolites(self, reaction):
        metabolites = []
        if 'speciesReferences' in list(reaction.keys()):
            for species_reference in reaction['speciesReferences']:
                metabolite = {}
                if 'species' in list(species_reference.keys()) and 'role' in list(species_reference.keys()):
                    if species_reference['role'].lower() == "reactant" or species_reference['role'].lower() == "substrate" or \
                            species_reference['role'].lower() == "product" or species_reference['role'].lower() == "sideproduct":
                        metabolite['bigg_id'] = species_reference['species']
                        metabolite['coefficient'] = self._get_metabolites_coefficient(species_reference)
                        metabolites.append(metabolite)

        return metabolites

    def _get_genes(self, reaction):
        genes = []
        if 'speciesReferences' in list(reaction.keys()):
            for species_reference in reaction['speciesReferences']:
                gene = {}
                if 'species' in list(species_reference.keys()) and 'role' in list(species_reference.keys()):
                    if species_reference['role'].lower() != "reactant" and species_reference[
                        'role'].lower() != "substrate" and \
                            species_reference['role'].lower() != "product" and species_reference[
                        'role'].lower() != "sideproduct":
                        gene['bigg_id'] = species_reference['species']
                        gene['name'] = self._find_escher_node_name(species_reference['species'])
                        genes.append(gene)

        return genes

    def _get_segments(self, reaction):
        segments = {}
        if 'speciesReferences' in list(reaction.keys()):
            for species_reference in reaction['speciesReferences']:
                segment_id = species_reference['referenceId']
                segment = {segment_id: {}}
                species_node_id = ""
                reaction_node_id = ""
                from_node_id = ""
                to_node_id = ""
                if 'species' in list(species_reference.keys()):
                    species_node_id = species_reference['species_glyph_id']
                if 'reaction' in list(species_reference.keys()):
                    reaction_node_id = species_reference['reaction_glyph_id']
                if 'role' in list(species_reference.keys()):
                    if species_reference['role'].lower() == "product" or species_reference['role'].lower() == "sideproduct":
                        from_node_id = reaction_node_id
                        to_node_id = species_node_id
                    else:
                        from_node_id = species_node_id
                        to_node_id = reaction_node_id
                segment[segment_id]['from_node_id'] = from_node_id
                segment[segment_id]['to_node_id'] = to_node_id
                segment[segment_id]['b1'] = self._get_segment_b1_features(species_reference)
                segment[segment_id]['b2'] = self._get_segment_b2_features(species_reference)
                segments.update(segment)

        return segments

    def _tag_reaction_modifiers(self, reaction):
        if 'speciesReferences' in list(reaction.keys()):
            for species_reference in reaction['speciesReferences']:
                if 'role' in list(species_reference.keys()):
                    if species_reference['role'].lower() != "reactant" and species_reference['role'].lower() != "substrate" and \
                            species_reference['role'].lower() != "product" and species_reference['role'].lower() != "sideproduct":
                        node_id = species_reference['species_glyph_id']
                        if node_id in self.nodes:
                            self.nodes[node_id]['node_is_primary'] = False

    def _has_start_multimarker(self, reaction):
        if 'speciesReferences' in list(reaction.keys()):
            if self._get_num_input_species(reaction['speciesReferences']) > 1:
                return True

        return False

    def _has_end_multimarker(self, reaction):
        if 'speciesReferences' in list(reaction.keys()):
            if self._get_num_output_species(reaction['speciesReferences']) > 1:
                return True

        return False

    @staticmethod
    def _get_num_input_species(species_references):
        num_input_species = 0
        for species_reference in species_references:
            if 'role' in list(species_reference.keys()) and (
                    species_reference['role'].lower() != "product" or species_reference[
                'role'].lower() == "sideproduct"):
                num_input_species += 1

        return num_input_species

    @staticmethod
    def _get_num_output_species(species_references):
        num_output_species = 0
        for species_reference in species_references:
            if 'role' in list(species_reference.keys()) and (
                    species_reference['role'].lower() == "product" or species_reference[
                'role'].lower() == "sideproduct"):
                num_output_species += 1

        return num_output_species

    @staticmethod
    def _is_valid_go(go):
        return 'id' in list(go.keys()) and 'referenceId' in list(go.keys())

    def _is_valid_species_reference(self, species_reference):
        if (self._is_valid_go(species_reference) and 'species' in list(species_reference.keys())
                and 'features' in list(species_reference.keys()) and 'curve' in list(
                    species_reference['features'].keys())):
            return True

    @staticmethod
    def _get_text_horizontal_padding():
        return 20

    @staticmethod
    def _get_text_vertical_padding():
        return -20

    def _get_position_x(self, features):
        if 'boundingBox' in list(features.keys()):
            return self._get_bb_center_x(features['boundingBox'])
        elif 'curve' in list(features.keys()):
            return self._get_curve_center_x(features['curve'])

        return 0.0

    def _get_position_y(self, features):
        if 'boundingBox' in list(features.keys()):
            return self._get_bb_center_y(features['boundingBox'])
        elif 'curve' in list(features.keys()):
            return self._get_curve_center_y(features['curve'])

        return 0.0

    @staticmethod
    def _get_bb_center_x(bounding_box):
        return bounding_box['x'] + 0.5 * bounding_box['width']

    @staticmethod
    def _get_bb_center_y(bounding_box):
        return bounding_box['y'] + 0.5 * bounding_box['height']

    @staticmethod
    def _get_curve_center_x(curve):
        if len(curve):
            return 0.5 * (curve[0]['startX'] + curve[len(curve) - 1]['endX'])

        return 0.0

    @staticmethod
    def _get_curve_center_y(curve, index):
        if len(curve):
            return 0.5 * (curve[0]['startY'] + curve[len(curve) - 1]['endY'])

        return 0.0

    @staticmethod
    def _get_name(features):
        if 'plainText' in list(features.keys()):
            return features['plainText']

    def _get_reversibility(self, reaction):
        # todo implement this
        return False

    @staticmethod
    def _get_metabolites_coefficient(species_reference):
        # todo the exact coefficient is not available in the species reference. Need to implement this
        if 'role' in list(species_reference.keys()):
            if species_reference['role'].lower() == "reactant" or species_reference['role'].lower() == "substrate":
                return -1
            elif species_reference['role'].lower() == "product" or species_reference['role'].lower() == "sideproduct":
                return 1

    def _find_escher_node_name(self, node_bigg_id):
        for node_id in self.nodes:
            node = self.nodes[node_id]
            if 'bigg_id' in list(node.keys()) and node['bigg_id'] == node_bigg_id:
                if 'name' in list(node.keys()):
                    return node['name']

        return ""

    @staticmethod
    def _get_segment_b1_features(species_reference):
        b1_x = 0
        b1_y = 0
        if 'features' in list(species_reference.keys()) and 'curve' in list(species_reference['features'].keys()):
            curve = species_reference['features']['curve']
            if len(curve):
                if 'basePoint1X' in list(curve[0].keys()):
                    b1_x = curve[0]['basePoint1X']
                else:
                    b1_x = curve[0]['startX']
                if 'basePoint1Y' in list(curve[0].keys()):
                    b1_y = curve[0]['basePoint1Y']
                else:
                    b1_y = curve[0]['startY']

        return {'x': b1_x, 'y': b1_y}

    @staticmethod
    def _get_segment_b2_features(species_reference):
        b2_x = 0
        b2_y = 0
        if 'features' in list(species_reference.keys()) and 'curve' in list(species_reference['features'].keys()):
            curve = species_reference['features']['curve']
            if len(curve):
                if 'basePoint2X' in list(curve[len(curve) - 1].keys()):
                    b2_x = curve[len(curve) - 1]['basePoint2X']
                else:
                    b2_x = curve[len(curve) - 1]['endX']
                if 'basePoint2Y' in list(curve[len(curve) - 1].keys()):
                    b2_y = curve[len(curve) - 1]['basePoint2Y']
                else:
                    b2_y = curve[len(curve) - 1]['endY']

        return {'x': b2_x, 'y': b2_y}

    @staticmethod
    def _get_valid_filename(file_name):
        if file_name.split('.')[-1] != "json":
            file_name += ".json"

        return file_name

    def export(self, file_name=""):
        horizontal_margin = 75
        vertical_margin = 75
        position_x = self.graph_info.extents['minX'] - horizontal_margin
        position_y = self.graph_info.extents['minY'] - vertical_margin
        dimensions_width = self.graph_info.extents['maxX'] - self.graph_info.extents['minX'] + 2 * horizontal_margin
        dimensions_height = self.graph_info.extents['maxY'] - self.graph_info.extents['minY'] + 2 * vertical_margin
        graph_info = [{'map_name': "escher_graph",
                       'map_id': "",
                       'map_description': "",
                       'homepage': ""},
                      {'canvas': {'x': position_x, 'y': position_y, 'width': dimensions_width,
                                  'height': dimensions_height},
                       'nodes': self.nodes,
                       'reactions': self.reactions,
                       'text_labels': self.extra_texts}]
        if file_name == "":
            return json.dumps(graph_info, indent=1)
        else:
            with open(self._get_valid_filename(file_name), 'w', encoding='utf8') as js_file:
                json.dump(graph_info, js_file, indent=1)
