import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Container } from "../components/ui/Container";
import { Section } from "../components/ui/Section";
import { Spinner } from "../components/ui/Spinner";
import { extractErrorMessage } from "../lib/api";
import { useAuthStore } from "../store/auth";

export function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register, login } = useAuthStore();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(name, email, password);
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Could not create your account."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Section>
      <Container className="max-w-md">
        <h1 className="text-3xl font-semibold text-cream-900">Create an account</h1>
        <p className="mt-2 text-sm text-cream-600">
          Already have one?{" "}
          <Link to="/login" className="font-medium text-primary-600 hover:underline">
            Log in
          </Link>
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-cream-800">Name</span>
            <input
              required
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-md border border-cream-300 bg-cream-50 px-3 py-2.5 text-sm outline-none focus:border-primary-400"
            />
          </label>
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
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-cream-300 bg-cream-50 px-3 py-2.5 text-sm outline-none focus:border-primary-400"
            />
            <span className="mt-1 block text-xs text-cream-500">At least 8 characters.</span>
          </label>

          {error && <p className="text-sm text-error">{error}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-primary-600 px-5 py-2.5 text-sm font-medium text-cream-50 hover:bg-primary-700 disabled:opacity-60"
          >
            {isSubmitting && <Spinner className="h-4 w-4" />}
            Create account
          </button>
        </form>
      </Container>
    </Section>
  );
}
