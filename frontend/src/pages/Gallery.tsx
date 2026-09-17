import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

import { Container } from "../components/ui/Container";
import { Eyebrow, Section } from "../components/ui/Section";
import { galleryImages } from "../lib/images";

const CATEGORIES = ["All", "Interior", "Seating", "Coffee Bar", "Outdoor"] as const;

export function Gallery() {
  const [filter, setFilter] = useState<(typeof CATEGORIES)[number]>("All");
  const [lightbox, setLightbox] = useState<number | null>(null);

  const filtered =
    filter === "All" ? galleryImages : galleryImages.filter((image) => image.category === filter);

  return (
    <div>
      <Section className="bg-cream-100 pb-10">
        <Container>
          <Eyebrow>Ambience</Eyebrow>
          <h1 className="text-4xl font-semibold text-cream-900 sm:text-5xl">A look inside CafeConnect</h1>
          <p className="mt-3 max-w-xl text-cream-700">
            From the espresso bar to our sunniest window seat — here's what to expect when you visit.
          </p>

          <div className="mt-6 flex flex-wrap gap-2">
            {CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => setFilter(category)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  filter === category
                    ? "bg-primary-600 text-cream-50"
                    : "border border-cream-300 text-cream-700 hover:border-primary-400"
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </Container>
      </Section>

      <Section className="pt-10">
        <Container>
          <div className="columns-1 gap-4 sm:columns-2 lg:columns-3 [&>*]:mb-4">
            {filtered.map((image, index) => (
              <motion.button
                key={image.src + index}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.35, delay: (index % 6) * 0.05 }}
                onClick={() => setLightbox(index)}
                className="block w-full overflow-hidden rounded-lg shadow-soft"
              >
                <img
                  src={image.src}
                  alt={image.alt}
                  loading="lazy"
                  className="w-full object-cover transition-transform duration-300 hover:scale-105"
                />
              </motion.button>
            ))}
          </div>
        </Container>
      </Section>

      <AnimatePresence>
        {lightbox !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-cream-900/90 p-4"
            onClick={() => setLightbox(null)}
            role="dialog"
            aria-modal="true"
            aria-label={filtered[lightbox].alt}
          >
            <motion.img
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              src={filtered[lightbox].src}
              alt={filtered[lightbox].alt}
              className="max-h-[85vh] max-w-full rounded-lg object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              onClick={() => setLightbox(null)}
              aria-label="Close image"
              className="absolute top-5 right-5 text-2xl text-cream-50"
            >
              ✕
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
