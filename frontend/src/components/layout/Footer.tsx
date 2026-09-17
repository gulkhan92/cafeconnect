import { useState } from "react";
import { Link } from "react-router-dom";

import { Container } from "../ui/Container";

export function Footer() {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  function handleSubscribe(e: React.FormEvent) {
    e.preventDefault();
    // Newsletter capture is intentionally a client-side stub for Phase 6:
    // the plan calls this "a simple email capture endpoint," which belongs
    // on the backend as its own small feature rather than being folded into
    // the auth/booking/order APIs already built. Swap this for a real POST
    // once that endpoint exists.
    setSubscribed(true);
    setEmail("");
  }

  return (
    <footer className="border-t border-cream-200 bg-cream-100">
      <Container className="grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="font-display text-lg font-semibold text-cream-900">CafeConnect</p>
          <p className="mt-3 max-w-xs text-sm text-cream-700">
            A neighborhood cafe serving thoughtfully sourced coffee, fresh bakes, and a warm seat by the window.
          </p>
          <div className="mt-4 flex gap-3">
            <SocialIcon href="https://instagram.com" label="Instagram">
              <InstagramIcon />
            </SocialIcon>
            <SocialIcon href="https://facebook.com" label="Facebook">
              <FacebookIcon />
            </SocialIcon>
            <SocialIcon href="https://twitter.com" label="Twitter / X">
              <TwitterIcon />
            </SocialIcon>
          </div>
        </div>

        <FooterLinks
          title="Explore"
          links={[
            { to: "/menu", label: "Menu" },
            { to: "/gallery", label: "Gallery" },
            { to: "/about", label: "Our Story" },
            { to: "/location", label: "Location & Hours" },
          ]}
        />

        <FooterLinks
          title="Visit"
          links={[
            { to: "/book-a-table", label: "Book a table" },
            { to: "/cart", label: "Order online" },
            { to: "/login", label: "Log in" },
          ]}
        />

        <div>
          <p className="text-sm font-semibold text-cream-900">Stay in the loop</p>
          <p className="mt-2 text-sm text-cream-700">New seasonal drinks, events, and cafe news.</p>
          {subscribed ? (
            <p className="mt-3 text-sm font-medium text-secondary-600">Thanks — you're on the list!</p>
          ) : (
            <form onSubmit={handleSubscribe} className="mt-3 flex gap-2">
              <label htmlFor="newsletter-email" className="sr-only">
                Email address
              </label>
              <input
                id="newsletter-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-md border border-cream-300 bg-cream-50 px-3 py-2 text-sm outline-none focus:border-primary-400"
              />
              <button
                type="submit"
                className="shrink-0 rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-cream-50 hover:bg-primary-700"
              >
                Join
              </button>
            </form>
          )}
        </div>
      </Container>

      <div className="border-t border-cream-200 py-6">
        <Container className="flex flex-col items-center justify-between gap-3 text-xs text-cream-600 sm:flex-row">
          <p>&copy; {new Date().getFullYear()} CafeConnect. All rights reserved.</p>
          <div className="flex gap-4">
            <Link to="/privacy" className="hover:text-cream-900">
              Privacy Policy
            </Link>
            <Link to="/terms" className="hover:text-cream-900">
              Terms of Service
            </Link>
          </div>
        </Container>
      </div>
    </footer>
  );
}

function FooterLinks({ title, links }: { title: string; links: { to: string; label: string }[] }) {
  return (
    <div>
      <p className="text-sm font-semibold text-cream-900">{title}</p>
      <ul className="mt-3 flex flex-col gap-2">
        {links.map((link) => (
          <li key={link.to}>
            <Link to={link.to} className="text-sm text-cream-700 hover:text-primary-600">
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SocialIcon({ href, label, children }: { href: string; label: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      aria-label={label}
      className="flex h-8 w-8 items-center justify-center rounded-full bg-cream-200 text-cream-700 transition-colors hover:bg-primary-600 hover:text-cream-50"
    >
      {children}
    </a>
  );
}

function InstagramIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="0.5" fill="currentColor" />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M14 9h3V6h-3a3 3 0 0 0-3 3v3H8v3h3v6h3v-6h3l1-3h-4V9a1 1 0 0 1 1-1z" strokeLinejoin="round" />
    </svg>
  );
}

function TwitterIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M4 4l16 16M20 4L4 20" strokeLinecap="round" />
    </svg>
  );
}
