
import re

with open("tests/test_analytics_tools.py", "r") as f:
    text = f.read()

# Add missing imports to the top
text = text.replace("yield_statistics,", "yield_statistics,\n    compare_datasets,\n    top_yield_conditions,\n    dataset_quality_report,")

# Remove the old import block for compare_datasets at the bottom
text = re.sub(r"from backend\.tools\.analytics_tools import compare_datasets.*?\n", "", text)
text = re.sub(r"import os\n\nDB_PATH = os\.path\.join\(\"backend\", \"database\", \"ord\.duckdb\"\)\n", "", text)

# Replace DB_PATH with DEFAULT_DB_PATH
text = text.replace("database_path=DB_PATH", "database_path=DEFAULT_DB_PATH")

with open("tests/test_analytics_tools.py", "w") as f:
    f.write(text)

