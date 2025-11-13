import time
from typing import Dict, List, Tuple, Optional
from fastapi import FastAPI
from pydantic import BaseModel

from models import Generator
from external_models import OpenAIRunner
from loguru import logger


GPT5_MINI_MODEL_NAME = "gpt-5-nano"


class GeneratorRequest(BaseModel):
    name: str
    input: str
    prefix: Optional[str]


class Generation(BaseModel):
    output: str
    score: float


class GeneratorResponse(BaseModel):
    outputs: List[Generation]


app = FastAPI()


generators: Dict[str, Generator] = {
    GPT5_MINI_MODEL_NAME: OpenAIRunner(
        model=GPT5_MINI_MODEL_NAME,
        temperature=0.3,
        max_tokens=1024,
        top_p=0.9,
        frequency_penalty=0,
        presence_penalty=0,
        num_return_sequences=5,
        openai_timeout=45,
    ),
}


@app.post("/generate")
async def generate(req: GeneratorRequest) -> GeneratorResponse:
    start = time.perf_counter()
    if req.name not in generators:
        logger.error("Unknown generator requested: {}", req.name)
        raise RuntimeError(
            f"Unknown generator '{req.name}'. Only {GPT5_MINI_MODEL_NAME} is supported."
        )
    model = generators[req.name]
    target_prefix = req.prefix if req.prefix is not None else ""
    outputs: List[Tuple[str, float]] = model.generate(req.input, target_prefix)
    duration = time.perf_counter() - start
    logger.info(
        "generate name={} chars={} prefix={} suggestions={} duration={:.2f}s",
        req.name,
        len(req.input),
        len(target_prefix),
        len(outputs),
        duration,
    )
    return GeneratorResponse(
        outputs=[Generation(output=out[0], score=out[1]) for out in outputs]
    )
