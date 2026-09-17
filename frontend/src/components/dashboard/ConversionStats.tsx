import type { RangeParams } from "../../hooks/useAnalytics";
import { useConversion } from "../../hooks/useAnalytics";
import { Spinner } from "../ui/Spinner";

export function ConversionStats({ params }: { params: RangeParams }) {
  const { data, isLoading, isError } = useConversion(params);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-cream-600">
        <Spinner /> Loading conversion…
      </div>
    );
  }

  if (isError || !data) {
    return <p className="text-error">Couldn't load conversion data.</p>;
  }

  return (
    <div>
      <h3 className="mb-4 font-display text-lg font-semibold text-cream-900">Booking-to-order conversion</h3>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-sm text-cream-600">Total bookings</p>
          <p className="text-xl font-semibold text-cream-900">{data.total_bookings}</p>
        </div>
        <div>
          <p className="text-sm text-cream-600">Led to an order</p>
          <p className="text-xl font-semibold text-cream-900">
            {data.bookings_with_order} ({Math.round(data.conversion_rate * 100)}%)
          </p>
        </div>
        <div>
          <p className="text-sm text-cream-600">Via chatbot</p>
          <p className="text-xl font-semibold text-cream-900">{data.chatbot_bookings}</p>
        </div>
        <div>
          <p className="text-sm text-cream-600">Manual</p>
          <p className="text-xl font-semibold text-cream-900">{data.manual_bookings}</p>
        </div>
      </div>
    </div>
  );
}
