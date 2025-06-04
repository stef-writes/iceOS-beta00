from pydantic import BaseModel, Field
from typing import List
from app.tools.base import BaseTool
import re

class TranscriptParserParams(BaseModel):
    raw_transcript_text: str = Field(..., description="The full transcript as plain text.")

class Utterance(BaseModel):
    timestamp: str
    speaker: str
    text: str

class TranscriptParserOutput(BaseModel):
    utterances: List[Utterance]

class TranscriptParserTool(BaseTool):
    name = "transcript_parser"
    description = "Parses a raw transcript into a list of utterances with timestamp, speaker, and text."
    parameters_schema = TranscriptParserParams
    output_schema = TranscriptParserOutput
    usage_example = '{"function_call": {"name": "transcript_parser", "arguments": {"raw_transcript_text": "[00:00:01] Alice: Hi everyone..."}}}'

    def run(self, raw_transcript_text: str) -> dict:
        utterances = []
        # Regex for [timestamp] Speaker: text, robust to whitespace
        pattern = re.compile(r"^\s*\[(\d{2}:\d{2}:\d{2})\]\s*(.*?):\s*(.*)$")
        for line in raw_transcript_text.splitlines():
            line = line.strip()
            match = pattern.match(line)
            if match:
                timestamp, speaker, text = match.groups()
                utterances.append({"timestamp": timestamp, "speaker": speaker, "text": text})
        return {"utterances": utterances} 