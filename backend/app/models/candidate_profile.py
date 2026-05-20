from pydantic import BaseModel, Field

from app.schemas import field_descriptions as fd


class IdentitySection(BaseModel):
    name: str = Field(description=fd.IDENTITY_NAME)
    confidence: float = Field(ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class CandidateTechItem(BaseModel):
    name: str = Field(description=fd.TECH_NAME)
    years: float | None = Field(description=fd.TECH_CV_YEARS)


class TechnologiesSection(BaseModel):
    items: list[CandidateTechItem] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class SoftSkillsSection(BaseModel):
    items: list[str] = Field(default_factory=list, description=fd.SOFT_SKILL)
    confidence: float = Field(ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class LeadershipSection(BaseModel):
    tech_lead: bool = Field(description=fd.TECH_LEAD)
    team_lead: bool = Field(description=fd.TEAM_LEAD)
    confidence: float = Field(ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class EducationItem(BaseModel):
    level: str = Field(description=fd.EDU_ITEM_LEVEL)
    field: str = Field(description=fd.EDU_ITEM_FIELD)


class EducationSection(BaseModel):
    items: list[EducationItem] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class ExperienceSection(BaseModel):
    total_years: float | None = Field(default=None, description=fd.EXP_TOTAL)
    confidence: float = Field(ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class CandidateProfile(BaseModel):
    reasoning: str = Field(description=fd.REASONING)
    ambiguities: list[str] = Field(default_factory=list, description=fd.AMBIGUITIES)
    identity: IdentitySection
    technologies: TechnologiesSection
    soft_skills: SoftSkillsSection
    leadership: LeadershipSection
    education: EducationSection
    experience: ExperienceSection
