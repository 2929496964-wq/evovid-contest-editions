"""Bounded storyboard protocol adapted from EvoVid Pocket's MIT Scene/Storyboard."""
from typing import Literal
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

Mode = Literal['demo', 'live']
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Search(Strict):
    query: str = Field(min_length=2, max_length=100)
    category: Literal['movie', 'artist'] = 'movie'
    mode: Mode = 'demo'
    public_reference: Literal[True]

    @field_validator('query')
    @classmethod
    def public_query(cls, value):
        if re.search(r'[@<>\\\n\r]|https?://|www\.|\b\d[\d\s()+-]{7,}\d\b', value, re.I):
            raise ValueError('Use a public movie title or artist stage name, without contact details, URLs or identifiers.')
        return value

class Plan(Strict):
    entity_ids: list[str] = Field(min_length=1, max_length=4)
    mode: Mode = 'demo'
    goal: str = Field(default='Find a little wonder in an ordinary day', min_length=3, max_length=160)
    duration: Literal[12, 16, 20, 24] = 16
    aspect: Literal['16:9', '9:16', '1:1'] = '16:9'
    pace: Literal['reflective', 'balanced', 'energetic'] = 'balanced'
    budget: Literal['phone-only', 'small-crew'] = 'phone-only'
    parent_id: str | None = None
    request_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{8,80}$')

    @field_validator('entity_ids')
    @classmethod
    def unique(cls, value):
        if len(set(value)) != len(value):
            raise ValueError('Choose each reference once.')
        return value

class Scene(Strict):
    title: str = Field(min_length=1, max_length=70)
    caption: str = Field(min_length=1, max_length=180)
    seconds: int = Field(ge=2, le=6)
    camera: Literal['locked', 'push', 'pan', 'orbit'] = 'push'
    evidence_ids: list[str] = Field(default_factory=list, max_length=8)

class Edit(Strict):
    version: int = Field(ge=1)
    brief_index: int = Field(ge=0, le=2)
    title: str = Field(min_length=1, max_length=100)
    scenes: list[Scene] = Field(min_length=4, max_length=4)

class Render(Strict):
    version: int = Field(ge=1)
    request_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{8,80}$')
