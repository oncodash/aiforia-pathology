#!/usr/bin/env python3
import logging
import argparse
import ontoweaver
import pandas as pd
import biocypher
import yaml

def extract_write(biocypher_config_path, schema_path, data_mappings, separator = None):
    """Calls several mappings, each on the related Pandas-redable tabular data file,
       then reconciliate duplicated nodes and edges (on nodes' IDs, merging properties in lists),
       then export everything with BioCypher.
       Returns the path to the resulting import file.

       Args:
           biocypher_config_path: the BioCypher configuration file
           schema_path: the assembling schema file
           data_mappings: a dictionary mapping data file path to the OntoWeaver mapping yaml file to extract them

       Returns:
           The path to the import file.
   """

    assert(type(data_mappings) == dict) # data_file => mapping_file

    nodes = []
    edges = []

    for data_file, mapping_file in data_mappings.items():
        table = pd.read_csv(data_file)

        with open(mapping_file) as fd:
            mapping = yaml.full_load(fd)

        adapter = ontoweaver.tabular.extract_all(table, mapping, affix="none")

        nodes += adapter.nodes
        edges += adapter.edges

    bc = biocypher.BioCypher(
        biocypher_config_path = biocypher_config_path,
        schema_config_path = schema_path
    )

    bc.write_nodes(nodes)
    bc.write_edges(edges)
    import_file = bc.write_import_call()

    return import_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("csv")
    parser.add_argument("mapping")
    parser.add_argument("schema")
    parser.add_argument("config")

    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    parser.add_argument("-v", "--verbose", metavar="LEVEL",
                        help="Set the verbose level (" + " ".join(l for l in levels.keys()) + ").", default="WARNING")

    asked = parser.parse_args()

    logging.basicConfig(level = levels[asked.verbose], format = "{levelname} -- {message}\t\t{filename}:{lineno}", style='{')


    import_file = extract_write(asked.config, asked.schema, {asked.csv: asked.mapping})

    print(import_file)
