from pycallgraph2 import PyCallGraph, Config
from pycallgraph2.globbing_filter import GlobbingFilter
from pycallgraph2.output import GraphvizOutput

# Include trace only for our package
config = Config()
config.trace_filter = GlobbingFilter(include=['shelves.*'])

graphviz = GraphvizOutput(output_file='shelves-callgraph.svg')

# Import functions from the package (registration in the module takes place during import)
import shelves

with PyCallGraph(output=graphviz, config=config):
    # Simple, secure calls to generate graphs
    shelves.vote_for_shelf('test-album-1', 'Incoming')
    shelves.vote_for_shelf('test-album-1', 'Standard')
    _ = shelves.get_album_shelf('test-album-1')
