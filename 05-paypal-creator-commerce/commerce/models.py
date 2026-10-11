"""EvoVid bounded storyboard protocol, extended for the creator-commerce fork."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Scene(Strict):
    title: str = Field(min_length=1, max_length=65)
    caption: str = Field(default='', max_length=140)
    seconds: int = Field(default=3, ge=2, le=6)
    accent: Literal['lime','violet','cyan','orange'] = 'lime'

class Board(Strict):
    title: str = Field(min_length=1, max_length=80)
    scenes: list[Scene] = Field(min_length=2,max_length=5)
    @model_validator(mode='after')
    def bound_duration(self):
        if sum(s.seconds for s in self.scenes)>24: raise ValueError('Maximum duration is 24 seconds.')
        return self

class NewProject(Strict):
    brief: str = Field(min_length=8,max_length=1200)
    planner: Literal['fixture','local-ai'] = 'fixture'

class EditProject(Strict):
    expected_revision: int = Field(ge=1)
    board: Board

class ImportProject(Strict):
    format: Literal['evovid-creator-commerce-v1']
    board: Board

class Checkout(Strict):
    project_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    revision: int = Field(ge=1)
    sku: Literal['portrait-hd-export'] = 'portrait-hd-export'

class FixtureAction(Strict):
    scenario: Literal['completed','pending','declined','wrong-amount','wrong-currency','wrong-merchant','wrong-order','wrong-reference','lost-response'] = 'completed'
