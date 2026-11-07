from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="participant")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    submissions: Mapped[list["Submission"]] = relationship(back_populates="user")
    registrations: Mapped[list["Registration"]] = relationship(back_populates="user")
    contests: Mapped[list["Contest"]] = relationship(back_populates="organizer")


class Problem(Base):
    __tablename__ = "Problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    short_description: Mapped[str] = mapped_column(String(400))
    statement: Mapped[str] = mapped_column(Text)
    input_format: Mapped[str] = mapped_column(Text)
    output_format: Mapped[str] = mapped_column(Text)
    constraints: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tests: Mapped[list["TestCase"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="TestCase.order_index",
    )


class TestCase(Base):
    __tablename__ = "TestCases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problems.id", ondelete="CASCADE"), index=True)
    input_data: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    problem: Mapped[Problem] = relationship(back_populates="tests")


class Contest(Base):
    __tablename__ = "Contests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizer: Mapped[User] = relationship(back_populates="contests")
    contest_problems: Mapped[list["ContestProblem"]] = relationship(
        back_populates="contest",
        cascade="all, delete-orphan",
        order_by="ContestProblem.order_index",
    )
    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="contest",
        cascade="all, delete-orphan",
    )


class ContestProblem(Base):
    __tablename__ = "ContestProblems"
    __table_args__ = (UniqueConstraint("contest_id", "problem_id", name="uq_contest_problem"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("Contests.id", ondelete="CASCADE"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problems.id"), index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    contest: Mapped[Contest] = relationship(back_populates="contest_problems")
    problem: Mapped[Problem] = relationship()


class Registration(Base):
    __tablename__ = "Registrations"
    __table_args__ = (UniqueConstraint("contest_id", "user_id", name="uq_registration"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("Contests.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id", ondelete="CASCADE"), index=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contest: Mapped[Contest] = relationship(back_populates="registrations")
    user: Mapped[User] = relationship(back_populates="registrations")


class Submission(Base):
    __tablename__ = "Submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("Problems.id"), index=True)
    contest_id: Mapped[Optional[int]] = mapped_column(ForeignKey("Contests.id"), nullable=True, index=True)
    language: Mapped[str] = mapped_column(String(32))
    source_code: Mapped[str] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(String(8), index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    runtime_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    tests_total: Mapped[int] = mapped_column(Integer, default=0)
    judge_mode: Mapped[str] = mapped_column(String(16), default="demo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped[User] = relationship(back_populates="submissions")
    problem: Mapped[Problem] = relationship()
    contest: Mapped[Optional[Contest]] = relationship()
