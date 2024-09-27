from .import_base import NetworkInfoImportBase


class NetworkInfoImportFromEscher(NetworkInfoImportBase):
    def __init__():
        super().__init__()

    def extract_info(self, graph):
        super().extract_info(graph)

        self.graph_info = graph
        self.extract_extents(self.graph_info)
        self.extract_entities(self.graph_info)

    def extract_extents(self, graph_info):
        for item in data:
            if 'canvas' in item:
                canvas = item['canvas']

        if 'position' in list(graph_info.keys()):
            if 'x' in list(graph_info['position'].keys()):
                self.extents['minX'] = graph_info['position']['x']
            if 'y' in list(graph_info['position'].keys()):
                self.extents['minY'] = graph_info['position']['y']
        if 'dimensions' in list(graph_info.keys()):
            if 'width' in list(graph_info['dimensions'].keys()):
                self.extents['minX'] -= 0.5 * graph_info['dimensions']['width']
                self.extents['maxX'] = self.extents['minX'] + graph_info['dimensions']['width']
            if 'height' in list(graph_info['dimensions'].keys()):
                self.extents['minY'] -= 0.5 * graph_info['dimensions']['height']
                self.extents['maxY'] = self.extents['minY'] + graph_info['dimensions']['height']
