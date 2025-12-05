from pycallgraph2 import PyCallGraph, Config
from pycallgraph2.globbing_filter import GlobbingFilter
from pycallgraph2.output import GraphvizOutput

# Trace nur für unser Paket einschließen
config = Config()
config.trace_filter = GlobbingFilter(include=['shelves.*'])

graphviz = GraphvizOutput(output_file='shelves-callgraph.svg')

# Funktionen aus dem Paket importieren (registrierung im Modul passiert beim Import)
import shelves

with PyCallGraph(output=graphviz, config=config):
    # Einfache, sichere Aufrufe zum Erzeugen von Graphen
    shelves.vote_for_shelf('test-album-1', 'Incoming')
    shelves.vote_for_shelf('test-album-1', 'Standard')
    _ = shelves.get_album_shelf('test-album-1')
