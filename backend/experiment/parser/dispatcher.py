import logging
import mimetypes
from typing import Any

from backend.experiment.models import CanonicalExperiment
from backend.experiment.parser.parser_csv import parse_csv
from backend.experiment.parser.parser_json import parse_json
from backend.experiment.parser.parser_text import parse_text
from backend.experiment.parser.parser_xlsx import parse_xlsx

logger = logging.getLogger(__name__)


def dispatch_parse(data: bytes, filename: str, mime_type: str | None = None) -> tuple[list[CanonicalExperiment], str]:
    """
    Determine the parser from mime_type and filename, then parse the data.
    Returns the parsed experiments and the parser name used.
    """
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(filename)
        
    mime_type = mime_type or ""
    mime_type = mime_type.lower()
    filename_lower = filename.lower()
    
    parser_used = "unknown"
    experiments = []
    
    try:
        if mime_type == "application/json" or filename_lower.endswith(".json"):
            parser_used = "json"
            experiments = parse_json(data, source=filename)
            
        elif mime_type == "text/csv" or filename_lower.endswith(".csv"):
            parser_used = "csv"
            experiments = parse_csv(data, source=filename)
            
        elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" or filename_lower.endswith(".xlsx"):
            parser_used = "xlsx"
            experiments = parse_xlsx(data, source=filename)
            
        elif mime_type.startswith("text/") or filename_lower.endswith(".txt"):
            parser_used = "text"
            experiments = parse_text(data, source=filename)
            
        else:
            # Fallback to text parsing if we can decode it
            parser_used = "text (fallback)"
            experiments = parse_text(data, source=filename)
            
    except Exception as e:
        logger.error(f"Failed to parse {filename} using {parser_used} parser: {e}")
        raise ValueError(f"Parsing failed for {filename} using {parser_used} parser") from e
        
    return experiments, parser_used
