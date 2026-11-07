import type { ReactElement } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth";
import type { Role } from "../types";
import { LoadingBlock, Page } from "./ui";

export function RequireAuth({ role, children }: { role?: Role; children: ReactElement }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-4">
        <LoadingBlock />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (role && user.role !== role) {
    return (
      <Page title="Недостаточно прав" subtitle="Создавать соревнования может только организатор.">
        <p className="text-sm text-zinc-400">Войдите под учётной записью организатора или зарегистрируйте новую.</p>
      </Page>
    );
  }
  return children;
}
