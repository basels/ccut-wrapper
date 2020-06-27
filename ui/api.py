from annotate import init_flat_search_lists, fuzzy_search_sheet, fuzzy_search_prefix, \
                    fuzzy_search_unit, add_annotation_to_cell, update_cell_dimension
from ccut import ccut
from ccut.main.config import Config
from ccut_sheets import init_globals, process_file
from flask import Flask, request, redirect, jsonify, render_template, url_for
from forms import ParseForm, ConversionForm, FileUploadForm, AnnotationEditForm
from json import load, dump, dumps
from os import makedirs
from os.path import exists
from werkzeug.utils import secure_filename

# Directory to store temporary work files
STORAGE_FOLDER = '/tmp/ccut_uploads/'

# Init Flask app
app = Flask(__name__)
app.config.from_object(Config)
# Init ccut sheets processor
init_globals()
# Init ccut instance
ccut = ccut()
# Init global variables
g_active_json = dict()
g_active_filename = ""
''' g_conv_res tuple contains:
    0: conv_val     1,2: conv_sts    3: orig_val     
    4: src_str_list 5: dst_str_list  6: src_list     7: dst_list
'''
g_conv_res = list()
g_conv_src_idx = 1
g_conv_dst_idx = 1

@app.route("/")
def welcome():
    ''' Page to welcome '''

    return render_template('generic.html', data='Welcome to CCUT Wrapper!')

@app.route('/parse', methods=['GET', 'POST'])
def parse():
    ''' Page to handle Canonical Compound Unit Parsing '''
    
    str_list = list()
    form = ParseForm()
    if form.validate_on_submit():
        cu_list = ccut.get_all_ccu(form.u.data)
        for cu in cu_list:
            str_list.append(dumps(cu, sort_keys=True, indent=4, separators=(',', ': ')))

    return render_template('ccu_parse.html', form=form, response=str_list)

@app.route('/convert', methods=['GET', 'POST'])
def convert():
    ''' Page to handle Canonical Compound Unit Conversion '''

    global g_conv_res, g_conv_src_idx, g_conv_dst_idx

    form = ConversionForm()
    if form.validate_on_submit():
        g_conv_src_idx = 1
        g_conv_dst_idx = 1
        src_ccu = ccut.get_all_ccu(form.in_unit.data)
        src_str_list = list()
        for cu in src_ccu:
            src_str_list.append(dumps(cu, sort_keys=True, indent=4, separators=(',', ': ')))

        dst_ccu = ccut.get_all_ccu(form.out_unit.data)
        dst_str_list = list()
        for cu in dst_ccu:
            dst_str_list.append(dumps(cu, sort_keys=True, indent=4, separators=(',', ': ')))

        g_conv_res = ccut.convert_ccu2ccu(src_ccu[g_conv_src_idx-1], dst_ccu[g_conv_dst_idx-1], float(form.in_val.data))
        g_conv_res += (float(form.in_val.data), src_str_list, dst_str_list)
        g_conv_res += (src_ccu, dst_ccu)
    elif len(g_conv_res) != 0:
        temp = g_conv_res
        g_conv_res = ccut.convert_ccu2ccu(temp[6][g_conv_src_idx-1], temp[7][g_conv_dst_idx-1], temp[3])
        g_conv_res += (temp[3], temp[4], temp[5], temp[6], temp[7])

    return render_template('ccu_convert.html', form=form, result=g_conv_res,\
                           src_idx=g_conv_src_idx, dst_idx=g_conv_dst_idx)

@app.route('/update_convert', methods=['GET'])
def update_convert():
    ''' API to handle choosing radio-button options for conversion '''

    global g_conv_src_idx, g_conv_dst_idx

    ARG_IN_OR_OUT = 'cu'
    ARG_IDX = 'i'
    if ARG_IN_OR_OUT in request.args and ARG_IDX in request.args:
        if request.args.get(ARG_IN_OR_OUT) == 'in':
            g_conv_src_idx = int(request.args.get(ARG_IDX))
        else:
            g_conv_dst_idx = int(request.args.get(ARG_IDX))

    return redirect(url_for('convert'))

@app.route('/annotate', methods=['GET', 'POST'])
def load_annotation_file():
    ''' Page to handle uploading annotation file (json). Redirects to editor-UI '''

    global g_active_json, g_active_filename

    form = FileUploadForm()
    if form.validate_on_submit():
        f = form.in_file.data
        filename = secure_filename(f.filename)
        if not exists(STORAGE_FOLDER):
            makedirs(STORAGE_FOLDER)
        g_active_filename = STORAGE_FOLDER + filename
        f.save(g_active_filename)
        with open(g_active_filename, 'r') as read_file_h:
            g_active_json = load(read_file_h)
        return redirect(url_for('edit_annotation_file'))
    else:
        return render_template('file_upload.html', form=form, title='Upload annotation file', file_ext='.json')

@app.route('/process_tables', methods=['GET', 'POST'])
def process_spreadsheet_file():
    ''' Page to handle processing excel file (xlsx). Creates json and redirects to editor-UI '''

    global g_active_json, g_active_filename

    form = FileUploadForm()
    if form.validate_on_submit():
        f = form.in_file.data
        filename = secure_filename(f.filename)
        if not exists(STORAGE_FOLDER):
            makedirs(STORAGE_FOLDER)
        spreadsheet_fname = STORAGE_FOLDER + filename
        f.save(spreadsheet_fname)
        g_active_json, _ = process_file(spreadsheet_fname)
        g_active_filename = '.'.join(spreadsheet_fname.split('.')[:-1]) + '.ccut.json'
        with open(g_active_filename, 'w') as outfile:
            dump(g_active_json, outfile, indent=2)

        # TODO: color original xlsx
        return redirect(url_for('edit_annotation_file'))
    else:
        return render_template('file_upload.html', form=form, title='Process spreadsheet file', file_ext='.xlsx')

@app.route('/edit', methods=['GET', 'POST'])
def edit_annotation_file():
    ''' Page holding the json editor-UI '''

    global g_active_json, g_active_filename

    init_flat_search_lists(g_active_json)
    form = AnnotationEditForm()
    if form.validate_on_submit():
        add_annotation_to_cell(g_active_json, form.q_sheet.data, form.cell.data, \
                               form.m.data, form.q_prefix.data, form.q_unit.data, form.e.data)
        update_cell_dimension(g_active_json, form.q_sheet.data, form.cell.data)

    return render_template('ccu_json_edit.html', ant_dict=g_active_json, fname=g_active_filename, form=form)

@app.route('/save')
def save_annotation_file():
    ''' API to save the json annotation file '''

    global g_active_json, g_active_filename

    if g_active_filename != "":
        with open(g_active_filename, 'w') as outfile:
            dump(g_active_json, outfile, indent=2)

    return redirect(url_for('edit_annotation_file'))

@app.route('/remove', methods=['GET'])
def remove_element_in_annotation_file():
    ''' API to remove an element (unit-part, cell or sheet) from annotation dictionary '''

    global g_active_json

    ARG_SHEET = 's'
    ARG_COL = 'c'
    ARG_ROW = 'r'
    ARG_IDX = 'i' # part index in cell
    if ARG_SHEET in request.args:
        sheet = request.args.get(ARG_SHEET)
        if ARG_COL in request.args:
            col = request.args.get(ARG_COL)
            if ARG_ROW in request.args:
                row = request.args.get(ARG_ROW)
                if ARG_IDX in request.args:
                    idx = request.args.get(ARG_IDX)
                    del g_active_json[sheet][col][row][0]['parts'][int(idx)-1]
                    update_cell_dimension(g_active_json, sheet, col+row)
                    # if there are more unit-parts in cell, return
                    if len(g_active_json[sheet][col][row][0]['parts']) != 0:
                        return redirect(url_for('edit_annotation_file'))
                    # otherwise, continute to remove row (cell)
                del g_active_json[sheet][col][row]
                # if there are no more rows in col, delete col
                if len(g_active_json[sheet][col]) == 0:
                    del g_active_json[sheet][col]
                # if there are more cols in sheet, return
                if len(g_active_json[sheet]) != 0:
                    return redirect(url_for('edit_annotation_file'))
                # otherwise, continute to remove sheet
        del g_active_json[sheet]

    return redirect(url_for('edit_annotation_file'))

@app.route("/edit/<string:box>")
def process(box):
    ''' API to get auto-complete suggestions for a given text box '''

    query = request.args.get('query')
    suggestions = list()
    if box == 'q_sheet':
        suggest_list = fuzzy_search_sheet(query)
    if box == 'q_prefix':
        suggest_list = fuzzy_search_prefix(query)
    if box == 'q_unit':
        suggest_list = fuzzy_search_unit(query)
    for itm in suggest_list:
        suggestions.append({'value': itm[0], 'data': itm[0]})

    return jsonify({"suggestions":suggestions})

if __name__ == "__main__":
    ''' Main/Entry point '''

    app.run(host='0.0.0.0', port=5000, debug=True)