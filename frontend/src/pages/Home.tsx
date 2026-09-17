import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import { buttonClasses } from "../components/ui/Button";
import { Container } from "../components/ui/Container";
import { Eyebrow, Section } from "../components/ui/Section";
import { useMenu } from "../hooks/useMenu";
import { images } from "../lib/images";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" as const } },
};

export function Home() {
  return (
    <div>
      <Hero />
      <FeaturedMenu />
      <StoryTeaser />
      <VisitCta />
    </div>
  );
}

function Hero() {
  return (
    <section className="relative flex min-h-[88vh] items-center overflow-hidden">
      <img
        src={images.heroInterior}
        alt="Sunlit interior of CafeConnect with wooden tables and warm ambience"
        className="absolute inset-0 h-full w-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-cream-900/80 via-cream-900/40 to-cream-900/20" />

      <Container className="relative z-10">
        <motion.div initial="hidden" animate="show" variants={fadeUp} className="max-w-xl">
          <Eyebrow>
            <span className="text-cream-100">Neighborhood cafe &amp; roastery</span>
          </Eyebrow>
          <h1 className="text-4xl leading-tight font-semibold text-cream-50 sm:text-5xl lg:text-6xl">
            A warm seat, honest coffee, and a table that's always ready for you.
          </h1>
          <p className="mt-5 max-w-md text-base text-cream-100/90 sm:text-lg">
            CafeConnect pairs thoughtfully sourced coffee and fresh bakes with a booking experience that actually
            works — check availability, reserve a table, and order ahead, all in one place.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link to="/book-a-table" className={buttonClasses("primary", "lg")}>
              Book a table
            </Link>
            <Link
              to="/menu"
              className={buttonClasses(
                "outline",
                "lg",
                "border-cream-100 bg-cream-900/30 text-cream-50 backdrop-blur-sm hover:bg-cream-900/50",
              )}
            >
              Order online
            </Link>
          </div>
        </motion.div>
      </Container>
    </section>
  );
}

function FeaturedMenu() {
  const { data: categories, isLoading } = useMenu();
  const featured = categories?.flatMap((c) => c.items).slice(0, 3) ?? [];

  return (
    <Section>
      <Container>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="mb-10 flex items-end justify-between"
        >
          <div>
            <Eyebrow>From the menu</Eyebrow>
            <h2 className="text-3xl font-semibold text-cream-900 sm:text-4xl">A few current favorites</h2>
          </div>
          <Link to="/menu" className="hidden text-sm font-medium text-primary-600 hover:underline sm:block">
            View full menu →
          </Link>
        </motion.div>

        {isLoading && <p className="text-sm text-cream-600">Loading menu…</p>}
        {!isLoading && featured.length === 0 && (
          <p className="text-sm text-cream-600">
            Our menu is being freshly curated — check back soon, or explore the full{" "}
            <Link to="/menu" className="text-primary-600 underline">
              menu page
            </Link>
            .
          </p>
        )}

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {featured.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="rounded-lg border border-cream-200 bg-cream-50 p-5 shadow-soft"
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="font-display text-lg font-semibold text-cream-900">{item.name}</h3>
                <span className="shrink-0 font-medium text-primary-600">${item.price}</span>
              </div>
              {item.description && <p className="mt-2 text-sm text-cream-700">{item.description}</p>}
            </motion.div>
          ))}
        </div>
      </Container>
    </Section>
  );
}

function StoryTeaser() {
  return (
    <Section className="bg-cream-100">
      <Container className="grid items-center gap-10 lg:grid-cols-2">
        <motion.img
          initial={{ opacity: 0, scale: 0.97 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          src={images.coffeeCheers}
          alt="Two people toasting their coffee cups together"
          className="h-80 w-full rounded-lg object-cover shadow-medium"
        />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <Eyebrow>Our story</Eyebrow>
          <h2 className="text-3xl font-semibold text-cream-900 sm:text-4xl">
            Built by people who missed their neighborhood cafe.
          </h2>
          <p className="mt-4 text-cream-700">
            CafeConnect started as a single espresso machine and a handful of regulars. Today it's a full menu,
            a real booking system, and the same care in every cup — read the whole story.
          </p>
          <Link to="/about" className="mt-5 inline-block text-sm font-semibold text-primary-600 hover:underline">
            Read our story →
          </Link>
        </motion.div>
      </Container>
    </Section>
  );
}

function VisitCta() {
  return (
    <Section>
      <Container>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center rounded-xl bg-secondary-700 px-6 py-14 text-center text-cream-50"
        >
          <h2 className="text-3xl font-semibold sm:text-4xl">Come sit with us.</h2>
          <p className="mt-3 max-w-lg text-cream-100/90">
            Check live table availability or chat with our assistant to find the perfect time.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-4">
            <Link
              to="/book-a-table"
              className={buttonClasses("secondary", "lg", "bg-cream-50 text-secondary-800 hover:bg-cream-100")}
            >
              Check availability
            </Link>
            <Link
              to="/location"
              className={buttonClasses("outline", "lg", "border-cream-100 text-cream-50 hover:bg-cream-50/10")}
            >
              Get directions
            </Link>
          </div>
        </motion.div>
      </Container>
    </Section>
  );
}
