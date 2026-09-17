// Real, license-clear Unsplash photography used as bootstrapping imagery
// during development, per the plan's Section 4.1 instructions. Replace every
// URL here with the cafe's own photography before production launch.
// Every id below has been visually verified to match its label/alt text.
function unsplash(id: string, width = 1600) {
  return `https://images.unsplash.com/${id}?auto=format&fit=crop&w=${width}&q=80`;
}

export const images = {
  heroInterior: unsplash("photo-1554118811-1e0d58224f24"), // sunlit cafe interior
  pourOverBrewing: unsplash("photo-1442512595331-e89e73853f31"), // kettle pouring into a pour-over brewer
  latteArt: unsplash("photo-1541167760496-1628856ab772"), // milk being poured into a latte
  breadLoaves: unsplash("photo-1509440159596-0249088772ff"), // artisan bread loaves
  seatingArea: unsplash("photo-1521017432531-fbd92d768814"), // cafe interior with tables and seating
  conservatorySeating: unsplash("photo-1445116572660-236099ec97a0"), // bright plant-filled table seating
  coffeeCheers: unsplash("photo-1495474472287-4d71bcdd2085"), // two people toasting coffee cups
  coffeeBeans: unsplash("photo-1447933601403-0c6688de566e"), // roasted coffee beans, close-up
  counter: unsplash("photo-1453614512568-c4024d13c247"), // espresso bar counter
  pastryTray: unsplash("photo-1483695028939-5bb13f8648b0"), // tray of croissants and pastries
};

export const galleryImages = [
  { src: images.heroInterior, alt: "Warm, sunlit interior seating area with wooden tables", category: "Interior" },
  { src: images.seatingArea, alt: "Cafe interior with wooden tables and soft lighting", category: "Seating" },
  { src: images.counter, alt: "The espresso bar and counter where orders are prepared", category: "Coffee Bar" },
  { src: images.pourOverBrewing, alt: "Hot water being poured over fresh grounds in a pour-over brewer", category: "Coffee Bar" },
  { src: images.latteArt, alt: "Steamed milk being poured to form latte art", category: "Coffee Bar" },
  { src: images.coffeeCheers, alt: "Two people toasting their coffee cups together", category: "Coffee Bar" },
  { src: images.conservatorySeating, alt: "Bright, plant-filled table seating near large windows", category: "Outdoor" },
  { src: images.breadLoaves, alt: "Freshly baked artisan bread loaves", category: "Interior" },
  { src: images.pastryTray, alt: "A tray of fresh croissants and pastries", category: "Interior" },
];
