''' The following form classes are used in the UI '''

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class ParseForm(FlaskForm):
    u        = StringField('Compound Unit',  validators=[DataRequired()])
    submit   = SubmitField('Parse')

class ConversionForm(FlaskForm):
    in_unit  = StringField('Input Compound Unit',  validators=[DataRequired()])
    out_unit = StringField('Output Compound Unit', validators=[DataRequired()])
    in_val   = StringField('Input Value', validators=[DataRequired()], default=1)
    submit   = SubmitField('Convert')

class FileUploadForm(FlaskForm):
    in_file  = FileField(validators=[FileRequired()])
    submit   = SubmitField('Upload')

class AnnotationEditForm(FlaskForm):
    q_sheet  = StringField('Sheet', validators=[DataRequired()])
    cell     = StringField('Cell',  validators=[DataRequired()])
    m        = StringField('Multiplier')
    q_prefix = StringField('Prefix')
    q_unit   = StringField('Unit',  validators=[DataRequired()])
    e        = StringField('Exponent')
    submit   = SubmitField('Add')
