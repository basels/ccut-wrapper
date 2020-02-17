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
```
curl -X GET "http://0.0.0.0:5000/get_canonical_json?u=km%20s^2"
```
#### Get Units Transformation
```
curl -X GET "http://0.0.0.0:5000/trans_form?in_unit=km&out_unit=ft&in_val=0.3049"
```

### Spreadsheets Validator:
TBD