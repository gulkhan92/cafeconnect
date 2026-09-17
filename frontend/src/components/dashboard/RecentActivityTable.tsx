import { useMemo, useState } from "react";

import { useAllBookings } from "../../hooks/useBookings";
import { useAllOrders } from "../../hooks/useOrders";
import { Spinner } from "../ui/Spinner";
import type { RangeParams } from "../../hooks/useAnalytics";

type SortDirection = "asc" | "desc";

function SortHeader<T extends string>({
  label,
  column,
  active,
  direction,
  onClick,
}: {
  label: string;
  column: T;
  active: boolean;
  direction: SortDirection;
  onClick: (column: T) => void;
}) {
  return (
    <th
      onClick={() => onClick(column)}
      className="cursor-pointer px-3 py-2 text-left font-medium text-cream-600 select-none hover:text-cream-900"
    >
      {label} {active ? (direction === "asc" ? "↑" : "↓") : ""}
    </th>
  );
}

const ORDER_STATUS_STYLES: Record<string, string> = {
  placed: "bg-warning-bg text-warning",
  preparing: "bg-warning-bg text-warning",
  ready: "bg-success-bg text-success",
  completed: "bg-cream-200 text-cream-600",
  cancelled: "bg-error-bg text-error",
};

const BOOKING_STATUS_STYLES: Record<string, string> = {
  pending: "bg-warning-bg text-warning",
  confirmed: "bg-success-bg text-success",
  cancelled: "bg-cream-200 text-cream-600",
};

function StatusBadge({ status, styles }: { status: string; styles: Record<string, string> }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${styles[status] ?? "bg-cream-200"}`}>
      {status}
    </span>
  );
}

export function RecentActivityTable({ params }: { params: RangeParams }) {
  const [tab, setTab] = useState<"orders" | "bookings">("orders");
  const [sortColumn, setSortColumn] = useState("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const ordersQuery = useAllOrders(
    { date_from: params.range === "custom" ? params.start : undefined, date_to: params.range === "custom" ? params.end : undefined },
    tab === "orders",
  );
  const bookingsQuery = useAllBookings(tab === "bookings");

  function toggleSort(column: string) {
    if (column === sortColumn) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortColumn(column);
      setSortDirection("desc");
    }
  }

  const sortedOrders = useMemo(() => {
    const rows = [...(ordersQuery.data ?? [])];
    rows.sort((a, b) => {
      let cmp = 0;
      if (sortColumn === "created_at") cmp = a.created_at.localeCompare(b.created_at);
      else if (sortColumn === "total_amount") cmp = Number(a.total_amount) - Number(b.total_amount);
      else if (sortColumn === "status") cmp = a.status.localeCompare(b.status);
      return sortDirection === "asc" ? cmp : -cmp;
    });
    return rows.slice(0, 20);
  }, [ordersQuery.data, sortColumn, sortDirection]);

  const sortedBookings = useMemo(() => {
    const rows = [...(bookingsQuery.data ?? [])];
    rows.sort((a, b) => {
      let cmp = 0;
      if (sortColumn === "created_at") cmp = a.created_at.localeCompare(b.created_at);
      else if (sortColumn === "status") cmp = a.status.localeCompare(b.status);
      else if (sortColumn === "party_size") cmp = a.party_size - b.party_size;
      return sortDirection === "asc" ? cmp : -cmp;
    });
    return rows.slice(0, 20);
  }, [bookingsQuery.data, sortColumn, sortDirection]);

  const isLoading = tab === "orders" ? ordersQuery.isLoading : bookingsQuery.isLoading;
  const isError = tab === "orders" ? ordersQuery.isError : bookingsQuery.isError;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-display text-lg font-semibold text-cream-900">Recent activity</h3>
        <div className="flex gap-1 rounded-md border border-cream-300 p-1">
          {(["orders", "bookings"] as const).map((option) => (
            <button
              key={option}
              onClick={() => {
                setTab(option);
                setSortColumn("created_at");
                setSortDirection("desc");
              }}
              className={`rounded px-3 py-1 text-xs font-medium capitalize transition-colors ${
                tab === option ? "bg-primary-600 text-cream-50" : "text-cream-700 hover:bg-cream-100"
              }`}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 text-cream-600">
          <Spinner /> Loading…
        </div>
      )}
      {isError && <p className="text-error">Couldn't load recent activity.</p>}

      {!isLoading && !isError && tab === "orders" && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-cream-200">
                <SortHeader label="Date" column="created_at" active={sortColumn === "created_at"} direction={sortDirection} onClick={toggleSort} />
                <SortHeader label="Status" column="status" active={sortColumn === "status"} direction={sortDirection} onClick={toggleSort} />
                <SortHeader label="Total" column="total_amount" active={sortColumn === "total_amount"} direction={sortDirection} onClick={toggleSort} />
                <th className="px-3 py-2 text-left font-medium text-cream-600">Items</th>
              </tr>
            </thead>
            <tbody>
              {sortedOrders.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-cream-500">
                    No orders in this range.
                  </td>
                </tr>
              )}
              {sortedOrders.map((order) => (
                <tr key={order.id} className="border-b border-cream-100">
                  <td className="px-3 py-2 text-cream-700">{new Date(order.created_at).toLocaleString()}</td>
                  <td className="px-3 py-2">
                    <StatusBadge status={order.status} styles={ORDER_STATUS_STYLES} />
                  </td>
                  <td className="px-3 py-2 font-medium text-cream-900">${order.total_amount}</td>
                  <td className="px-3 py-2 text-cream-600">{order.items.length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!isLoading && !isError && tab === "bookings" && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-cream-200">
                <SortHeader label="Date" column="created_at" active={sortColumn === "created_at"} direction={sortDirection} onClick={toggleSort} />
                <SortHeader label="Status" column="status" active={sortColumn === "status"} direction={sortDirection} onClick={toggleSort} />
                <SortHeader label="Party size" column="party_size" active={sortColumn === "party_size"} direction={sortDirection} onClick={toggleSort} />
                <th className="px-3 py-2 text-left font-medium text-cream-600">Source</th>
              </tr>
            </thead>
            <tbody>
              {sortedBookings.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-cream-500">
                    No bookings yet.
                  </td>
                </tr>
              )}
              {sortedBookings.map((booking) => (
                <tr key={booking.id} className="border-b border-cream-100">
                  <td className="px-3 py-2 text-cream-700">{new Date(booking.created_at).toLocaleString()}</td>
                  <td className="px-3 py-2">
                    <StatusBadge status={booking.status} styles={BOOKING_STATUS_STYLES} />
                  </td>
                  <td className="px-3 py-2 text-cream-900">{booking.party_size}</td>
                  <td className="px-3 py-2 text-cream-600 capitalize">{booking.created_via}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-cream-500">
            Showing the most recent bookings across all dates — the bookings API doesn't yet support a date-range
            filter the way orders does.
          </p>
        </div>
      )}
    </div>
  );
}
