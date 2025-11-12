from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

from models import *
from external_models import OpenAIRunner

app = FastAPI()

models = {
    "gpt-5-mini": OpenAIRunner(
        model="gpt-5-mini",
        temperature=None,
        max_tokens=1024,
        top_p=None,
        frequency_penalty=None,
        presence_penalty=None,
        reasoning={"effort": "medium"},
        num_return_sequences=5,
        openai_timeout=45,
    ),
    "gpt-5-nano": OpenAIRunner(
        model="gpt-5-nano",
        temperature=None,
        max_tokens=1024,
        top_p=None,
        frequency_penalty=None,
        presence_penalty=None,
        reasoning={"effort": "medium"},
        num_return_sequences=5,
        openai_timeout=45,
    ),
}


class GeneratorRequest(BaseModel):
    name: str
    input: str
    prefix: Optional[str]


class Generation(BaseModel):
    output: str
    score: float


class GeneratorResponse(BaseModel):
    outputs: List[Generation]


class EncoderRequest(BaseModel):
    name: str
    input: str


class EncoderResponse(BaseModel):
    outputs: List[float]


@app.post("/generate")
async def generate(req: GeneratorRequest) -> GeneratorResponse:
    model = models[req.name]
    target_prefix = req.prefix if req.prefix is not None else ""
    outputs = model.generate(req.input, target_prefix)
    return GeneratorResponse(
        outputs=[Generation(output=out[0], score=out[1]) for out in outputs]
    )


@app.post("/encode")
async def encode(req: EncoderRequest) -> EncoderResponse:
    model = models[req.name]
    feature = model.encode(req.input)
    return EncoderResponse(outputs=feature.tolist())
