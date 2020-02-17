# CCUT Wrapper
Wrapper infrastructure (UI/Evaluation) for [CCUT](https://github.com/basels/ccut/). A framework for the identification and transformation of units of measure.

This repository provides the following:
* Allows running the CCUT service over a UI (and an accessible HTTP endpoint)
* Provides additional validation tools to run CCUT over spreadsheets (`xlsx`) and validate them (`json`)


### UI:
How to run:
```
python ui/api.py
```
Navigate to `http://localhost:localport/` (usually set as `http://0.0.0.0:5000/`).<br />
The UI allows performing operations over the browser, but also allows running against an HTTP endpoint.

#### Get Unit Representation
This example retrieves the representation of `km/s^2`:
```
curl -X GET "http://0.0.0.0:5000/get_canonical_json?u=km%20s^2"
```

#### Get Units Transformation
This example provides the conversion value (and summary dictionary) of converting the value `0.3049` of source unit `km` to `ft`:
```
curl -X GET "http://0.0.0.0:5000/trans_form?in_unit=km&out_unit=ft&in_val=0.3049"
```


### Spreadsheets Validator:
#### Generate a `json` dictionary file of detected units
Run `ccut_sheets.py` over an `xlsx` file. As in:
```
python validator/ccut_sheets.py -i my_spreadsheet.xlsx
```
This will produce a file called `my_spreadsheet.ccut.json`

#### Validate a directory of spreadsheets files and their `json` results files
Run `ccut_sheets_validator.py` over a directory of `xlsx` files and their matching `json`s. As in:
```
python validator/ccut_sheets_validator.py -d my_dir/
```