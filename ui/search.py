from ccut.main.symbol_map import SymbolMap
from fuzzywuzzy.process import extract

URI_SEPARATOR = '#'
NUM_RESULTS_TO_SUGGEST = 3

prefix_flat_list = list()
unit_flat_list = list()

def init_flat_search_lists():
    global prefix_flat_list, unit_flat_list

    if len(prefix_flat_list) == 0:
        d = SymbolMap.get_instance()
        for _, sym_d in d.si_prefix_map.items():
            inst_uri = sym_d.uri
            if URI_SEPARATOR in inst_uri:
                prefixeless_uri = str(inst_uri).split(URI_SEPARATOR)[1]
                if prefixeless_uri not in prefix_flat_list:
                    prefix_flat_list.append(prefixeless_uri)

    if len(unit_flat_list) == 0:
        d = SymbolMap.get_instance()
        for _, sym_d in d.symbol_map.items():
            for op_qu in sym_d:
                inst_uri = op_qu[1].uri # each is a tuple of (prio, qu)
                if URI_SEPARATOR in inst_uri:
                    prefixeless_uri = str(inst_uri).split(URI_SEPARATOR)[1]
                    if prefixeless_uri not in unit_flat_list:
                        unit_flat_list.append(prefixeless_uri)

def fuzzy_search_prefix(query):
    global prefix_flat_list

    top_res = extract(query, prefix_flat_list, limit=NUM_RESULTS_TO_SUGGEST)
    return top_res

def fuzzy_search_unit(query):
    global unit_flat_list
    
    top_res = extract(query, unit_flat_list, limit=NUM_RESULTS_TO_SUGGEST)
    return top_res