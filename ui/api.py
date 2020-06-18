''' This is the API entry point (and Flask front end) '''

from os import makedirs
from os.path import exists
from json import load
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, jsonify, render_template, url_for
from forms import TransformationForm, RepresentationForm, AnnotationForm
from ccut import ccut
from ccut.main.config import Config

STORAGE_FOLDER = '/tmp/ccut_uploads/'

app = Flask(__name__)
app.config.from_object(Config)
ccut = ccut()
g_active_json = dict()

@app.route("/")
def hello():
    return render_template('generic.html', data='Welcome to CCUT Wrapper!')

@app.route('/get_canonical_json', methods=['GET', 'POST'])
def get_canonical_json():
    if "u" in request.args:
        unit_string = request.args.get("u")
        return jsonify(ccut.get_top_ccu(unit_string))
    form = RepresentationForm()
    return render_template('ccu_represent.html', form=form)

@app.route('/trans_form', methods=['GET', 'POST'])
def transform_ccu():
    if "in_unit" in request.args and "out_unit" in request.args and "in_val" in request.args:
        unit_in_string = request.args.get("in_unit")
        unit_out_string = request.args.get("out_unit")
        val_in = float(request.args.get("in_val"))
        return jsonify(ccut.convert_str2str(unit_in_string, unit_out_string, val_in))
    form = TransformationForm()
    return render_template('ccu_transform.html', form=form)

@app.route('/annotate', methods=['GET', 'POST'])
def load_annotation_file():
    global g_active_json

    ant_form = AnnotationForm()
    if ant_form.validate_on_submit():
        f = ant_form.in_file.data
        filename = secure_filename(f.filename)
        if not exists(STORAGE_FOLDER):
            makedirs(STORAGE_FOLDER)
        g_active_filename = STORAGE_FOLDER + filename
        f.save(g_active_filename)
        with open(g_active_filename, 'r') as read_file_h:
            g_active_json = load(read_file_h)
        return redirect(url_for('edit_annotation_file'))
    else:
        return render_template('ant_file_upload.html', form=ant_form)

@app.route('/eannotate', methods=['GET', 'POST'])
def edit_annotation_file():
    global g_active_json

    return render_template('ant_file_view.html', ant_dict=g_active_json)

#########################################################################

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
