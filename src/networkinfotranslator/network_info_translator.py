from .imports.import_sbml import NetworkInfoImportFromSBMLModel
from .imports.import_network_editor import NetworkInfoImportFromNetworkEditor
from .exports.export_sbml import NetworkInfoExportToSBMLModel
from .exports.export_network_editor import NetworkInfoExportToNetworkEditor
from .exports.export_cytoscapejs import NetworkInfoExportToCytoscapeJs
from .exports.export_figure_skia import NetworkInfoExportToSkia
from .exports.export_escher import NetworkInfoExportToEscher

def import_sbml_export_figure(import_file, file_name="", display_compartments_text_label=True,
                              display_species_text_label=True, display_reactions_text_label=False):
    import_from_sbml = NetworkInfoImportFromSBMLModel(display_compartments_text_label, display_species_text_label,
                                                      display_reactions_text_label)
    import_from_sbml.extract_info(import_file)
    export_to_figure = NetworkInfoExportToSkia()
    export_to_figure.extract_graph_info(import_from_sbml)
    export_to_figure.export(file_name)


def import_sbml_export_pil_image(import_file, display_compartments_text_label=True,
                                 display_species_text_label=True, display_reactions_text_label=False):
    import_from_sbml = NetworkInfoImportFromSBMLModel(display_compartments_text_label, display_species_text_label,
                                                        display_reactions_text_label)
    import_from_sbml.extract_info(import_file)
    export_to_figure = NetworkInfoExportToSkia()
    export_to_figure.extract_graph_info(import_from_sbml)
    return export_to_figure.export_as_pil_image()

def import_network_editor_export_sbml(import_file, export_file=""):
    import_from_network_editor = NetworkInfoImportFromNetworkEditor()
    import_from_network_editor.extract_info(import_file)
    export_to_sbml = NetworkInfoExportToSBMLModel()
    export_to_sbml.extract_graph_info(import_from_network_editor)
    return export_to_sbml.export(export_file)

def import_sbml_export_network_editor(import_file, export_file=""):
    import_from_sbml = NetworkInfoImportFromSBMLModel()
    import_from_sbml.extract_info(import_file)
    export_to_network_editor = NetworkInfoExportToNetworkEditor()
    export_to_network_editor.extract_graph_info(import_from_sbml)
    return export_to_network_editor.export(export_file)