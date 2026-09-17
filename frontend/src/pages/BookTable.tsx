import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Container } from "../components/ui/Container";
import { Eyebrow, Section } from "../components/ui/Section";
import { Spinner } from "../components/ui/Spinner";
import { useAvailability } from "../hooks/useAvailability";
import { useCreateBooking } from "../hooks/useBookings";
import { extractErrorMessage } from "../lib/api";
import { useAuthStore } from "../store/auth";
import type { TableAvailability } from "../types";

const AREAS = ["All areas", "window", "patio", "indoor"] as const;

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

interface SlotChip {
  slotId: string;
  time: string;
  tableId: string;
  tableNumber: string;
  locationTag: string | null;
}

function buildSlotChips(tables: TableAvailability[] | undefined, area: string): SlotChip[] {
  if (!tables) return [];
  const filtered = area === "All areas" ? tables : tables.filter((t) => t.location_tag === area);

  const chips: SlotChip[] = [];
  for (const table of filtered) {
    for (const slot of table.available_slots) {
      chips.push({
        slotId: slot.id,
        time: slot.start_time.slice(0, 5),
        tableId: table.id,
        tableNumber: table.table_number,
        locationTag: table.location_tag,
      });
    }
  }
  return chips.sort((a, b) => a.time.localeCompare(b.time));
}

export function BookTable() {
  const [date, setDate] = useState(todayIsoDate());
  const [partySize, setPartySize] = useState(2);
  const [area, setArea] = useState<(typeof AREAS)[number]>("All areas");
  const [selectedSlot, setSelectedSlot] = useState<SlotChip | null>(null);
  const [confirmation, setConfirmation] = useState<string | null>(null);

  const { user } = useAuthStore();
  const navigate = useNavigate();
  const availability = useAvailability(date, partySize, partySize > 0);
  const createBooking = useCreateBooking();

  const chips = useMemo(() => buildSlotChips(availability.data, area), [availability.data, area]);

  function handleBook() {
    if (!selectedSlot) return;
    if (!user) {
      navigate("/login", { state: { from: { pathname: "/book-a-table" } } });
      return;
    }

    createBooking.mutate(
      { slot_id: selectedSlot.slotId, party_size: partySize, created_via: "manual" },
      {
        onSuccess: () => {
          setConfirmation(
            `You're booked! Table ${selectedSlot.tableNumber} on ${date} at ${selectedSlot.time} for ${partySize} guests.`,
          );
          setSelectedSlot(null);
        },
      },
    );
  }

  return (
    <div>
      <Section className="bg-cream-100 pb-10">
        <Container>
          <Eyebrow>Reserve a table</Eyebrow>
          <h1 className="text-4xl font-semibold text-cream-900 sm:text-5xl">Book a table</h1>
          <p className="mt-3 max-w-xl text-cream-700">
            Pick a date and party size to see real-time availability — or use the chat assistant in the corner to
            book in natural language instead.
          </p>
        </Container>
      </Section>

      <Section className="pt-10">
        <Container className="max-w-3xl">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium text-cream-800">Date</span>
              <input
                type="date"
                min={todayIsoDate()}
                value={date}
                onChange={(e) => {
                  setDate(e.target.value);
                  setSelectedSlot(null);
                }}
                className="mt-1 w-full rounded-md border border-cream-300 bg-cream-50 px-3 py-2.5 text-sm outline-none focus:border-primary-400"
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-cream-800">Party size</span>
              <input
                type="number"
                min={1}
                max={20}
                value={partySize}
                onChange={(e) => {
                  setPartySize(Number(e.target.value) || 1);
                  setSelectedSlot(null);
                }}
                className="mt-1 w-full rounded-md border border-cream-300 bg-cream-50 px-3 py-2.5 text-sm outline-none focus:border-primary-400"
              />
            </label>
          </div>

          <div className="mt-5">
            <span className="text-sm font-medium text-cream-800">Area preference</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {AREAS.map((option) => (
                <button
                  key={option}
                  onClick={() => {
                    setArea(option);
                    setSelectedSlot(null);
                  }}
                  className={`rounded-full px-4 py-1.5 text-sm font-medium capitalize transition-colors ${
                    area === option
                      ? "bg-primary-600 text-cream-50"
                      : "border border-cream-300 text-cream-700 hover:border-primary-400"
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-8">
            <span className="text-sm font-medium text-cream-800">Available times</span>

            {availability.isLoading && (
              <div className="mt-3 flex items-center gap-2 text-cream-600">
                <Spinner /> Checking availability…
              </div>
            )}

            {availability.isError && (
              <p className="mt-3 text-error">Couldn't load availability — please try again.</p>
            )}

            {!availability.isLoading && chips.length === 0 && (
              <p className="mt-3 text-cream-600">
                No open tables for {partySize} guest{partySize === 1 ? "" : "s"} on {date}
                {area !== "All areas" ? ` in the ${area} area` : ""}. Try a different date or area.
              </p>
            )}

            <div className="mt-3 flex flex-wrap gap-2">
              {chips.map((chip) => (
                <button
                  key={chip.slotId}
                  onClick={() => setSelectedSlot(chip)}
                  className={`rounded-md border px-3.5 py-2 text-sm font-medium transition-colors ${
                    selectedSlot?.slotId === chip.slotId
                      ? "border-primary-600 bg-primary-600 text-cream-50"
                      : "border-cream-300 text-cream-800 hover:border-primary-400"
                  }`}
                >
                  {chip.time} · Table {chip.tableNumber}
                </button>
              ))}
            </div>
          </div>

          {selectedSlot && (
            <div className="mt-8 rounded-lg border border-cream-200 bg-cream-100 p-5">
              <p className="text-sm text-cream-800">
                Table {selectedSlot.tableNumber} · {date} at {selectedSlot.time} · {partySize} guest
                {partySize === 1 ? "" : "s"}
              </p>

              {!user && (
                <p className="mt-2 text-sm text-cream-600">
                  <Link to="/login" className="font-medium text-primary-600 hover:underline">
                    Log in
                  </Link>{" "}
                  to confirm this booking.
                </p>
              )}

              {createBooking.isError && (
                <p className="mt-2 text-sm text-error">{extractErrorMessage(createBooking.error)}</p>
              )}

              <button
                onClick={handleBook}
                disabled={createBooking.isPending}
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary-600 px-5 py-2.5 text-sm font-medium text-cream-50 hover:bg-primary-700 disabled:opacity-60"
              >
                {createBooking.isPending && <Spinner className="h-4 w-4" />}
                {user ? "Confirm booking" : "Log in to book"}
              </button>
            </div>
          )}

          {confirmation && (
            <div className="mt-6 rounded-lg bg-success-bg px-5 py-4 text-sm font-medium text-success">
              {confirmation}
            </div>
          )}
        </Container>
      </Section>
    </div>
  );
}
