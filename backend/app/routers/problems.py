from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_optional_user
from ..models import Problem, Submission, User
from ..schemas import ProblemDetail, ProblemOut
from ..services import solved_problem_ids

router = APIRouter(prefix="/problems", tags=["problems"])


def accepted_counts(db: Session) -> dict[int, int]:
    rows = (
        db.query(Submission.problem_id, func.count(Submission.id))
        .filter(Submission.verdict == "OK")
        .group_by(Submission.problem_id)
        .all()
    )
    return {problem_id: count for problem_id, count in rows}


def to_problem_out(problem: Problem, counts: dict[int, int], solved: set[int]) -> ProblemOut:
    return ProblemOut(
        id=problem.id,
        title=problem.title,
        short_description=problem.short_description,
        difficulty=problem.difficulty,
        accepted_count=counts.get(problem.id, 0),
        solved_by_me=problem.id in solved,
    )


@router.get("", response_model=list[ProblemOut])
def list_problems(
    search: str = "",
    difficulty: str = "",
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> list[ProblemOut]:
    problems = db.query(Problem).order_by(Problem.id.asc()).all()
    needle = search.strip().casefold()
    if needle:
        problems = [
            problem
            for problem in problems
            if needle in problem.title.casefold() or needle in problem.short_description.casefold()
        ]
    if difficulty in ("easy", "medium", "hard"):
        problems = [problem for problem in problems if problem.difficulty == difficulty]
    elif difficulty:
        raise HTTPException(status_code=400, detail="Неизвестная сложность")
    counts = accepted_counts(db)
    solved = solved_problem_ids(db, user.id if user else None)
    return [to_problem_out(problem, counts, solved) for problem in problems]


@router.get("/{problem_id}", response_model=ProblemDetail)
def get_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> ProblemDetail:
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    counts = accepted_counts(db)
    solved = solved_problem_ids(db, user.id if user else None)
    card = to_problem_out(problem, counts, solved)
    examples = [
        {"input": test.input_data, "output": test.expected_output}
        for test in problem.tests
        if test.is_sample
    ]
    return ProblemDetail(
        **card.model_dump(),
        statement=problem.statement,
        input_format=problem.input_format,
        output_format=problem.output_format,
        constraints=problem.constraints,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        examples=examples,
    )
