from enum import Enum

from app.model import ModelRunner
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()
runner = ModelRunner()


class ScanDecision(Enum):
    ALLOW = "allow"
    HUMAN_IN_THE_LOOP_REQUIRED = "human_in_the_loop_required"
    BLOCK = "block"


class InferenceInput(BaseModel):
    trace_id: str
    user_inputs: list[str]


class InferenceOutput(BaseModel):
    trace_id: str
    decisions: list[str]


@app.get("/health")
def health():
    if runner.ready:
        return {"status": "ready"}

    return JSONResponse(status_code=503, content={"status": "loading"})


@app.post("/filter", response_model=InferenceOutput)
async def classify_single(data: InferenceInput):
    scores = runner.run(data.user_inputs)

    return {
        "trace_id": data.trace_id,
        "decisions": [
            ScanDecision.ALLOW if _probs[0] > 0.5 else ScanDecision.BLOCK
            for _probs in scores
        ],
    }
