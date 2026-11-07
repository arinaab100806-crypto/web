"""Проверка основных сценариев API. Запуск: py -3 smoke_test.py из папки backend."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(tempfile.gettempdir()) / "codearena-smoke.db"
if DB_PATH.exists():
    DB_PATH.unlink()
os.environ["DATABASE_PATH"] = str(DB_PATH)
os.environ["JUDGE0_URL"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402

SOLUTIONS = {
    "Сумма двух чисел": "a, b = map(int, input().split())\nprint(a + b)\n",
    "Максимум из трёх чисел": "print(max(map(int, input().split())))\n",
    "Сумма последовательности": "n = int(input())\nprint(sum(map(int, input().split())))\n",
    "Палиндром": "s = input().strip()\nprint('YES' if s == s[::-1] else 'NO')\n",
    "Факториал": "n = int(input())\nr = 1\nfor i in range(2, n + 1):\n    r *= i\nprint(r)\n",
    "Простое число": (
        "n = int(input())\n"
        "if n < 2:\n"
        "    print('NO')\n"
        "else:\n"
        "    ok = True\n"
        "    i = 2\n"
        "    while i * i <= n:\n"
        "        if n % i == 0:\n"
        "            ok = False\n"
        "            break\n"
        "        i += 1\n"
        "    print('YES' if ok else 'NO')\n"
    ),
    "Число Фибоначчи": "n = int(input())\na, b = 0, 1\nfor _ in range(n):\n    a, b = b, a + b\nprint(a)\n",
    "Максимальная сумма отрезка": (
        "n = int(input())\n"
        "arr = list(map(int, input().split()))\n"
        "best = cur = arr[0]\n"
        "for x in arr[1:]:\n"
        "    cur = max(x, cur + x)\n"
        "    best = max(best, cur)\n"
        "print(best)\n"
    ),
    "Кратчайший путь в графе": (
        "from collections import deque\n"
        "n, m = map(int, input().split())\n"
        "g = [[] for _ in range(n + 1)]\n"
        "for _ in range(m):\n"
        "    u, v = map(int, input().split())\n"
        "    g[u].append(v)\n"
        "    g[v].append(u)\n"
        "s, t = map(int, input().split())\n"
        "dist = [-1] * (n + 1)\n"
        "dist[s] = 0\n"
        "q = deque([s])\n"
        "while q:\n"
        "    u = q.popleft()\n"
        "    for v in g[u]:\n"
        "        if dist[v] == -1:\n"
        "            dist[v] = dist[u] + 1\n"
        "            q.append(v)\n"
        "print(dist[t])\n"
    ),
}


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")
    print(f"OK: {message}")


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        expect(health.status_code == 200 and health.json()["ok"] is True, "health")
        system = client.get("/api/system").json()
        expect(system["judge_mode"] == "demo", "режим проверки демонстрационный")
        expect("Демонстрационный" in system["judge_label"], "подпись демонстрационного режима")

        short = client.post(
            "/api/auth/register",
            json={"username": "ab", "email": "ab@example.com", "password": "123456", "role": "participant"},
        )
        expect(short.status_code == 422, "короткое имя отклоняется")

        participant = client.post(
            "/api/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "secret123",
                "role": "participant",
            },
        )
        expect(participant.status_code == 200, "регистрация участника")
        participant_token = participant.json()["access_token"]
        expect(participant.json()["user"]["role"] == "participant", "роль участника")

        duplicate = client.post(
            "/api/auth/register",
            json={
                "username": "Alice",
                "email": "other@example.com",
                "password": "secret123",
                "role": "participant",
            },
        )
        expect(duplicate.status_code == 400, "имя без учёта регистра занято")

        organizer = client.post(
            "/api/auth/register",
            json={
                "username": "bob",
                "email": "bob@example.com",
                "password": "secret123",
                "role": "organizer",
            },
        )
        expect(organizer.status_code == 200, "регистрация организатора")
        organizer_token = organizer.json()["access_token"]

        bad_login = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "wrongpass"})
        expect(bad_login.status_code == 401, "неверный пароль")
        login = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "secret123"})
        expect(login.status_code == 200, "вход")
        participant_token = login.json()["access_token"]
        me = client.get("/api/auth/me", headers=auth(participant_token))
        expect(me.status_code == 200 and me.json()["username"] == "alice", "текущий пользователь")
        expect(client.get("/api/auth/me").status_code == 401, "закрытый маршрут без токена")

        db = SessionLocal()
        try:
            stored = db.query(User).filter(User.email == "alice@example.com").one()
            expect(stored.password_hash != "secret123" and "$" in stored.password_hash, "пароль хранится как хеш")
        finally:
            db.close()

        problems = client.get("/api/problems").json()
        expect(len(problems) == 9, "в каталоге 9 задач из базы")
        found = client.get("/api/problems", params={"search": "фибоначчи"}).json()
        expect(len(found) == 1 and found[0]["title"] == "Число Фибоначчи", "поиск по-русски")
        hard = client.get("/api/problems", params={"difficulty": "hard"}).json()
        expect(len(hard) == 2, "фильтр сложной сложности")

        first = client.get(f"/api/problems/{problems[0]['id']}").json()
        expect(first["statement"] and first["examples"], "у задачи есть условие и примеры")
        expect("1000000000" not in str(first), "скрытые тесты не отдаются клиенту")

        forbidden = client.post(
            "/api/contests",
            headers=auth(participant_token),
            json={
                "title": "Чужое соревнование",
                "description": "Не должно создаться",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "duration_minutes": 60,
                "problem_ids": [problems[0]["id"]],
            },
        )
        expect(forbidden.status_code == 403, "участник не создаёт соревнования")

        run = client.post(
            "/api/run",
            headers=auth(participant_token),
            json={"problem_id": problems[0]["id"], "language": "python", "source_code": SOLUTIONS["Сумма двух чисел"]},
        )
        expect(run.status_code == 200 and run.json()["verdict"] == "OK", "запуск примеров")
        expect(run.json()["samples_only"] is True, "запуск проверяет только примеры")
        expect("Демонстрационный" in run.json()["message"], "результат запуска помечен как демонстрационный")
        expect(client.get("/api/submissions", headers=auth(participant_token)).json() == [], "запуск не сохраняется в историю")

        by_title = {item["title"]: item for item in problems}
        for title, source in SOLUTIONS.items():
            sent = client.post(
                "/api/submissions",
                headers=auth(participant_token),
                json={"problem_id": by_title[title]["id"], "language": "python", "source_code": source},
            )
            body = sent.json()
            expect(sent.status_code == 200 and body["verdict"] == "OK", f"решение «{title}» получило OK ({body.get('message')})")
            expect(body["judge_mode"] == "demo", f"проверка «{title}» в демонстрационном режиме")

        wrong = client.post(
            "/api/submissions",
            headers=auth(participant_token),
            json={"problem_id": problems[0]["id"], "language": "python", "source_code": "print(0)\n"},
        )
        expect(wrong.status_code == 200 and wrong.json()["verdict"] == "WA", "неверный ответ получает WA")
        expect(wrong.json()["failed_expected"] is not None, "для WA есть ожидаемый ответ")

        broken = client.post(
            "/api/submissions",
            headers=auth(participant_token),
            json={"problem_id": problems[0]["id"], "language": "python", "source_code": "def (\n"},
        )
        expect(broken.status_code == 200 and broken.json()["verdict"] == "CE", "синтаксическая ошибка получает CE")

        looping = client.post(
            "/api/submissions",
            headers=auth(participant_token),
            json={"problem_id": problems[0]["id"], "language": "python", "source_code": "while True:\n    pass\n"},
        )
        expect(looping.status_code == 200 and looping.json()["verdict"] == "TLE", "бесконечный цикл получает TLE")

        history = client.get("/api/submissions", headers=auth(participant_token), params={"problem_id": problems[0]["id"]}).json()
        expect(len(history) >= 3, "история отправок сохраняется")
        detail = client.get(f"/api/submissions/{history[0]['id']}", headers=auth(participant_token)).json()
        expect(bool(detail["source_code"]), "можно открыть код отправки")

        dashboard = client.get("/api/dashboard", headers=auth(participant_token)).json()
        expect(dashboard["solved_count"] == 9, "на главной считаются решённые задачи")
        expect(dashboard["recent_submissions"], "на главной есть последние результаты")

        later = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        created = client.post(
            "/api/contests",
            headers=auth(organizer_token),
            json={
                "title": "Вечерний тур",
                "description": "Короткий тур для проверки платформы.",
                "start_time": later,
                "duration_minutes": 90,
                "problem_ids": [problems[0]["id"], problems[1]["id"]],
            },
        )
        expect(created.status_code == 200 and created.json()["phase"] == "draft", "организатор создаёт черновик")
        contest_id = created.json()["id"]
        expect(client.get("/api/contests").json() == [], "черновик скрыт от гостей")
        edited = client.put(
            f"/api/contests/{contest_id}",
            headers=auth(organizer_token),
            json={
                "title": "Вечерний турнир",
                "description": "Обновлённое описание.",
                "start_time": later,
                "duration_minutes": 90,
                "problem_ids": [problems[0]["id"], problems[1]["id"]],
            },
        )
        expect(edited.status_code == 200 and edited.json()["title"] == "Вечерний турнир", "организатор редактирует черновик")
        published = client.post(f"/api/contests/{contest_id}/publish", headers=auth(organizer_token))
        expect(published.status_code == 200 and published.json()["phase"] == "upcoming", "публикация будущего турнира")

        registered = client.post(f"/api/contests/{contest_id}/register", headers=auth(participant_token))
        expect(registered.status_code == 200 and registered.json()["is_registered"] is True, "регистрация на турнир")
        cancelled = client.delete(f"/api/contests/{contest_id}/register", headers=auth(participant_token))
        expect(cancelled.status_code == 200 and cancelled.json()["is_registered"] is False, "отмена регистрации до старта")
        client.post(f"/api/contests/{contest_id}/register", headers=auth(participant_token))
        early = client.post(
            "/api/submissions",
            headers=auth(participant_token),
            json={
                "problem_id": problems[0]["id"],
                "language": "python",
                "source_code": SOLUTIONS["Сумма двух чисел"],
                "contest_id": contest_id,
            },
        )
        expect(early.status_code == 403, "нельзя сдавать задачу до старта")

        started = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        live = client.post(
            "/api/contests",
            headers=auth(organizer_token),
            json={
                "title": "Идущий турнир",
                "description": "Турнир, который уже начался.",
                "start_time": started,
                "duration_minutes": 120,
                "problem_ids": [problems[0]["id"], problems[2]["id"]],
            },
        )
        live_id = live.json()["id"]
        client.post(f"/api/contests/{live_id}/publish", headers=auth(organizer_token))
        live_view = client.get(f"/api/contests/{live_id}").json()
        expect(live_view["phase"] == "running", "опубликованный турнир со стартом в прошлом идёт")
        expect(len(live_view["problems"]) == 2, "в турнире две задачи")

        locked = client.put(
            f"/api/contests/{live_id}",
            headers=auth(organizer_token),
            json={
                "title": "Попытка изменить",
                "description": "Уже нельзя",
                "start_time": started,
                "duration_minutes": 120,
                "problem_ids": [problems[0]["id"]],
            },
        )
        expect(locked.status_code == 400, "идущий турнир нельзя редактировать")

        second = client.post(
            "/api/auth/register",
            json={"username": "cara", "email": "cara@example.com", "password": "secret123", "role": "participant"},
        )
        cara = second.json()["access_token"]
        expect(client.post(f"/api/contests/{live_id}/register", headers=auth(participant_token)).status_code == 200, "alice в турнире")
        expect(client.post(f"/api/contests/{live_id}/register", headers=auth(cara)).status_code == 200, "cara в турнире")
        expect(
            client.delete(f"/api/contests/{live_id}/register", headers=auth(participant_token)).status_code == 400,
            "после старта регистрацию не отменить",
        )

        alice_ok = client.post(
            "/api/submissions",
            headers=auth(participant_token),
            json={
                "problem_id": problems[0]["id"],
                "contest_id": live_id,
                "language": "python",
                "source_code": SOLUTIONS["Сумма двух чисел"],
            },
        )
        expect(alice_ok.json()["verdict"] == "OK" and alice_ok.json()["contest_id"] == live_id, "зачётная отправка в турнире")
        cara_ok = client.post(
            "/api/submissions",
            headers=auth(cara),
            json={
                "problem_id": problems[0]["id"],
                "contest_id": live_id,
                "language": "python",
                "source_code": SOLUTIONS["Сумма двух чисел"],
            },
        )
        expect(cara_ok.json()["verdict"] == "OK", "вторая участница тоже решила задачу")
        alice_second = client.post(
            "/api/submissions",
            headers=auth(participant_token),
            json={
                "problem_id": problems[2]["id"],
                "contest_id": live_id,
                "language": "python",
                "source_code": SOLUTIONS["Сумма последовательности"],
            },
        )
        expect(alice_second.json()["verdict"] == "OK", "alice решила вторую задачу турнира")

        table = client.get(f"/api/contests/{live_id}/standings").json()
        expect(len(table) == 2, "в таблице оба участника")
        expect(table[0]["username"] == "alice" and table[0]["solved"] == 2 and table[0]["place"] == 1, "лидер по числу задач")
        expect(table[1]["username"] == "cara" and table[1]["solved"] == 1 and table[1]["place"] == 2, "второе место")
        expect(table[0]["time_seconds"] >= 0, "время посчитано")

        ended = client.post(
            "/api/contests",
            headers=auth(organizer_token),
            json={
                "title": "Прошедший турнир",
                "description": "Уже закончился.",
                "start_time": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
                "duration_minutes": 30,
                "problem_ids": [problems[0]["id"]],
            },
        )
        ended_id = ended.json()["id"]
        client.post(f"/api/contests/{ended_id}/publish", headers=auth(organizer_token))
        closed = client.post(f"/api/contests/{ended_id}/register", headers=auth(participant_token))
        expect(closed.status_code == 400, "на завершённый турнир нельзя зарегистрироваться")
        expect(client.get(f"/api/contests/{ended_id}").json()["phase"] == "finished", "статус завершённого турнира")

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
