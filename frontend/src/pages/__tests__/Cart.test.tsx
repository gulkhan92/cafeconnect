import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../../lib/api";
import { useAuthStore } from "../../store/auth";
import { useCartStore } from "../../store/cart";
import { renderWithProviders } from "../../test/testUtils";
import { Cart } from "../Cart";

vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn() },
  };
});

const CUSTOMER = { id: "u1", name: "Test Customer", email: "customer@example.com", role: "customer" as const, phone: null };

describe("Cart / checkout flow", () => {
  beforeEach(() => {
    useCartStore.setState({ lines: [] });
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, isHydrating: false });
    vi.clearAllMocks();
  });

  afterEach(() => {
    useCartStore.setState({ lines: [] });
    useAuthStore.setState({ accessToken: null, refreshToken: null, user: null, isHydrating: false });
  });

  it("shows an empty-cart message with no items added", () => {
    renderWithProviders(<Cart />);
    expect(screen.getByText(/your cart is empty/i)).toBeInTheDocument();
  });

  it("lists cart lines and computes the total", () => {
    useCartStore.setState({
      lines: [
        { menuItemId: "m1", name: "Cappuccino", price: "4.50", quantity: 2 },
        { menuItemId: "m2", name: "Croissant", price: "3.75", quantity: 1 },
      ],
    });
    renderWithProviders(<Cart />);
    expect(screen.getByText("Cappuccino")).toBeInTheDocument();
    expect(screen.getByText("Croissant")).toBeInTheDocument();
    expect(screen.getByText("$12.75")).toBeInTheDocument(); // 2*4.50 + 1*3.75
  });

  it("prompts an unauthenticated user to log in instead of placing the order", async () => {
    useCartStore.setState({ lines: [{ menuItemId: "m1", name: "Cappuccino", price: "4.50", quantity: 1 }] });
    renderWithProviders(<Cart />, { route: "/cart" });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /log in to order/i }));

    expect(api.post).not.toHaveBeenCalled();
  });

  it("places a real order via the API when checked out while logged in", async () => {
    useAuthStore.setState({ accessToken: "fake-token", refreshToken: "fake-refresh", user: CUSTOMER, isHydrating: false });
    useCartStore.setState({ lines: [{ menuItemId: "m1", name: "Cappuccino", price: "4.50", quantity: 2 }] });

    vi.mocked(api.post).mockResolvedValueOnce({
      data: { id: "order-123", status: "placed", items: [] },
    });

    renderWithProviders(<Cart />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /place order/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith("/orders", {
        items: [{ menu_item_id: "m1", quantity: 2 }],
      });
    });

    await waitFor(() => expect(screen.getByText(/order placed/i)).toBeInTheDocument());
    // The cart is cleared once the order succeeds.
    expect(useCartStore.getState().lines).toEqual([]);
  });

  it("shows an error message when the order API call fails", async () => {
    useAuthStore.setState({ accessToken: "fake-token", refreshToken: "fake-refresh", user: CUSTOMER, isHydrating: false });
    useCartStore.setState({ lines: [{ menuItemId: "m1", name: "Cappuccino", price: "4.50", quantity: 1 }] });

    vi.mocked(api.post).mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { detail: "Cappuccino is not currently available" } },
    });

    renderWithProviders(<Cart />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /place order/i }));

    await waitFor(() => expect(screen.getByText(/not currently available/i)).toBeInTheDocument());
  });
});
