import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import { PhaseBadge, VerdictBadge } from "../components/badges";
import { Alert, Button, EmptyState, LoadingBlock } from "../components/ui";
import { formatDate, formatDuration } from "../lib/format";
import type { Contest, Dashboard, Problem } from "../types";

export function HomePage() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingBlock />;
  return user ? <DashboardView /> : <Landing />;
}

function Landing() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [contests, setContests] = useState<Contest[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api<Problem[]>("/problems"), api<Contest[]>("/contests")])
      .then(([problemRows, contestRows]) => {
        setProblems(problemRows);
        setContests(contestRows);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить данные"));
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <div className="grid items-center gap-10 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <p className="text-sm font-medium text-violet-300">Платформа алгоритмических задач</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white sm:text-5xl">Решайте задачи. Участвуйте в соревнованиях.</h1>
          <p className="mt-4 max-w-xl text-zinc-400">
            CodeArena — место, где можно выбрать задачу, написать решение в редакторе и отправить его на проверку. Организаторы собирают турниры и смотрят таблицу результатов.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/register">
              <Button>Создать аккаунт</Button>
            </Link>
            <Link to="/problems">
              <Button variant="secondary">Каталог задач</Button>
            </Link>
          </div>
          <dl className="mt-8 flex gap-8 text-sm">
            <div>
              <dt className="text-zinc-500">Задач в базе</dt>
              <dd className="mt-1 text-2xl font-semibold text-white">{problems.length || "—"}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">Открытых турниров</dt>
              <dd className="mt-1 text-2xl font-semibold text-white">{contests.length || "—"}</dd>
            </div>
          </dl>
        </div>
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-3 text-xs text-zinc-500">
            <span>solution.py</span>
            <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 font-mono text-emerald-300">OK</span>
          </div>
          <pre className="overflow-x-auto p-4 font-mono text-sm leading-6 text-zinc-300">{`a, b = map(int, input().split())
print(a + b)`}</pre>
        </div>
      </div>
      {error && (
        <div className="mt-8">
          <Alert>{error}</Alert>
        </div>
      )}
      <div className="mt-12 grid gap-4 md:grid-cols-3">
        {[
          ["Каталог", "Задачи с условием, примерами и уровнем сложности."],
          ["Редактор", "Python, C++, Java и JavaScript в Monaco Editor."],
          ["Турниры", "Регистрация, решения и автоматическая таблица."],
        ].map(([title, text]) => (
          <div key={title} className="card p-4">
            <h2 className="font-medium">{title}</h2>
            <p className="mt-1 text-sm text-zinc-400">{text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function DashboardView() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Dashboard>("/dashboard")
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить главную"));
  }, []);

  if (error) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8">
        <Alert>{error}</Alert>
      </div>
    );
  }
  if (!data) return <LoadingBlock label="Загрузка главной..." />;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Здравствуйте, {data.username}</h1>
          <p className="mt-1 text-sm text-zinc-400">Продолжайте с задач или присоединяйтесь к турниру.</p>
        </div>
        <Link to="/problems">
          <Button>Перейти к задачам</Button>
        </Link>
      </div>
      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <Stat label="Решено задач" value={String(data.solved_count)} />
        <Stat label="Отправок" value={String(data.submission_count)} />
        <Stat label="Активных турниров" value={String(data.contests.length)} />
      </div>
      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-zinc-500">Соревнования</h2>
          {data.contests.length === 0 ? (
            <EmptyState title="Нет ближайших турниров" text="Когда организатор опубликует соревнование, оно появится здесь." />
          ) : (
            <div className="space-y-3">
              {data.contests.map((contest) => (
                <Link key={contest.id} to={`/contests/${contest.id}`} className="card block p-4 transition hover:border-violet-500/40">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-medium">{contest.title}</h3>
                    <PhaseBadge value={contest.phase} />
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm text-zinc-400">{contest.description}</p>
                  <p className="mt-3 text-xs text-zinc-500">
                    {contest.problem_count} задач · {formatDuration(contest.duration_minutes)} · {formatDate(contest.start_time)}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </section>
        <section>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-zinc-500">Последние результаты</h2>
          {data.recent_submissions.length === 0 ? (
            <EmptyState title="Пока нет отправок" text="Откройте задачу и отправьте первое решение." />
          ) : (
            <div className="card divide-y divide-white/5">
              {data.recent_submissions.map((submission) => (
                <Link key={submission.id} to={`/problems/${submission.problem_id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-white/[0.03]">
                  <VerdictBadge value={submission.verdict} />
                  <div className="min-w-0">
                    <p className="truncate text-sm">{submission.problem_title}</p>
                    <p className="text-xs text-zinc-500">
                      {submission.language} · {formatDate(submission.created_at)}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-4">
      <p className="text-sm text-zinc-400">{label}</p>
      <p className="mt-1 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}
