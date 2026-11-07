const FIELD_NAMES: Record<string, string> = {
  username: "имя пользователя",
  email: "email",
  password: "пароль",
  role: "роль",
  title: "название",
  description: "описание",
  start_time: "дата начала",
  duration_minutes: "продолжительность",
  problem_ids: "список задач",
  source_code: "код",
  language: "язык",
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function messageFromBody(data: unknown): string {
  if (!data || typeof data !== "object" || !("detail" in data)) {
    return "Ошибка запроса";
  }
  const detail = (data as { detail: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { loc?: unknown[]; msg?: string };
    const field = Array.isArray(first.loc) ? first.loc.filter((part) => part !== "body").join(".") : "";
    const label = FIELD_NAMES[field] ?? field;
    if (label) return `Проверьте поле «${label}»`;
    return "Проверьте заполнение формы";
  }
  return "Ошибка запроса";
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = localStorage.getItem("token");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`/api${path}`, { ...options, headers });
  } catch {
    throw new ApiError(0, "Сервер недоступен. Запустите backend на порту 8000.");
  }

  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, messageFromBody(data));
  return data as T;
}
