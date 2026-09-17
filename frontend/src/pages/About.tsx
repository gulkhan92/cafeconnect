import { motion } from "framer-motion";

import { Container } from "../components/ui/Container";
import { Eyebrow, Section } from "../components/ui/Section";
import { images } from "../lib/images";

const VALUES = [
  {
    title: "Sourced with intention",
    body: "Every bag of beans is traceable to the farm it came from. We rotate single-origin offerings seasonally and pay above fair-trade minimums.",
  },
  {
    title: "Baked daily, never shipped",
    body: "Our pastry case is refilled each morning by our in-house baker — nothing arrives frozen, and nothing sits more than a day.",
  },
  {
    title: "A table that's actually available",
    body: "We built our own booking system because we were tired of turning people away at the door. If it says available, it's available.",
  },
];

export function About() {
  return (
    <div>
      <Section className="bg-cream-100">
        <Container className="max-w-3xl text-center">
          <Eyebrow>Our story</Eyebrow>
          <h1 className="text-4xl font-semibold text-cream-900 sm:text-5xl">
            We missed our neighborhood cafe, so we built one.
          </h1>
          <p className="mt-5 text-lg text-cream-700">
            CafeConnect began in 2021 with one espresso machine, a folding table, and a promise: no burnt coffee,
            no mystery pastries, and no more standing in the doorway wondering if there's a seat for you.
          </p>
        </Container>
      </Section>

      <Section>
        <Container className="grid items-center gap-10 lg:grid-cols-2">
          <motion.img
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            src={images.counter}
            alt="The espresso counter where the team prepares every order"
            className="h-96 w-full rounded-lg object-cover shadow-medium"
          />
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <Eyebrow>From the founders</Eyebrow>
            <h2 className="text-3xl font-semibold text-cream-900">
              "We wanted a cafe that respected your time as much as your coffee."
            </h2>
            <p className="mt-4 text-cream-700">
              After years of working in cafes that ran on paper waitlists and phone-tag reservations, we set out
              to prove a small, independent shop could offer the same booking reliability as a big-city
              restaurant — without losing the warmth that made us love this business in the first place.
            </p>
            <p className="mt-4 text-cream-700">
              Today that shows up in small ways: a live seating chart instead of a guess, a menu that tells you
              exactly what's in season, and a team that still remembers your order.
            </p>
          </motion.div>
        </Container>
      </Section>

      <Section className="bg-secondary-800 text-cream-50">
        <Container>
          <Eyebrow>
            <span className="text-cream-200">What we stand for</span>
          </Eyebrow>
          <h2 className="max-w-xl text-3xl font-semibold sm:text-4xl">The values behind every cup</h2>
          <div className="mt-10 grid gap-8 sm:grid-cols-3">
            {VALUES.map((value, i) => (
              <motion.div
                key={value.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <h3 className="font-display text-xl font-semibold">{value.title}</h3>
                <p className="mt-2 text-sm text-cream-100/85">{value.body}</p>
              </motion.div>
            ))}
          </div>
        </Container>
      </Section>
    </div>
  );
}
