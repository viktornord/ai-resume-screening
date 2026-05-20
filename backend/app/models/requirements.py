from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import field_descriptions as fd

Seniority = Literal["junior", "mid", "senior", "lead", "unknown"]
TechPriority = Literal["must", "nice"]


class RoleSection(BaseModel):
    title: str = Field(default="", description=fd.ROLE_TITLE)
    seniority: Seniority = Field(default="unknown", description=fd.ROLE_SENIORITY)
    confidence: float = Field(default=0.5, ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class TechItem(BaseModel):
    name: str = Field(description=fd.TECH_NAME)
    min_years: float | None = Field(description=fd.TECH_MIN_YEARS)
    priority: TechPriority = Field(description=fd.TECH_PRIORITY)


class TechnologiesSection(BaseModel):
    items: list[TechItem] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class SoftSkillsSection(BaseModel):
    items: list[str] = Field(default_factory=list, description=fd.SOFT_SKILL)
    confidence: float = Field(default=0.5, ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class LeadershipSection(BaseModel):
    tech_lead: bool = Field(default=False, description=fd.TECH_LEAD)
    team_lead: bool = Field(default=False, description=fd.TEAM_LEAD)
    confidence: float = Field(default=0.5, ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class EducationSection(BaseModel):
    min_level: str | None = Field(default=None, description=fd.EDU_MIN_LEVEL)
    fields: list[str] = Field(default_factory=list, description=fd.EDU_FIELDS)
    required: bool = Field(default=False, description=fd.EDU_REQUIRED)
    confidence: float = Field(default=0.5, ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class ExperienceSection(BaseModel):
    min_total_years: float | None = Field(default=None, description=fd.EXP_MIN_TOTAL)
    confidence: float = Field(default=0.5, ge=0, le=1, description=fd.SECTION_CONFIDENCE)


class Requirements(BaseModel):
    reasoning: str = Field(default="", description=fd.REASONING)
    ambiguities: list[str] = Field(default_factory=list, description=fd.AMBIGUITIES)
    role: RoleSection
    technologies: TechnologiesSection
    soft_skills: SoftSkillsSection
    leadership: LeadershipSection
    education: EducationSection
    experience: ExperienceSection
