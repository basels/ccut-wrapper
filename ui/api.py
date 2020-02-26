''' This is the API entry point (and Flask front end) '''

from flask import Flask, request, jsonify, render_template
from forms import TransformationForm, RepresentationForm
from ccut import ccut
from ccut.main.config import Config
from ccut.main.dimension_map import DimensionMap

app = Flask(__name__)
app.config.from_object(Config)
ccut = ccut()

@app.route("/")
def hello():
    return render_template('generic.html', data='Welcome to MINT CCUT!')

@app.route("/get_dimension_map")
def get_dimension_map():
    d = DimensionMap.get_instance()
    return jsonify(d.qd_map)

@app.route('/get_canonical_json', methods=['GET', 'POST'])
def get_canonical_json():
    if "u" in request.args:
        unit_string = request.args.get("u")
        return jsonify(ccut.get_top_ccu(unit_string))
    form = RepresentationForm()
    return render_template('ccu_represent.html', title='Canonical Representation', form=form)

@app.route('/trans_form', methods=['GET', 'POST'])
def transform_ccu():
    if "in_unit" in request.args and "out_unit" in request.args and "in_val" in request.args:
        unit_in_string = request.args.get("in_unit")
        unit_out_string = request.args.get("out_unit")
        val_in = float(request.args.get("in_val"))
        return jsonify(ccut.convert_str2str(unit_in_string, unit_out_string, val_in))
    form = TransformationForm()
    return render_template('ccu_transform.html', title='Canonical Transform', form=form)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
