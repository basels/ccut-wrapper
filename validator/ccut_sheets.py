from argparse import ArgumentParser
from baselutils import column_num2str, fclrprint
from ccut import ccut, QUDT_PROPERTIES_NAMESPACE, CCUT_NAMESPACE
from json import dump
from os.path import basename
from pandas import ExcelFile, Series, isnull
from re import search as search_rx

IDX_CCUT_DIM = f'{CCUT_NAMESPACE}:hasDimension'
IDX_CCUT_PRT = f'{CCUT_NAMESPACE}:hasPart'
IDX_QDTP_QTK = f'{QUDT_PROPERTIES_NAMESPACE}:quantityKind'
IDX_CCUT_PFX = f'{CCUT_NAMESPACE}:prefix'
IDX_CCUT_EXP = f'{CCUT_NAMESPACE}:exponent'
IDX_CCUT_MLT = f'{CCUT_NAMESPACE}:multiplier'

MAX_NUM_OF_WORDS_ALLOWED_IN_CELL = 6

# --- entrypoint --------------------------------------------------------------

def main():
    ap = ArgumentParser(description=f'Process a spreasheet file (xlsx) and generate a dictionary file (json) of cell locations in which units were detected.\n\tUSAGE: python {basename(__file__)} -i INPUT_FILE')
    ap.add_argument('-i', '--input_file', help='input spreasheet file (xlsx).', type=str)
    args = ap.parse_args()

    if args.input_file:
        init_globals()
        output_fname = '.'.join(args.input_file.split('.')[:-1]) + '.ccut.json'
        fclrprint(f'Processing file {args.input_file}')
        dict_out, _ = process_file(args.input_file)
        with open(output_fname, 'w') as outfile:
            dump(dict_out, outfile, indent=2)
        fclrprint(f'Done... generated file {output_fname}', 'g')
    else:
        fclrprint(f'An input file was not provided.', 'r')
        exit(1)

def get_tot_num_of_sheets():
    ''' Return the total number of sheets processed (from globals). '''

    global g_tot_num_of_sheets
    return g_tot_num_of_sheets

def init_globals():
    ''' Initializes globals used in file. '''

    global g_ccut_inst, g_tot_num_of_sheets
    g_ccut_inst = ccut()
    g_tot_num_of_sheets = 0

# --- processing --------------------------------------------------------------

def process_ccu_repr_output(ccut_repr):
    ''' Processes the CCU Representation dictionary and returns a dictionary
    with a list of 'parts', each has:
        'u'=unit ; 'p'=prefix ; 'e'=exponent ; 'm'=multiplier
    and a 'dimensoion' summary for its parts.

    i.e.: { "dimension": "L-1 I",
    "parts": [
    { "p": "http://data.nasa.gov/qudt/owl/unit#Micro",
      "u": "http://data.nasa.gov/qudt/owl/unit#Ampere" },
    { "p": "http://data.nasa.gov/qudt/owl/unit#Micro",
      "u": "http://data.nasa.gov/qudt/owl/unit#Meter",
      "e": "-1" } ] '''

    # check if has any parts
    if IDX_CCUT_PRT not in ccut_repr:
        return None
    
    s_unt_dict = dict()
    # iterate over each part and check if recognized
    for prt in ccut_repr[IDX_CCUT_PRT]:
        # get URI
        prt_unit_uri = prt[IDX_QDTP_QTK]
        if "UNKNOWN TYPE" == prt_unit_uri:
            continue
        # URI is valid, parse part components 
        prt_single = {'u': prt_unit_uri}
        if IDX_CCUT_PFX in prt:
            prt_single['p'] = prt[IDX_CCUT_PFX]
        if IDX_CCUT_EXP in prt:
            prt_single['e'] = prt[IDX_CCUT_EXP]
        if IDX_CCUT_MLT in prt:
            prt_single['m'] = prt[IDX_CCUT_MLT]
        # append to list in dictionary
        if 'parts' not in s_unt_dict:
            s_unt_dict['parts'] = list()
        s_unt_dict['parts'].append(prt_single)

    if 'parts' in s_unt_dict:
        # TODO: check if unknown dimension
        s_unt_dict['dimension'] = ccut_repr[IDX_CCUT_DIM]
        return s_unt_dict
    else:
        return None

def process_cell(cell_content):
    ''' Processes a cell content looking for units, returns a structured output (dict) of the cell.
    See process_ccu_repr_output documentation for more info. '''

    global g_ccut_inst

    input_str = str(cell_content)

    # check if cell has any text
    if 0 == len(input_str):
        return None

    ########################## NAIVE HEURISTICS ###############################
    # replace paranthesis with spaces
    input_str = str(input_str).replace('(', ' ').replace(')', ' ').replace('[', ' ').replace(']', ' ')

    # skip cells that don't have any text element
    if not search_rx('[a-zA-Z]', input_str):
        return None

    # skip cells with too many words in dict (post-observation of a dev-set)   
    if len(input_str.split(' ')) > MAX_NUM_OF_WORDS_ALLOWED_IN_CELL:
        return None
    ###########################################################################

    try:
        urepr = g_ccut_inst.get_all_ccu(input_str)[0] # we check only the top result (TODO: fix)
        return process_ccu_repr_output(urepr)
    except:
        return None

def insert_instance_to_sheet_dict(column_idx, row_idx, sheet_dict, unit_inst_dict):
    ''' Insert a compound unit instance to a dictionary holding the sheet units info. '''
    
    if column_idx not in sheet_dict:
        sheet_dict[column_idx] = dict()
    if row_idx not in sheet_dict[column_idx]:
        sheet_dict[column_idx][row_idx] = list()
    sheet_dict[column_idx][row_idx].append(unit_inst_dict)

def process_sheet(dataframe):
    ''' Processes a sheet looking for units, returns a structured output (dict) of the sheet. '''

    # init sheet dict
    sh_dict = dict()
    # Fill merged rows with row value
    dataframe.index = Series(dataframe.index)
    # iterate over all columns in a given sheet
    for r_idx, row in dataframe.loc[:].iterrows():
        r_idx_str = str(r_idx+1)
        # iterate over row cells (Each column)
        for c_idx, cell in enumerate(row):
            c_idx_str = column_num2str(c_idx+1)
            # if not NaN
            if not isnull(cell):
                #fclrprint(f'analyzing [{c_idx_str}][{r_idx_str}] {cell}', 'c')
                cell_dict = process_cell(cell)
                # TODO: case where there are multiple compound units in cell...
                if cell_dict:
                    insert_instance_to_sheet_dict(c_idx_str, r_idx_str, sh_dict, cell_dict)
                    #totstr = ', '.join(u['u'] for u in cell_dict['parts'])
                    #fclrprint(f'[{c_idx_str}][{r_idx_str}] {totstr}', 'g')
    if sh_dict:
        return sh_dict
    return None

def process_file(fname):
    ''' Processes a file looking for units, returns a structured output (dict) of the file. '''

    global g_tot_num_of_sheets

    # init file dictionaries
    f_dict = dict()
    raw_f_dict = dict()
    # Load spreadsheets
    xl = ExcelFile(fname)
    # iterate over sheets
    for sheet_name in xl.sheet_names:
        g_tot_num_of_sheets += 1
        # Load a sheet into a DataFrame by name
        df = xl.parse(sheet_name, header=None, skip_blank_lines=False)
        raw_f_dict[sheet_name] = df
        fclrprint(f'Processing Sheet {sheet_name}...')
        sht_dict = process_sheet(df)
        if sht_dict:
            f_dict[sheet_name] = sht_dict
    if f_dict:
        return f_dict, raw_f_dict
    return None, raw_f_dict

if __name__ == '__main__':
    main()