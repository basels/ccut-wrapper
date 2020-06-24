from ccut.main.symbol_map import SymbolMap
from ccut.main.dimension_map import DimensionMap
from ccut.main.dimension import DimensionVector
from fuzzywuzzy.process import extract
from re import findall

QUDT_NAMESPACE = 'http://www.qudt.org/qudt/owl/1.0.0/unit/Instances.html#'
URI_SEPARATOR = '#'
NUM_RESULTS_TO_SUGGEST = 3

sheet_flat_list = list()
prefix_flat_list = list()
unit_flat_list = list()
uri_to_qkind = dict()

def init_flat_search_lists(active_dict):
    global sheet_flat_list, prefix_flat_list, unit_flat_list, uri_to_qkind

    for sheet_n in active_dict.keys():
        if sheet_n not in sheet_flat_list:
            sheet_flat_list.append(sheet_n)

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
                        if hasattr(op_qu[1], 'quantity_kind'):
                            uri_to_qkind[prefixeless_uri] = op_qu[1].quantity_kind.rsplit("#")[1]
                        

def fuzzy_search_sheet(query):
    global sheet_flat_list
    top_res = extract(query, sheet_flat_list, limit=NUM_RESULTS_TO_SUGGEST)
    return top_res

def fuzzy_search_prefix(query):
    global prefix_flat_list
    top_res = extract(query, prefix_flat_list, limit=NUM_RESULTS_TO_SUGGEST)
    return top_res

def fuzzy_search_unit(query):
    global unit_flat_list
    top_res = extract(query, unit_flat_list, limit=NUM_RESULTS_TO_SUGGEST)
    return top_res

def add_annotation_to_cell(ant_dict, sheet, cell, multiplier, prefix, unit, exponent):    
    global uri_to_qkind

    cell_row = findall(r'\d+', cell)[0]
    cell_col = cell.split(cell_row)[0].upper()

    if sheet not in ant_dict:
        ant_dict[sheet] = dict()
    if cell_col not in ant_dict[sheet]:
        ant_dict[sheet][cell_col] = dict()
    if cell_row not in ant_dict[sheet][cell_col]:
        ant_dict[sheet][cell_col][cell_row] = list()

    cell_list_inst = ant_dict[sheet][cell_col][cell_row]
    prt_single = {'u': QUDT_NAMESPACE+unit}
    if len(multiplier) > 0:
        prt_single['m'] = multiplier
    if len(prefix) > 0:
        prt_single['p'] = QUDT_NAMESPACE+prefix
    if len(exponent) > 0:
        prt_single['e'] = exponent

    if len(cell_list_inst) > 0: # assuming a single compound unit in cell
        cell_list_inst[0]['parts'].append(prt_single)
    else:
        cell_list_inst.append({'parts': [prt_single]})

    dim_vec = DimensionVector()
    d = DimensionMap.get_instance()
    for a_unt in cell_list_inst[0]['parts']: # assuming a single compound unit in cell
        unt_name = a_unt['u'].rsplit("#")[1]
        unt_exp = 1
        if 'e' in a_unt:
            unt_exp = a_unt['e']
        if unt_name in uri_to_qkind:
            unt_quantity_kind = uri_to_qkind[unt_name]
            if unt_quantity_kind in d.qd_map:
                dimension = d.qd_map[unt_quantity_kind]
                if dimension:
                    dim_vec += DimensionVector().set_dimensions(dimension).raise_to_power(unt_exp)
    cell_list_inst[0]['dimension'] = dim_vec.get_abbr()
