import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { ContestFormPage } from "./pages/ContestFormPage";
import { ContestPage } from "./pages/ContestPage";
import { ContestsPage } from "./pages/ContestsPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { ProblemsPage } from "./pages/ProblemsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { SolvePage } from "./pages/SolvePage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/problems" element={<ProblemsPage />} />
        <Route path="/problems/:problemId" element={<SolvePage />} />
        <Route path="/contests" element={<ContestsPage />} />
        <Route
          path="/contests/new"
          element={
            <RequireAuth role="organizer">
              <ContestFormPage />
            </RequireAuth>
          }
        />
        <Route path="/contests/:contestId" element={<ContestPage />} />
        <Route
          path="/contests/:contestId/edit"
          element={
            <RequireAuth role="organizer">
              <ContestFormPage />
            </RequireAuth>
          }
        />
        <Route path="/contests/:contestId/problems/:problemId" element={<SolvePage />} />
      </Route>
    </Routes>
  );
}
