import { Container } from "../components/ui/Container";
import { Section } from "../components/ui/Section";
import { Spinner } from "../components/ui/Spinner";
import { useMenu } from "../hooks/useMenu";
import { useMyOrders } from "../hooks/useOrders";

const STATUS_STYLES: Record<string, string> = {
  placed: "bg-warning-bg text-warning",
  preparing: "bg-warning-bg text-warning",
  ready: "bg-success-bg text-success",
  completed: "bg-cream-200 text-cream-600",
  cancelled: "bg-error-bg text-error",
};

export function MyOrders() {
  const { data: orders, isLoading, isError } = useMyOrders(true);
  const { data: categories } = useMenu();

  const itemNameById = new Map<string, string>();
  for (const category of categories ?? []) {
    for (const item of category.items) itemNameById.set(item.id, item.name);
  }

  return (
    <Section>
      <Container className="max-w-2xl">
        <h1 className="text-3xl font-semibold text-cream-900">My orders</h1>
        <p className="mt-1 text-sm text-cream-600">Status updates automatically while an order is active.</p>

        {isLoading && (
          <div className="mt-6 flex items-center gap-2 text-cream-600">
            <Spinner /> Loading your orders…
          </div>
        )}
        {isError && <p className="mt-6 text-error">Couldn't load your orders.</p>}
        {!isLoading && orders?.length === 0 && <p className="mt-6 text-cream-600">You haven't placed an order yet.</p>}

        <div className="mt-6 space-y-4">
          {orders?.map((order) => (
            <div key={order.id} className="rounded-lg border border-cream-200 bg-cream-50 p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-cream-600">{new Date(order.created_at).toLocaleString()}</p>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium capitalize ${STATUS_STYLES[order.status] ?? "bg-cream-200"}`}
                >
                  {order.status}
                </span>
              </div>
              <ul className="mt-3 space-y-1 text-sm text-cream-800">
                {order.items.map((item) => (
                  <li key={item.id} className="flex justify-between">
                    <span>
                      {item.quantity} × {itemNameById.get(item.menu_item_id) ?? "Menu item"}
                    </span>
                    <span>${(Number(item.unit_price_at_order_time) * item.quantity).toFixed(2)}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-2 flex justify-between border-t border-cream-200 pt-2 text-sm font-semibold text-cream-900">
                <span>Total</span>
                <span>${order.total_amount}</span>
              </div>
            </div>
          ))}
        </div>
      </Container>
    </Section>
  );
}
