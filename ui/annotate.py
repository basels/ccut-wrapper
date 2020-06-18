from ccut.main.symbol_map import SymbolMap
from fuzzywuzzy.process import extract
from re import findall

URI_SEPARATOR = '#'
NUM_RESULTS_TO_SUGGEST = 3

prefix_flat_list = list()
unit_flat_list = list()
sheet_flat_list = list()

def init_flat_search_lists(active_dict):
    global sheet_flat_list, prefix_flat_list, unit_flat_list

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
    cell_row = findall(r'\d+', cell)[0]
    cell_col = cell.split(cell_row)[0].upper()

    if sheet not in ant_dict:
        ant_dict[sheet] = dict()
    if cell_col not in ant_dict[sheet]:
        ant_dict[sheet][cell_col] = dict()
    if cell_row not in ant_dict[sheet][cell_col]:
        ant_dict[sheet][cell_col][cell_row] = list()

    cell_list_inst = ant_dict[sheet][cell_col][cell_row]
    prt_single = {'u': unit}
    if len(multiplier) > 0:
        prt_single['m'] = multiplier
    if len(prefix) > 0:
        prt_single['p'] = prefix
    if len(exponent) > 0:
        prt_single['e'] = exponent

    if len(cell_list_inst) > 0: # assuming a single compound unit in cell
        cell_list_inst[0]['parts'].append(prt_single)
    else:
        cell_list_inst.append({'dimension': "TODO", 'parts': [prt_single]})

    print(ant_dict)
    # TODO: 1. update dimension
    print('*'*100)