import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../../lib/api";
import { useAuthStore } from "../../store/auth";
import { renderWithProviders } from "../../test/testUtils";
import type { TableAvailability } from "../../types";
import { BookTable } from "../BookTable";

vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn() },
  };
});

const MOCK_AVAILABILITY: TableAvailability[] = [
  {
    id: "table-1",
    table_number: "T1",
    capacity: 4,
    location_tag: "window",
    available_slots: [{ id: "slot-1", date: "2026-01-01", start_time: "18:00:00", end_time: "18:30:00" }],
  },
  {
    id: "table-2",
    table_number: "T2",
    capacity: 4,
    location_tag: "patio",
    available_slots: [{ id: "slot-2", date: "2026-01-01", start_time: "19:00:00", end_time: "19:30:00" }],
  },
];

const CUSTOMER = { id: "u1", name: "Test Customer", email: "customer@example.com", role: "customer" as const, phone: null };

describe("Book a table flow", () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, isHydrating: false });
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({ data: MOCK_AVAILABILITY });
  });

  it("fetches availability for the default date and party size on mount", async () => {
    renderWithProviders(<BookTable />);

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith(
        "/tables/availability",
        expect.objectContaining({ params: expect.objectContaining({ party_size: 2 }) }),
      ),
    );

    expect(await screen.findByText(/18:00 · Table T1/)).toBeInTheDocument();
    expect(screen.getByText(/19:00 · Table T2/)).toBeInTheDocument();
  });

  it("filters slot chips by area preference", async () => {
    renderWithProviders(<BookTable />);
    await screen.findByText(/18:00 · Table T1/);

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "patio" }));

    expect(screen.queryByText(/18:00 · Table T1/)).not.toBeInTheDocument();
    expect(screen.getByText(/19:00 · Table T2/)).toBeInTheDocument();
  });

  it("prompts login instead of booking when the visitor is not authenticated", async () => {
    renderWithProviders(<BookTable />);
    const slotChip = await screen.findByText(/18:00 · Table T1/);

    const user = userEvent.setup();
    await user.click(slotChip);

    expect(screen.getByRole("button", { name: /log in to book/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /log in to book/i }));
    expect(api.post).not.toHaveBeenCalled();
  });

  it("creates a real booking via the API when a logged-in customer confirms", async () => {
    useAuthStore.setState({ accessToken: "fake-token", refreshToken: "fake-refresh", user: CUSTOMER, isHydrating: false });
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { id: "booking-1", status: "pending", slot_id: "slot-1" },
    });

    renderWithProviders(<BookTable />);
    const slotChip = await screen.findByText(/18:00 · Table T1/);

    const user = userEvent.setup();
    await user.click(slotChip);
    await user.click(screen.getByRole("button", { name: /confirm booking/i }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith("/bookings", {
        slot_id: "slot-1",
        party_size: 2,
        created_via: "manual",
      }),
    );

    expect(await screen.findByText(/you're booked!/i)).toBeInTheDocument();
  });

  it("shows the API error message when booking fails (e.g. slot taken concurrently)", async () => {
    useAuthStore.setState({ accessToken: "fake-token", refreshToken: "fake-refresh", user: CUSTOMER, isHydrating: false });
    vi.mocked(api.post).mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { detail: "This slot is already booked" } },
    });

    renderWithProviders(<BookTable />);
    const slotChip = await screen.findByText(/18:00 · Table T1/);

    const user = userEvent.setup();
    await user.click(slotChip);
    await user.click(screen.getByRole("button", { name: /confirm booking/i }));

    expect(await screen.findByText(/already booked/i)).toBeInTheDocument();
  });
});
