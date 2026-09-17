import { Container } from "../components/ui/Container";
import { Section } from "../components/ui/Section";
import { Spinner } from "../components/ui/Spinner";
import { useMyBookings } from "../hooks/useBookings";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-warning-bg text-warning",
  confirmed: "bg-success-bg text-success",
  cancelled: "bg-cream-200 text-cream-600",
};

export function MyBookings() {
  const { data: bookings, isLoading, isError } = useMyBookings(true);

  return (
    <Section>
      <Container className="max-w-2xl">
        <h1 className="text-3xl font-semibold text-cream-900">My bookings</h1>

        {isLoading && (
          <div className="mt-6 flex items-center gap-2 text-cream-600">
            <Spinner /> Loading your bookings…
          </div>
        )}
        {isError && <p className="mt-6 text-error">Couldn't load your bookings.</p>}
        {!isLoading && bookings?.length === 0 && (
          <p className="mt-6 text-cream-600">You don't have any bookings yet.</p>
        )}

        <div className="mt-6 space-y-3">
          {bookings?.map((booking) => (
            <div
              key={booking.id}
              className="flex items-center justify-between rounded-lg border border-cream-200 bg-cream-50 px-4 py-3.5"
            >
              <div>
                <p className="font-medium text-cream-900">Party of {booking.party_size}</p>
                <p className="text-sm text-cream-600">
                  Booked {new Date(booking.created_at).toLocaleDateString()} · via {booking.created_via}
                </p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${STATUS_STYLES[booking.status] ?? "bg-cream-200"}`}
              >
                {booking.status}
              </span>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
