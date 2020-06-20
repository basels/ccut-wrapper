from argparse import ArgumentParser
from baselutils import fclrprint, get_num_of_files_in_dir
from ccut_sheets import init_globals, process_file, get_tot_num_of_sheets
from datetime import timedelta
from json import load
from os import listdir
from os.path import basename, exists, join
from time import time

# --- entrypoint --------------------------------------------------------------

def main():

    global g_ignore_articles, g_list_of_ignored_articles
    g_ignore_articles = False

    ap = ArgumentParser(description=f'Validate files (xlsx, ccutvld.json) and output validation results.\n\tUSAGE: python {basename(__file__)} -d DIR_NAME')
    ap.add_argument('-d', '--dir_name', help='directory path.', type=str)
    ap.add_argument('-o', '--output_debug_file', help='If specified, print debug summary to output file (csv).', type=str)
    ap.add_argument('-g', '--ignore_files_list', help='If specified, ignore the list of file titles in given file (json).', type=str)
    args = ap.parse_args()

    if args.dir_name:
        fclrprint(f'Preparing to run over files in directory {args.dir_name}')
        # load list of filenames to ignore
        if args.ignore_files_list:
            g_ignore_articles = True
            with open(args.ignore_files_list, 'r') as infile:
                g_list_of_ignored_articles = load(infile)
        # test each .xlsx and .ccutvld.json
        ccut_test_xlsx_files_in_dir(args.dir_name, args.output_debug_file)
    else:
        fclrprint(f'Directory path was not provided.', 'r')
        exit(1)

# --- evaluation --------------------------------------------------------------

def init_ccut_validation(output_file=None):
    ''' Initialize global variables used in this file. '''
    
    global g_err_dbg, g_err_dct_p_unit, g_err_dct_p_file
    g_err_dbg = False
    if output_file:
        g_err_dbg = True
    g_err_dct_p_unit = dict()
    g_err_dct_p_file = dict()

def append_to_debug_dict(atomic_unit, debug_class=None):
    ''' Update debug dictionary with atomic_unit info by debug_class ('tp', 'fp', 'fn'). '''

    global g_err_dct_p_unit

    if debug_class:
        if atomic_unit['u'] not in g_err_dct_p_unit:
            g_err_dct_p_unit[atomic_unit['u']] = dict()
            g_err_dct_p_unit[atomic_unit['u']]['tp'] = 0
            g_err_dct_p_unit[atomic_unit['u']]['fp'] = 0
            g_err_dct_p_unit[atomic_unit['u']]['fn'] = 0
        g_err_dct_p_unit[atomic_unit['u']][debug_class] += 1

def count_number_of_unit_instances_in_cell(cell, debug_class=None):
    ''' Return number of unit instances in a cell. '''

    global g_err_dbg

    # cell is a list of compound units (each item in list has a unit)
    total_u = 0
    for compound_unit in cell:
        total_u += len(compound_unit['parts'])
        # --- debug prints for errors dict ----------
        if g_err_dbg and debug_class:
            for atmu in compound_unit['parts']:
                append_to_debug_dict(atmu, debug_class)
        # -------------------------------------------
    return total_u

def count_number_of_unit_instances_in_column(column, debug_class=None):
    ''' Return number of unit instances in a column (all rows). '''

    total_u = 0
    for _, cell in column.items():
        total_u += count_number_of_unit_instances_in_cell(cell, debug_class)
    return total_u

def count_number_of_unit_instances_in_sheet(sheet, debug_class=None):
    ''' Return number of unit instances in a sheet. '''

    total_u = 0
    for _, column in sheet.items():
        total_u += count_number_of_unit_instances_in_column(column, debug_class)
    return total_u

def check_if_lists_contain_match_and_delete(cell_list_1, cell_list_2):
    ''' Check if lists contain any matches.
    Return a boolean indicator and indexes of the found units in each list if match found. '''

    global g_err_dbg

    # iterate over items in actual list (compound units)
    for idx_cl1, cl1 in enumerate(cell_list_1):
        # iterate over each atomic unit in a compound unit (actual)
        for idx_al1, al1 in enumerate(cl1['parts']):
            # iterate over items in expected list (compound units)
            for idx_cl2, cl2 in enumerate(cell_list_2):
                # iterate over each atomic unit in a compound unit (expected)
                for idx_al2, al2 in enumerate(cl2['parts']):
                    # compare unit URIs
                    if al1['u'] == al2['u']:
                        # --- debug prints for errors dict ----------
                        if g_err_dbg:
                            append_to_debug_dict(al1, 'tp')
                        # -------------------------------------------
                        # TODO: compare other attributes
                        return True, idx_cl1, idx_al1, idx_cl2, idx_al2

    return False, None, None, None, None

def compare_cell_lists(actual_cell_lst, expected_cell_lst):
    ''' Compare two given lists (lists of dictionaries representing each cell's units content in the spreadsheet).
    Return the number of True-Positives and update (delete elements from) the lists. '''

    tp = 0
    while True:
        res, c_a_idx, a_a_idx, c_e_idx, a_e_idx = check_if_lists_contain_match_and_delete(actual_cell_lst, expected_cell_lst)
        if res:
            actual_cell_lst[c_a_idx]['parts'].pop(a_a_idx)
            expected_cell_lst[c_e_idx]['parts'].pop(a_e_idx)
            tp += 1
        else:
            break
    
    return tp

def compare_actual_with_expected_columns(actual_col, expected_col):
    ''' Compare two given dictionaries (representing each columns's units content in the spreadsheet).
    Return the number of True-Positives and False-Positives and update (delete elements from) the dicts. '''

    c_tp, c_fp = 0, 0

    for c_ka, c_va in actual_col.items():
        if c_ka not in expected_col:
            ''' we detected units in this cell but nothing is there
            count number of unit instances in this cell and add to fp '''
            c_fp += count_number_of_unit_instances_in_cell(c_va, 'fp')
            # skip to next cell
            continue
        # cell-dict exists in both actual and expected, check cell-lists
        c_tp += compare_cell_lists(c_va, expected_col[c_ka])

    return (c_tp, c_fp)

def compare_actual_with_expected_sheets(actual_sh, expected_sh):
    ''' Compare two given dictionaries (representing each sheet's units content in the spreadsheet).
    Return the number of True-Positives and False-Positives and update (delete elements from) the dicts. '''

    col_tp, col_fp = 0, 0

    for col_ka, col_va in actual_sh.items():
        if col_ka not in expected_sh:
            ''' we detected units in this column but nothing is there
            count number of unit instances in this column and add to fp '''
            col_fp += count_number_of_unit_instances_in_column(col_va, 'fp')
            # skip to next column
            continue
        # column-dict exists in both actual and expected, check cells
        res = compare_actual_with_expected_columns(col_va, expected_sh[col_ka])
        col_tp += res[0]
        col_fp += res[1]

    return (col_tp, col_fp)

def compare_actual_with_expected_dicts(actual, expected):
    ''' Compare two given dictionaries (representing each file's units, the actual and the expected).
    Return the number of True-Positives, False-Positives and False-Negatives. '''

    sh_tp, sh_fp, sh_fn = 0, 0, 0

    if actual and expected:
        for sheet_ka, sheet_va in actual.items():
            if sheet_ka not in expected:
                ''' we detected units in this sheeet but nothing is there
                count number of unit instances in this sheet and add to fp '''
                sh_fp += count_number_of_unit_instances_in_sheet(sheet_va, 'fp')
                # skip to next sheet
                continue
            # sheet-dict exists in both actual and expected, check columns
            res = compare_actual_with_expected_sheets(sheet_va, expected[sheet_ka])
            sh_tp += res[0]
            sh_fp += res[1]

    # go over leftovers in actual an add to fp (those we recognized incorrectly)
    if actual:
        for _, sheet_va in actual.items():
            sh_fp += count_number_of_unit_instances_in_sheet(sheet_va, 'fp')

    # go over lefovers in expected and add to fn
    if expected:
        for _, sheet_ve in expected.items():
            sh_fn += count_number_of_unit_instances_in_sheet(sheet_ve, 'fn')

    return sh_tp, sh_fp, sh_fn

def calc_and_print_stats(true_pos, false_pos, false_neg, color='c'):
    ''' Calculate and print validation statistics (Precision, Recall, F1, etc...). '''

    try:
        precision = (float(true_pos)) / (true_pos + false_pos)
        recall = (float(true_pos)) / (true_pos + false_neg)
        f1_score = (2.0 * precision * recall) / (precision + recall)
        fclrprint('f1=%.4f | precision=%.4f, recall=%.4f | tp=%d, fp=%d, fn=%d' % \
            (f1_score, precision, recall, true_pos, false_pos, false_neg), color)
    except:
        fclrprint(f'Something went terribly wrong in stats calculations...', 'r')

def print_debug_dict(fdebug_file):
    ''' Print debug dictionary to file '''

    global g_err_dbg, g_err_dct_p_unit, g_err_dct_p_file

    if g_err_dbg:
        # write to csv files
        fdebug_file_units = '.'.join(fdebug_file.split('.')[:-1]) + '.units.csv'
        with open(fdebug_file_units, 'w', encoding='utf-8') as write_file:
            write_file.write('unit_uri_or_suffix,tp,fp,fn\n')
            for atm_unt_full_uri, atm_unt_inst in g_err_dct_p_unit.items():
                atm_unt_uri_to_print = atm_unt_full_uri.split("#")[-1]
                write_file.write(atm_unt_uri_to_print + "," + str(atm_unt_inst['tp']) + "," \
                    + str(atm_unt_inst['fp']) + "," + str(atm_unt_inst['fn']) + "\n")
        fdebug_file_files = '.'.join(fdebug_file.split('.')[:-1]) + '.files.csv'
        with open(fdebug_file_files, 'w', encoding='utf-8') as write_file:
            write_file.write('filename,tp,fp,fn\n')
            for filename, file_inst in g_err_dct_p_file.items():
                write_file.write(filename + "," + str(file_inst['tp']) + "," \
                    + str(file_inst['fp']) + "," + str(file_inst['fn']) + "\n")
        fclrprint(f'Dumped debug results to files {fdebug_file_units}, {fdebug_file_files}', 'c')

def ccut_test_xlsx_files_in_dir(input_dir_name, output_debug_file):
    ''' Process the xlsx files in a given directory and match against its given validation file. '''

    global g_err_dbg, g_err_dct_p_file, g_ignore_articles, g_list_of_ignored_articles

    init_globals()
    init_ccut_validation(output_debug_file)
    true_pos, false_pos, false_neg = 0, 0, 0

    tot_files = get_num_of_files_in_dir(input_dir_name, ".xlsx")
    files_processed = 0
    actual_files_processed = 0
    start = time()
    for xfname in listdir(input_dir_name):
        if xfname.endswith(".xlsx"):
            files_processed += 1
            xfname_no_suffix = xfname.split('.xlsx')[0]
            if g_ignore_articles:
                # check if article is in provided list
                if xfname_no_suffix in g_list_of_ignored_articles:
                    continue
            actual_files_processed += 1
            xfname_full = join(input_dir_name, xfname)
            vfname_full = join(input_dir_name, xfname_no_suffix + '.ccutvld.json')
            if not exists(vfname_full):
                fclrprint(f'File {xfname_full} does not have a results file. Skipping...', 'r')
                continue
            fclrprint(f'Processing file {xfname_full} and comparing results to {vfname_full}')
            act_dict, _ = process_file(xfname_full)
            #import IPython; IPython.embed();
            with open(vfname_full, 'r') as read_file:
                val_dict = load(read_file)
            f_tp, f_fp, f_fn = compare_actual_with_expected_dicts(act_dict, val_dict)
            # update debug dictionary
            if g_err_dbg:
                g_err_dct_p_file[xfname] = dict()
                g_err_dct_p_file[xfname]['tp'] = f_tp
                g_err_dct_p_file[xfname]['fp'] = f_fp
                g_err_dct_p_file[xfname]['fn'] = f_fn
            # add to total
            true_pos += f_tp
            false_pos += f_fp
            false_neg += f_fn
            if (files_processed % 10) == 0:
                eta = (tot_files - files_processed) * (time() - start) / files_processed
                eta = str(timedelta(seconds=int(eta))).zfill(8)
                print('Completion: %04.2f%%, eta: %s' % (100 * files_processed / tot_files, eta))
                calc_and_print_stats(true_pos, false_pos, false_neg)

    calc_and_print_stats(true_pos, false_pos, false_neg, color='g')
    print(f'Processed a total of {actual_files_processed} files ({get_tot_num_of_sheets()} sheets) out of {files_processed} .xlsx files in given directory {input_dir_name}!')
    print_debug_dict(output_debug_file)

if __name__ == '__main__':
    main()
