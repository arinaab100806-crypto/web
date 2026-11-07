from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: Literal["participant", "organizer"] = "participant"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ExampleOut(BaseModel):
    input: str
    output: str


class ProblemOut(BaseModel):
    id: int
    title: str
    short_description: str
    difficulty: str
    accepted_count: int
    solved_by_me: bool = False


class ProblemDetail(ProblemOut):
    statement: str
    input_format: str
    output_format: str
    constraints: str
    time_limit_ms: int
    memory_limit_mb: int
    examples: list[ExampleOut]


class CodeIn(BaseModel):
    problem_id: int
    language: Literal["python", "cpp", "java", "javascript"]
    source_code: str = Field(min_length=1, max_length=100_000)
    contest_id: Optional[int] = None


class ResultOut(BaseModel):
    verdict: str
    message: Optional[str] = None
    runtime_ms: Optional[int] = None
    tests_passed: int = 0
    tests_total: int = 0
    judge_mode: str
    judge_label: str
    samples_only: bool = False
    failed_input: Optional[str] = None
    failed_expected: Optional[str] = None
    failed_actual: Optional[str] = None


class SubmissionOut(ResultOut):
    id: int
    problem_id: int
    problem_title: Optional[str] = None
    contest_id: Optional[int] = None
    language: str
    source_code: Optional[str] = None
    created_at: str


class ContestIn(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=1, max_length=5000)
    start_time: datetime
    duration_minutes: int = Field(ge=5, le=10080)
    problem_ids: list[int] = Field(min_length=1)


class ContestProblemOut(BaseModel):
    problem_id: int
    order_index: int
    code: str
    title: str
    difficulty: str
    solved_by_me: bool = False


class ContestOut(BaseModel):
    id: int
    title: str
    description: str
    problem_count: int
    start_time: str
    duration_minutes: int
    phase: str
    is_registered: bool
    is_owner: bool
    organizer_name: str
    problems: list[ContestProblemOut] = []


class StandingOut(BaseModel):
    place: int
    user_id: int
    username: str
    solved: int
    time_seconds: int


class DashboardOut(BaseModel):
    username: str
    solved_count: int
    submission_count: int
    contests: list[ContestOut]
    recent_submissions: list[SubmissionOut]


class SystemOut(BaseModel):
    judge_mode: str
    judge_label: str
    languages: list[str]
