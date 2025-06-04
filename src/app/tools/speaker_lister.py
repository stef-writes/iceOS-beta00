from pydantic import BaseModel, Field
from typing import List
from app.tools.base import BaseTool

class SpeakerListerParams(BaseModel):
    utterances: List[dict] = Field(..., description="List of utterances, each with timestamp, speaker, and text.")

class SpeakerListerOutput(BaseModel):
    speakers: List[str]

class SpeakerListerTool(BaseTool):
    name = "speaker_lister"
    description = "Extracts a list of unique speakers from a list of utterances."
    parameters_schema = SpeakerListerParams
    output_schema = SpeakerListerOutput
    usage_example = '{"function_call": {"name": "speaker_lister", "arguments": {"utterances": [{"timestamp": "00:00:01", "speaker": "Alice", "text": "Hi"}]}}}'

    def run(self, utterances: List[dict]) -> dict:
        speakers = list({u.get("speaker") for u in utterances if u.get("speaker")})
        return {"speakers": speakers} 