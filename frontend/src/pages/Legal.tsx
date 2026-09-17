import { Container } from "../components/ui/Container";
import { Section } from "../components/ui/Section";

export function PrivacyPolicy() {
  return (
    <Section>
      <Container className="max-w-2xl">
        <h1 className="text-3xl font-semibold text-cream-900">Privacy Policy</h1>
        <p className="mt-4 text-sm text-cream-600">
          This is placeholder legal copy for development. Replace with your reviewed privacy policy — covering
          what account, booking, and order data is collected, how it's stored, and how customers can request its
          deletion — before taking the site live.
        </p>
      </Container>
    </Section>
  );
}

export function TermsOfService() {
  return (
    <Section>
      <Container className="max-w-2xl">
        <h1 className="text-3xl font-semibold text-cream-900">Terms of Service</h1>
        <p className="mt-4 text-sm text-cream-600">
          This is placeholder legal copy for development. Replace with reviewed terms covering bookings,
          cancellations, and online ordering before taking the site live.
        </p>
      </Container>
    </Section>
  );
}
