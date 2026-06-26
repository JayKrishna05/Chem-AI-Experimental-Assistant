
import re

with open("backend/api/routes.py", "r") as f:
    text = f.read()

# We will replace the entire bottom part
replacement = """# ---------------------------------------------------------------------------
# Upload & Compare endpoints
# ---------------------------------------------------------------------------

from fastapi import Request, File, UploadFile
import json
from backend.api.models import UploadExperimentRequest, ParseExperimentResponse, CompareExperimentResponse
from backend.experiment.parser import dispatch_parse
from backend.experiment.normalizer import normalize_experiment
from backend.experiment.validator import validate_experiment
from backend.services.comparison_service import compare_experiment


async def _parse_and_validate(request: Request, file: UploadFile | None = None) -> list[Any]:
    content_type = request.headers.get("content-type", "").lower()
    
    exps = []
    
    if "multipart/form-data" in content_type and file:
        data = await file.read()
        exps, _ = dispatch_parse(data, filename=file.filename, mime_type=file.content_type)
    elif "application/json" in content_type:
        body = await request.json()
        req_obj = UploadExperimentRequest(**body)
        
        # Simulate file based on format
        if req_obj.format == "json":
            exps, _ = dispatch_parse(req_obj.content.encode("utf-8"), "upload.json", "application/json")
        elif req_obj.format == "csv":
            exps, _ = dispatch_parse(req_obj.content.encode("utf-8"), "upload.csv", "text/csv")
        else:
            exps, _ = dispatch_parse(req_obj.content.encode("utf-8"), "upload.txt", "text/plain")
    else:
        raise ValueError("Unsupported content type or missing file")
        
    results = []
    for exp in exps:
        normalized_exp, normalized_fields = normalize_experiment(exp)
        validation_result = validate_experiment(normalized_exp, normalized_fields)
        results.append(validation_result)
        
    return results


@router.post("/experiments/parse", response_model=ParseExperimentResponse)
async def experiments_parse(request: Request, file: UploadFile | None = File(None)) -> ParseExperimentResponse:
    \"\"\"Parse and validate an uploaded experiment payload (supports multipart file uploads and legacy JSON).\"\"\"
    try:
        results = await _parse_and_validate(request, file)
        if not results:
            return ParseExperimentResponse(experiments=[], warnings=["No experiments parsed"], is_valid=False)
            
        experiments = [res.experiment.model_dump() for res in results]
        warnings = []
        is_valid = True
        for res in results:
            warnings.extend(res.warnings)
            if not res.is_valid:
                is_valid = False
                
        return ParseExperimentResponse(
            experiments=experiments,
            warnings=list(set(warnings)),
            is_valid=is_valid
        )
    except Exception as exc:
        handle_tool_error(exc)


@router.post("/experiments/compare", response_model=CompareExperimentResponse)
async def experiments_compare(request: Request, file: UploadFile | None = File(None)) -> CompareExperimentResponse:
    \"\"\"Parse, validate, and compare uploaded experiments against the database (supports multipart file uploads and legacy JSON).\"\"\"
    try:
        validation_results = await _parse_and_validate(request, file)
        
        comparisons = []
        for res in validation_results:
            comp_report = compare_experiment(res)
            comparisons.append(comp_report)
            
        return CompareExperimentResponse(comparisons=comparisons)
    except Exception as exc:
        handle_tool_error(exc)
"""

text = re.sub(r"# ---------------------------------------------------------------------------\n# Upload & Compare endpoints.*", replacement, text, flags=re.DOTALL)

with open("backend/api/routes.py", "w") as f:
    f.write(text)

