''' The following form classes are used in the UI '''

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class RepresentationForm(FlaskForm):
    u = StringField('Unit',  validators=[DataRequired()])
    submit   = SubmitField('Generate')

class TransformationForm(FlaskForm):
    in_unit  = StringField('Input Unit',  validators=[DataRequired()])
    out_unit = StringField('Output Unit', validators=[DataRequired()])
    in_val   = StringField('Input Value', validators=[DataRequired()])
    submit   = SubmitField('Generate')

class AnnotationUploadForm(FlaskForm):
    in_file  = FileField(validators=[FileRequired()])
    submit   = SubmitField('Upload')

class AnnotationEditForm(FlaskForm):
    cell = StringField('Cell')
    m = StringField('Multiplier')
    e = StringField('Exponent')
    submit = SubmitField('Add')
