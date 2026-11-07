from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_user, get_optional_user, require_organizer
from ..models import Contest, ContestProblem, Registration, User
from ..schemas import ContestIn, ContestOut, ContestProblemOut, StandingOut
from ..services import (
    as_naive_utc,
    build_standings,
    ensure_editable,
    ensure_owner,
    isoformat_utc,
    phase_of,
    problem_letter,
    replace_contest_problems,
    is_registered,
    solved_problem_ids,
    visible_contest,
)

router = APIRouter(prefix="/contests", tags=["contests"])


def _load_contest(db: Session, contest_id: int) -> Contest:
    contest = (
        db.query(Contest)
        .options(
            selectinload(Contest.organizer),
            selectinload(Contest.contest_problems).selectinload(ContestProblem.problem),
            selectinload(Contest.registrations),
        )
        .filter(Contest.id == contest_id)
        .first()
    )
    if contest is None:
        raise HTTPException(status_code=404, detail="Соревнование не найдено")
    return contest


def _to_contest_out(db: Session, contest: Contest, user: Optional[User], with_problems: bool) -> ContestOut:
    solved = solved_problem_ids(db, user.id if user else None, contest.id)
    problems: list[ContestProblemOut] = []
    if with_problems:
        links = sorted(contest.contest_problems, key=lambda item: item.order_index)
        for link in links:
            problems.append(
                ContestProblemOut(
                    problem_id=link.problem_id,
                    order_index=link.order_index,
                    code=problem_letter(link.order_index),
                    title=link.problem.title,
                    difficulty=link.problem.difficulty,
                    solved_by_me=link.problem_id in solved,
                )
            )
    return ContestOut(
        id=contest.id,
        title=contest.title,
        description=contest.description,
        problem_count=len(contest.contest_problems),
        start_time=isoformat_utc(contest.start_time),
        duration_minutes=contest.duration_minutes,
        phase=phase_of(contest),
        is_registered=is_registered(db, contest.id, user.id if user else None),
        is_owner=user is not None and contest.organizer_id == user.id,
        organizer_name=contest.organizer.username,
        problems=problems,
    )


@router.get("", response_model=list[ContestOut])
def list_contests(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> list[ContestOut]:
    contests = (
        db.query(Contest)
        .options(
            selectinload(Contest.organizer),
            selectinload(Contest.contest_problems),
            selectinload(Contest.registrations),
        )
        .all()
    )
    visible = [contest for contest in contests if visible_contest(contest, user)]
    # joinedload can duplicate rows
    unique = {contest.id: contest for contest in visible}
    items = list(unique.values())

    def sort_key(contest: Contest) -> tuple:
        phase = phase_of(contest)
        rank = {"running": 0, "upcoming": 1, "draft": 2, "finished": 3}[phase]
        stamp = contest.start_time.timestamp()
        if phase == "finished":
            stamp = -stamp
        return (rank, stamp)

    items.sort(key=sort_key)
    return [_to_contest_out(db, contest, user, False) for contest in items]


@router.post("", response_model=ContestOut)
def create_contest(
    payload: ContestIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_organizer),
) -> ContestOut:
    contest = Contest(
        title=payload.title.strip(),
        description=payload.description.strip(),
        start_time=as_naive_utc(payload.start_time),
        duration_minutes=payload.duration_minutes,
        status="draft",
        organizer_id=user.id,
    )
    db.add(contest)
    db.flush()
    replace_contest_problems(db, contest, payload.problem_ids)
    db.commit()
    db.expire_all()
    return _to_contest_out(db, _load_contest(db, contest.id), user, True)


@router.get("/{contest_id}", response_model=ContestOut)
def get_contest(
    contest_id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> ContestOut:
    contest = _load_contest(db, contest_id)
    if not visible_contest(contest, user):
        raise HTTPException(status_code=404, detail="Соревнование не найдено")
    return _to_contest_out(db, contest, user, True)


@router.put("/{contest_id}", response_model=ContestOut)
def update_contest(
    contest_id: int,
    payload: ContestIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContestOut:
    contest = _load_contest(db, contest_id)
    ensure_owner(user, contest)
    ensure_editable(contest)
    contest.title = payload.title.strip()
    contest.description = payload.description.strip()
    contest.start_time = as_naive_utc(payload.start_time)
    contest.duration_minutes = payload.duration_minutes
    replace_contest_problems(db, contest, payload.problem_ids)
    db.commit()
    db.expire_all()
    return _to_contest_out(db, _load_contest(db, contest.id), user, True)


@router.post("/{contest_id}/publish", response_model=ContestOut)
def publish_contest(
    contest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContestOut:
    contest = _load_contest(db, contest_id)
    ensure_owner(user, contest)
    if contest.status == "published":
        raise HTTPException(status_code=400, detail="Соревнование уже опубликовано")
    if not contest.contest_problems:
        raise HTTPException(status_code=400, detail="Добавьте хотя бы одну задачу")
    contest.status = "published"
    db.commit()
    db.expire_all()
    return _to_contest_out(db, _load_contest(db, contest.id), user, True)


@router.post("/{contest_id}/register", response_model=ContestOut)
def register_for_contest(
    contest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContestOut:
    contest = _load_contest(db, contest_id)
    if not visible_contest(contest, user) or contest.status != "published":
        raise HTTPException(status_code=404, detail="Соревнование не найдено")
    phase = phase_of(contest)
    if phase == "finished":
        raise HTTPException(status_code=400, detail="Регистрация закрыта: соревнование завершено")
    if phase == "draft":
        raise HTTPException(status_code=400, detail="Нельзя зарегистрироваться на черновик")
    exists = (
        db.query(Registration)
        .filter(Registration.contest_id == contest.id, Registration.user_id == user.id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Вы уже зарегистрированы")
    db.add(Registration(contest_id=contest.id, user_id=user.id))
    db.commit()
    db.expire_all()
    return _to_contest_out(db, _load_contest(db, contest.id), user, True)


@router.delete("/{contest_id}/register", response_model=ContestOut)
def unregister(
    contest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContestOut:
    contest = _load_contest(db, contest_id)
    if not visible_contest(contest, user):
        raise HTTPException(status_code=404, detail="Соревнование не найдено")
    if phase_of(contest) in ("running", "finished"):
        raise HTTPException(status_code=400, detail="Нельзя отменить регистрацию после старта")
    registration = (
        db.query(Registration)
        .filter(Registration.contest_id == contest.id, Registration.user_id == user.id)
        .first()
    )
    if registration is None:
        raise HTTPException(status_code=400, detail="Вы не зарегистрированы")
    db.delete(registration)
    db.commit()
    db.expire_all()
    return _to_contest_out(db, _load_contest(db, contest.id), user, True)


@router.get("/{contest_id}/standings", response_model=list[StandingOut])
def standings(
    contest_id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> list[StandingOut]:
    contest = _load_contest(db, contest_id)
    if not visible_contest(contest, user):
        raise HTTPException(status_code=404, detail="Соревнование не найдено")
    return [StandingOut(**row) for row in build_standings(db, contest)]
