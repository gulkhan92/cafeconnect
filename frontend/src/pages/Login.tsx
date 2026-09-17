import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Container } from "../components/ui/Container";
import { Section } from "../components/ui/Section";
import { Spinner } from "../components/ui/Spinner";
import { extractErrorMessage } from "../lib/api";
import { useAuthStore } from "../store/auth";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const user = await login(email, password);
      navigate(user.role === "staff_admin" ? "/staff/dashboard" : from, { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Incorrect email or password."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Section>
      <Container className="max-w-md">
        <h1 className="text-3xl font-semibold text-cream-900">Log in</h1>
        <p className="mt-2 text-sm text-cream-600">
          New here?{" "}
          <Link to="/register" className="font-medium text-primary-600 hover:underline">
            Create an account
          </Link>
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-cream-800">Email</span>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-cream-300 bg-cream-50 px-3 py-2.5 text-sm outline-none focus:border-primary-400"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-cream-800">Password</span>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-cream-300 bg-cream-50 px-3 py-2.5 text-sm outline-none focus:border-primary-400"
            />
          </label>

          {error && <p className="text-sm text-error">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-primary-600 px-5 py-2.5 text-sm font-medium text-cream-50 hover:bg-primary-700 disabled:opacity-60"
          >
            {isSubmitting && <Spinner className="h-4 w-4" />}
            Log in
          </button>
        </form>
      </Container>
    </Section>
  );
}
