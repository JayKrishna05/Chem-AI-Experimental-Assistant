
import re

with open("tests/test_experiment_upload.py", "r") as f:
    text = f.read()

text = text.replace("from backend.experiment.parser import parse_json, parse_csv, parse_text", "from backend.experiment.parser import dispatch_parse")
text = text.replace("parse_json(", "dispatch_parse(")
text = text.replace("parse_csv(", "dispatch_parse(")
text = text.replace("parse_text(", "dispatch_parse(")

with open("tests/test_experiment_upload.py", "w") as f:
    f.write(text)

