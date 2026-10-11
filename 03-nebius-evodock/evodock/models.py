"""EvoVid's strict storyboard boundary extended with asset IDs and revisions."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

ASSETS = {
    'orbit': 'Orbital circles on a midnight canvas',
    'product': 'Abstract product pedestal',
    'nature': 'Geometric sunrise and hills',
    'type': 'Clean kinetic typography',
}
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
class Scene(Strict):
    id: str = Field(pattern=r'^s[1-8]$')
    asset_id: Literal['orbit','product','nature','type']
    title: str = Field(min_length=1, max_length=70)
    caption: str = Field(max_length=180)
    seconds: int = Field(ge=2, le=8)
    motion: Literal['drift','pulse','rise']
    color: Literal['mint','amber','violet','sky']
class Storyboard(Strict):
    title: str = Field(min_length=1, max_length=100)
    scenes: list[Scene] = Field(min_length=2, max_length=6)
    @model_validator(mode='after')
    def boundaries(self):
        if len({s.id for s in self.scenes}) != len(self.scenes):
            raise ValueError('Scene IDs must be unique.')
        if sum(s.seconds for s in self.scenes) > 36:
            raise ValueError('The entire video must be 36 seconds or shorter.')
        return self
class PlanRequest(Strict):
    brief: str = Field(min_length=4, max_length=1200)
    mode: Literal['fixture','live'] = 'fixture'
    model: str = Field(default='', max_length=200)
    consent_to_transmit: bool = False
class RevisionRequest(Strict):
    instruction: str = Field(min_length=3, max_length=500)
    expected_revision: int = Field(ge=1)
    model: str = Field(default='', max_length=200)
    consent_to_transmit: bool = False
class EditRequest(Strict):
    storyboard: Storyboard
    expected_revision: int = Field(ge=1)
class RenderRequest(Strict):
    expected_revision: int = Field(ge=1)
    confirmed: bool = False
