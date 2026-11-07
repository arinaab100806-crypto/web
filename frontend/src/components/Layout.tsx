import { useEffect, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { roleLabel } from "../lib/format";
import type { SystemInfo } from "../types";
import { cx } from "./ui";

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight text-white">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-violet-600 shadow-lg shadow-violet-950/50">
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 7L5 12l4 5M15 7l4 5-4 5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      CodeArena
    </Link>
  );
}

export function Layout() {
  const { user, logout } = useAuth();
  const [system, setSystem] = useState<SystemInfo | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    api<SystemInfo>("/system")
      .then((info) => {
        setSystem(info);
        setOffline(false);
      })
      .catch(() => setOffline(true));
  }, []);

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cx("rounded-lg px-3 py-1.5 text-sm transition", isActive ? "bg-white/10 text-white" : "text-zinc-400 hover:text-white");

  return (
    <div className="min-h-screen bg-[#09090b]">
      <header className="sticky top-0 z-30 border-b border-white/10 bg-[#09090b]/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-3 px-4 py-3">
          <Logo />
          <nav className="flex items-center gap-1">
            <NavLink to="/problems" className={linkClass}>
              Задачи
            </NavLink>
            <NavLink to="/contests" className={linkClass}>
              Соревнования
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-2">
            {user ? (
              <>
                <span className="hidden text-xs text-zinc-500 sm:inline">{roleLabel[user.role]}</span>
                <span className="rounded-lg bg-white/5 px-2.5 py-1 text-sm text-zinc-200">{user.username}</span>
                <button onClick={logout} className="rounded-lg px-3 py-1.5 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white">
                  Выйти
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="rounded-lg px-3 py-1.5 text-sm text-zinc-300 hover:text-white">
                  Войти
                </Link>
                <Link to="/register" className="rounded-lg bg-violet-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-violet-500">
                  Регистрация
                </Link>
              </>
            )}
          </div>
        </div>
      </header>
      {offline && (
        <div className="border-b border-red-500/20 bg-red-500/10 px-4 py-2 text-center text-sm text-red-200">
          Нет связи с сервером. Запустите backend командой uvicorn на порту 8000.
        </div>
      )}
      {system?.judge_mode === "demo" && (
        <div className="border-b border-amber-500/20 bg-amber-500/10 px-4 py-2 text-center text-sm text-amber-100">
          Демонстрационный режим проверки кода. Вердикты считаются локально по подготовленным тестам. Чтобы использовать Judge0, укажите JUDGE0_URL в backend/.env.
        </div>
      )}
      {system?.judge_mode === "judge0" && (
        <div className="border-b border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-center text-sm text-emerald-100">
          Проверка решений выполняется через Judge0.
        </div>
      )}
      <Outlet />
    </div>
  );
}
