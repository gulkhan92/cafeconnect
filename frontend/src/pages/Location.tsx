import { Container } from "../components/ui/Container";
import { Eyebrow, Section } from "../components/ui/Section";

const HOURS = [
  { day: "Monday – Friday", time: "9:00 AM – 10:00 PM" },
  { day: "Saturday – Sunday", time: "9:00 AM – 10:00 PM" },
];

export function Location() {
  return (
    <Section>
      <Container>
        <Eyebrow>Visit us</Eyebrow>
        <h1 className="text-4xl font-semibold text-cream-900 sm:text-5xl">Location &amp; hours</h1>

        <div className="mt-10 grid gap-10 lg:grid-cols-2">
          <div className="overflow-hidden rounded-lg shadow-medium">
            <iframe
              title="CafeConnect location map"
              src="https://maps.google.com/maps?q=coffee%20shop&t=&z=14&ie=UTF8&iwloc=&output=embed"
              className="h-96 w-full border-0"
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
            />
          </div>

          <div className="space-y-8">
            <div>
              <h2 className="text-lg font-semibold text-cream-900">Address</h2>
              <p className="mt-1 text-cream-700">
                128 Windmill Lane
                <br />
                Portside District
                <br />
                Open in Maps for directions
              </p>
            </div>

            <div>
              <h2 className="text-lg font-semibold text-cream-900">Hours</h2>
              <dl className="mt-2 divide-y divide-cream-200 rounded-md border border-cream-200">
                {HOURS.map((row) => (
                  <div key={row.day} className="flex justify-between px-4 py-2.5 text-sm">
                    <dt className="text-cream-700">{row.day}</dt>
                    <dd className="font-medium text-cream-900">{row.time}</dd>
                  </div>
                ))}
              </dl>
            </div>

            <div>
              <h2 className="text-lg font-semibold text-cream-900">Contact</h2>
              <p className="mt-1 text-cream-700">
                <a href="tel:+15551234567" className="hover:text-primary-600">
                  (555) 123-4567
                </a>
                <br />
                <a href="mailto:hello@cafeconnect.io" className="hover:text-primary-600">
                  hello@cafeconnect.io
                </a>
              </p>
            </div>

            <a
              href="https://maps.google.com/maps?q=coffee+shop"
              target="_blank"
              rel="noreferrer"
              className="inline-block rounded-md bg-primary-600 px-5 py-2.5 text-sm font-medium text-cream-50 hover:bg-primary-700"
            >
              Get directions
            </a>
          </div>
        </div>
      </Container>
    </Section>
  );
}
