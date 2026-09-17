import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Container } from "../components/ui/Container";
import { Section } from "../components/ui/Section";
import { Spinner } from "../components/ui/Spinner";
import { useCreateOrder } from "../hooks/useOrders";
import { extractErrorMessage } from "../lib/api";
import { useAuthStore } from "../store/auth";
import { useCartStore } from "../store/cart";

export function Cart() {
  const { lines, setQuantity, removeItem, clear, totalCents } = useCartStore();
  const { user } = useAuthStore();
  const createOrder = useCreateOrder();
  const navigate = useNavigate();
  const [placedOrderId, setPlacedOrderId] = useState<string | null>(null);

  const total = (totalCents() / 100).toFixed(2);

  function handleCheckout() {
    if (!user) {
      navigate("/login", { state: { from: { pathname: "/cart" } } });
      return;
    }

    createOrder.mutate(
      { items: lines.map((line) => ({ menu_item_id: line.menuItemId, quantity: line.quantity })) },
      {
        onSuccess: (order) => {
          setPlacedOrderId(order.id);
          clear();
        },
      },
    );
  }

  if (placedOrderId) {
    return (
      <Section>
        <Container className="max-w-lg text-center">
          <h1 className="text-3xl font-semibold text-cream-900">Order placed!</h1>
          <p className="mt-3 text-cream-700">
            Your order is confirmed and will be ready at the counter — pay when you pick it up. We'll update the
            status as it's prepared.
          </p>
          <Link
            to="/account/orders"
            className="mt-6 inline-block rounded-md bg-primary-600 px-5 py-2.5 text-sm font-medium text-cream-50 hover:bg-primary-700"
          >
            Track your order
          </Link>
        </Container>
      </Section>
    );
  }

  if (lines.length === 0) {
    return (
      <Section>
        <Container className="max-w-lg text-center">
          <h1 className="text-3xl font-semibold text-cream-900">Your cart is empty</h1>
          <p className="mt-3 text-cream-700">Add something from the menu to get started.</p>
          <Link
            to="/menu"
            className="mt-6 inline-block rounded-md bg-primary-600 px-5 py-2.5 text-sm font-medium text-cream-50 hover:bg-primary-700"
          >
            Browse the menu
          </Link>
        </Container>
      </Section>
    );
  }

  return (
    <Section>
      <Container className="max-w-2xl">
        <h1 className="text-3xl font-semibold text-cream-900">Your order</h1>

        <div className="mt-6 divide-y divide-cream-200 rounded-lg border border-cream-200">
          {lines.map((line) => (
            <div key={line.menuItemId} className="flex items-center justify-between gap-4 px-4 py-3.5">
              <div>
                <p className="font-medium text-cream-900">{line.name}</p>
                <p className="text-sm text-cream-600">${line.price} each</p>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min={1}
                  value={line.quantity}
                  onChange={(e) => setQuantity(line.menuItemId, Number(e.target.value) || 0)}
                  className="w-16 rounded-md border border-cream-300 px-2 py-1 text-center text-sm"
                  aria-label={`Quantity for ${line.name}`}
                />
                <button
                  onClick={() => removeItem(line.menuItemId)}
                  aria-label={`Remove ${line.name}`}
                  className="text-sm text-primary-600 hover:underline"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex items-center justify-between text-lg font-semibold text-cream-900">
          <span>Total</span>
          <span>${total}</span>
        </div>
        <p className="mt-1 text-sm text-cream-600">Pay at the counter or on pickup — no payment required online.</p>

        {createOrder.isError && <p className="mt-3 text-sm text-error">{extractErrorMessage(createOrder.error)}</p>}
        {!user && (
          <p className="mt-3 text-sm text-cream-600">
            <Link to="/login" className="font-medium text-primary-600 hover:underline">
              Log in
            </Link>{" "}
            to place this order.
          </p>
        )}

        <button
          onClick={handleCheckout}
          disabled={createOrder.isPending}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-md bg-primary-600 px-5 py-3 text-sm font-medium text-cream-50 hover:bg-primary-700 disabled:opacity-60"
        >
          {createOrder.isPending && <Spinner className="h-4 w-4" />}
          {user ? "Place order" : "Log in to order"}
        </button>
      </Container>
    </Section>
  );
}
