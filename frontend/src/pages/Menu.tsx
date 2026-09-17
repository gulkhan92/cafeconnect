import { motion } from "framer-motion";
import { useState } from "react";

import { Container } from "../components/ui/Container";
import { Eyebrow, Section } from "../components/ui/Section";
import { Spinner } from "../components/ui/Spinner";
import { useMenu, useMenuSearch } from "../hooks/useMenu";
import { images } from "../lib/images";
import { useCartStore } from "../store/cart";
import type { MenuItem } from "../types";

const FALLBACK_IMAGES = [images.breadLoaves, images.counter, images.coffeeBeans, images.pastryTray];

function fallbackImageFor(itemId: string) {
  let hash = 0;
  for (const char of itemId) hash = (hash * 31 + char.charCodeAt(0)) % FALLBACK_IMAGES.length;
  return FALLBACK_IMAGES[hash];
}

export function Menu() {
  const [query, setQuery] = useState("");
  const { data: categories, isLoading, isError } = useMenu();
  const searchQuery = useMenuSearch(query);
  const isSearching = query.trim().length > 1;

  return (
    <div>
      <Section className="bg-cream-100 pb-10">
        <Container>
          <Eyebrow>The menu</Eyebrow>
          <h1 className="text-4xl font-semibold text-cream-900 sm:text-5xl">What we're pouring today</h1>
          <p className="mt-3 max-w-xl text-cream-700">
            Browse by category, or describe what you're craving — try "something warm and spiced."
          </p>

          <div className="relative mt-6 max-w-lg">
            <SearchIcon className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-cream-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search the menu…"
              aria-label="Search the menu"
              className="w-full rounded-md border border-cream-300 bg-cream-50 py-3 pr-4 pl-10 text-sm outline-none focus:border-primary-400"
            />
          </div>
        </Container>
      </Section>

      <Section className="pt-10">
        <Container>
          {isSearching ? (
            <SearchResults results={searchQuery.data} isLoading={searchQuery.isLoading} query={query} />
          ) : (
            <CategoryListing categories={categories} isLoading={isLoading} isError={isError} />
          )}
        </Container>
      </Section>
    </div>
  );
}

function SearchResults({
  results,
  isLoading,
  query,
}: {
  results: { item: MenuItem }[] | undefined;
  isLoading: boolean;
  query: string;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-cream-600">
        <Spinner /> Searching for "{query}"…
      </div>
    );
  }

  if (!results || results.length === 0) {
    return <p className="text-cream-600">No matches for "{query}" — try describing it differently.</p>;
  }

  return (
    <div>
      <p className="mb-6 text-sm text-cream-600">
        {results.length} match{results.length === 1 ? "" : "es"} for "{query}"
      </p>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {results.map(({ item }) => (
          <MenuItemCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

function CategoryListing({
  categories,
  isLoading,
  isError,
}: {
  categories: { id: string; name: string; items: MenuItem[] }[] | undefined;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-cream-600">
        <Spinner /> Loading the menu…
      </div>
    );
  }

  if (isError) {
    return <p className="text-error">We couldn't load the menu right now. Please refresh the page.</p>;
  }

  if (!categories || categories.every((c) => c.items.length === 0)) {
    return <p className="text-cream-600">Our menu is being freshly curated — check back very soon.</p>;
  }

  return (
    <div className="space-y-16">
      {categories
        .filter((category) => category.items.length > 0)
        .map((category) => (
          <div key={category.id}>
            <h2 className="mb-6 text-2xl font-semibold text-cream-900">{category.name}</h2>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {category.items.map((item) => (
                <MenuItemCard key={item.id} item={item} />
              ))}
            </div>
          </div>
        ))}
    </div>
  );
}

function MenuItemCard({ item }: { item: MenuItem }) {
  const addItem = useCartStore((state) => state.addItem);
  const [justAdded, setJustAdded] = useState(false);
  const imageSrc = item.image_url ?? fallbackImageFor(item.id);

  function handleAdd() {
    addItem(item, 1);
    setJustAdded(true);
    window.setTimeout(() => setJustAdded(false), 1400);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.35 }}
      className="flex flex-col overflow-hidden rounded-lg border border-cream-200 bg-cream-50 shadow-soft"
    >
      <img src={imageSrc} alt={item.name} className="h-40 w-full object-cover" loading="lazy" />
      <div className="flex flex-1 flex-col p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-display text-lg font-semibold text-cream-900">{item.name}</h3>
          <span className="shrink-0 font-medium text-primary-600">${item.price}</span>
        </div>
        {item.description && <p className="mt-1.5 flex-1 text-sm text-cream-700">{item.description}</p>}

        {!item.is_available ? (
          <span className="mt-3 inline-block w-fit rounded-full bg-cream-200 px-2.5 py-1 text-xs font-medium text-cream-600">
            Currently unavailable
          </span>
        ) : (
          <button
            onClick={handleAdd}
            className="mt-3 self-start rounded-md border border-primary-500 px-3 py-1.5 text-xs font-semibold text-primary-600 transition-colors hover:bg-primary-600 hover:text-cream-50"
          >
            {justAdded ? "Added ✓" : "Add to cart"}
          </button>
        )}
      </div>
    </motion.div>
  );
}

function SearchIcon({ className = "" }: { className?: string }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      aria-hidden
      className={className}
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.35-4.35" strokeLinecap="round" />
    </svg>
  );
}
