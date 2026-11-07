import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { DifficultyBadge } from "../components/badges";
import { Alert, Button, LoadingBlock, Page, TextArea, TextField, cx } from "../components/ui";
import { toLocalInput } from "../lib/format";
import type { Contest, Problem } from "../types";

export function ContestFormPage() {
  const { contestId } = useParams();
  const editing = Boolean(contestId);
  const navigate = useNavigate();
  const [problems, setProblems] = useState<Problem[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [start, setStart] = useState("");
  const [duration, setDuration] = useState(120);
  const [selected, setSelected] = useState<number[]>([]);
  const [phase, setPhase] = useState<string>("draft");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const catalog = await api<Problem[]>("/problems");
        if (cancelled) return;
        setProblems(catalog);
        if (contestId) {
          const contest = await api<Contest>(`/contests/${contestId}`);
          if (cancelled) return;
          setTitle(contest.title);
          setDescription(contest.description);
          setStart(toLocalInput(contest.start_time));
          setDuration(contest.duration_minutes);
          setSelected(contest.problems.map((item) => item.problem_id));
          setPhase(contest.phase);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Не удалось открыть форму");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [contestId]);

  function toggle(id: number) {
    setSelected((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  async function save(publish: boolean) {
    setError("");
    if (!title.trim() || !description.trim() || !start) {
      setError("Заполните название, описание и дату начала.");
      return;
    }
    if (selected.length === 0) {
      setError("Выберите хотя бы одну задачу.");
      return;
    }
    setBusy(true);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim(),
        start_time: new Date(start).toISOString(),
        duration_minutes: duration,
        problem_ids: selected,
      };
      const contest = editing
        ? await api<Contest>(`/contests/${contestId}`, { method: "PUT", body: JSON.stringify(payload) })
        : await api<Contest>("/contests", { method: "POST", body: JSON.stringify(payload) });
      if (publish) {
        await api(`/contests/${contest.id}/publish`, { method: "POST" });
      }
      navigate(`/contests/${contest.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось сохранить соревнование");
    } finally {
      setBusy(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    save(false);
  }

  if (loading) return <LoadingBlock label="Загрузка формы..." />;

  const locked = phase === "running" || phase === "finished";
  const order = selected
    .map((id, index) => {
      const problem = problems.find((item) => item.id === id);
      return problem ? `${String.fromCharCode(65 + index)}. ${problem.title}` : "";
    })
    .filter(Boolean);

  return (
    <Page
      title={editing ? "Редактирование соревнования" : "Новое соревнование"}
      subtitle="Черновик виден только вам. После публикации участники смогут зарегистрироваться."
      actions={
        <Link to={editing ? `/contests/${contestId}` : "/contests"}>
          <Button variant="secondary">Назад</Button>
        </Link>
      }
    >
      {error && (
        <div className="mb-4">
          <Alert>{error}</Alert>
        </div>
      )}
      {locked ? (
        <Alert>Соревнование уже началось или завершилось, изменить его нельзя.</Alert>
      ) : (
        <form onSubmit={onSubmit} className="grid gap-4 lg:grid-cols-[1fr_1fr]">
          <div className="card space-y-4 p-5">
            <TextField label="Название" value={title} onChange={(event) => setTitle(event.target.value)} required minLength={3} maxLength={120} />
            <TextArea label="Описание" value={description} onChange={(event) => setDescription(event.target.value)} required />
            <TextField label="Дата начала" type="datetime-local" value={start} onChange={(event) => setStart(event.target.value)} required />
            <TextField
              label="Продолжительность, минуты"
              type="number"
              min={5}
              max={10080}
              value={duration}
              onChange={(event) => setDuration(Number(event.target.value))}
              required
            />
            <p className="text-xs text-zinc-500">Если указать время в прошлом, после публикации соревнование сразу получит статус «идёт» или «завершено».</p>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" variant="secondary" loading={busy}>
                {phase === "upcoming" ? "Сохранить изменения" : "Сохранить черновик"}
              </Button>
              {phase === "draft" && (
                <Button type="button" loading={busy} onClick={() => save(true)}>
                  Опубликовать
                </Button>
              )}
            </div>
          </div>
          <div className="card p-5">
            <h2 className="font-medium">Задачи</h2>
            <p className="mt-1 text-sm text-zinc-400">Порядок в турнире совпадает с порядком выбора.</p>
            {order.length > 0 && <p className="mt-3 text-sm text-zinc-300">{order.join(" · ")}</p>}
            <div className="mt-4 max-h-[460px] space-y-2 overflow-auto pr-1">
              {problems.map((problem) => {
                const checked = selected.includes(problem.id);
                return (
                  <label key={problem.id} className={cx("flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-2", checked ? "border-violet-500/50 bg-violet-500/10" : "border-white/10")}>
                    <input type="checkbox" className="mt-1" checked={checked} onChange={() => toggle(problem.id)} />
                    <span>
                      <span className="block text-sm">{problem.title}</span>
                      <span className="mt-1 inline-flex">
                        <DifficultyBadge value={problem.difficulty} />
                      </span>
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        </form>
      )}
    </Page>
  );
}
