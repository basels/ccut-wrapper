''' This is the API entry point (and Flask front end) '''

from os import makedirs
from os.path import exists
from json import load, dump
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, jsonify, render_template, url_for
from forms import *
from annotate import *
from ccut import ccut
from ccut.main.config import Config
from ccut_sheets import init_globals, process_file

STORAGE_FOLDER = '/tmp/ccut_uploads/'

app = Flask(__name__)
app.config.from_object(Config)
init_globals()
ccut = ccut()
g_active_json = dict()
g_active_filename = ""

@app.route("/")
def hello():
    return render_template('generic.html', data='Welcome to CCUT Wrapper!')

@app.route('/get_canonical_json', methods=['GET', 'POST'])
def get_canonical_json():
    if "u" in request.args:
        unit_string = request.args.get("u")
        return jsonify(ccut.get_top_ccu(unit_string))
    form = RepresentationForm()
    # TODO: show list of all possible representation and choose
    return render_template('ccu_represent.html', form=form)

@app.route('/trans_form', methods=['GET', 'POST'])
def transform_ccu():
    if "in_unit" in request.args and "out_unit" in request.args and "in_val" in request.args:
        unit_in_string = request.args.get("in_unit")
        unit_out_string = request.args.get("out_unit")
        val_in = float(request.args.get("in_val"))
        return jsonify(ccut.convert_str2str(unit_in_string, unit_out_string, val_in))
    form = TransformationForm()
    # TODO: show list of all possible representation and choose
    return render_template('ccu_transform.html', form=form)

@app.route('/annotate', methods=['GET', 'POST'])
def load_annotation_file():
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
        return render_template('file_upload.html', form=form, file_ext='.json')

@app.route('/process_tables', methods=['GET', 'POST'])
def process_spreadsheet_file():
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

        return redirect(url_for('edit_annotation_file'))
    else:
        return render_template('file_upload.html', form=form, file_ext='.xlsx')

@app.route('/search', methods=['GET', 'POST'])
def edit_annotation_file():
    global g_active_json, g_active_filename

    # TODO: ability to remove units from cells (minus icon next to each 'parts')

    init_flat_search_lists(g_active_json)
    form = AnnotationEditForm()
    if form.validate_on_submit():
        add_annotation_to_cell(g_active_json,
                               form.q_sheet.data,
                               form.cell.data,
                               form.m.data,
                               form.q_prefix.data,
                               form.q_unit.data,
                               form.e.data)

    return render_template('ccu_search.html', ant_dict=g_active_json, fname=g_active_filename, form=form)

@app.route('/save')
def save_annotation_file():
    global g_active_json, g_active_filename

    if g_active_filename != "":
        with open(g_active_filename, 'w') as outfile:
            dump(g_active_json, outfile, indent=2)

    return redirect(url_for('edit_annotation_file'))

@app.route("/search/<string:box>")
def process(box):
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

#########################################################################

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
