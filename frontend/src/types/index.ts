export type UserRole = "customer" | "staff_admin";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  phone: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MenuItem {
  id: string;
  category_id: string;
  name: string;
  description: string | null;
  price: string;
  image_url: string | null;
  is_available: boolean;
}

export interface MenuCategory {
  id: string;
  name: string;
  display_order: number;
  items: MenuItem[];
}

export interface MenuSearchResult {
  item: MenuItem;
  score: number;
}

export interface TableSlot {
  id: string;
  date: string;
  start_time: string;
  end_time: string;
}

export interface TableAvailability {
  id: string;
  table_number: string;
  capacity: number;
  location_tag: string | null;
  available_slots: TableSlot[];
}

export type BookingStatus = "pending" | "confirmed" | "cancelled";
export type BookingSource = "chatbot" | "manual";

export interface Booking {
  id: string;
  user_id: string;
  table_id: string;
  slot_id: string;
  party_size: number;
  status: BookingStatus;
  created_via: BookingSource;
  created_at: string;
}

export type OrderStatus = "placed" | "preparing" | "ready" | "completed" | "cancelled";

export interface OrderItem {
  id: string;
  menu_item_id: string;
  quantity: number;
  unit_price_at_order_time: string;
}

export interface Order {
  id: string;
  user_id: string;
  booking_id: string | null;
  status: OrderStatus;
  total_amount: string;
  source: "seed_demo" | "live";
  created_at: string;
  items: OrderItem[];
}

export type AnalyticsRange = "today" | "week" | "month" | "custom";

export interface RevenuePoint {
  date: string;
  revenue: string;
  order_count: number;
}

export interface RevenueSummary {
  range_start: string;
  range_end: string;
  total_revenue: string;
  order_count: number;
  average_order_value: string;
  series: RevenuePoint[];
}

export interface TopItem {
  menu_item_id: string;
  name: string;
  quantity_sold: number;
  revenue: string;
}

export interface TopItemsResponse {
  range_start: string;
  range_end: string;
  by_quantity: TopItem[];
  by_revenue: TopItem[];
}

export interface TableUtilizationRow {
  table_id: string;
  table_number: string;
  total_slots: number;
  booked_slots: number;
  occupancy_rate: number;
}

export interface HourlyBookingCount {
  hour: number;
  booking_count: number;
}

export interface TableUtilizationResponse {
  range_start: string;
  range_end: string;
  tables: TableUtilizationRow[];
  peak_hours: HourlyBookingCount[];
}

export interface ConversionResponse {
  range_start: string;
  range_end: string;
  total_bookings: number;
  bookings_with_order: number;
  conversion_rate: number;
  chatbot_bookings: number;
  manual_bookings: number;
}

export interface DashboardSummary {
  today_revenue: string;
  today_bookings: number;
  active_orders: number;
}

export interface ChatMessageResponse {
  session_id: string;
  intent: string;
  reply: string;
  provider_used: string | null;
  data: Record<string, unknown> | null;
}

export interface ApiErrorBody {
  detail?: string | { msg: string }[];
}
