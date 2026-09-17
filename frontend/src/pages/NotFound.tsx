import { Link } from "react-router-dom";

import { Container } from "../components/ui/Container";
import { Section } from "../components/ui/Section";

export function NotFound() {
  return (
    <Section>
      <Container className="max-w-lg text-center">
        <h1 className="text-4xl font-semibold text-cream-900">Page not found</h1>
        <p className="mt-3 text-cream-700">We couldn't find that page. Let's get you back on track.</p>
        <Link
          to="/"
          className="mt-6 inline-block rounded-md bg-primary-600 px-5 py-2.5 text-sm font-medium text-cream-50 hover:bg-primary-700"
        >
          Back to home
        </Link>
      </Container>
    </Section>
  );
}
