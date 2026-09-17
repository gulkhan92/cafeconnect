import { useEffect } from "react";
import { Route, Routes } from "react-router-dom";

import { Layout } from "./components/layout/Layout";
import { RequireAuth, RequireStaff } from "./components/RouteGuards";
import { About } from "./pages/About";
import { BookTable } from "./pages/BookTable";
import { Cart } from "./pages/Cart";
import { Gallery } from "./pages/Gallery";
import { Home } from "./pages/Home";
import { PrivacyPolicy, TermsOfService } from "./pages/Legal";
import { Location } from "./pages/Location";
import { Login } from "./pages/Login";
import { Menu } from "./pages/Menu";
import { MyBookings } from "./pages/MyBookings";
import { MyOrders } from "./pages/MyOrders";
import { NotFound } from "./pages/NotFound";
import { Register } from "./pages/Register";
import { StaffDashboard } from "./pages/StaffDashboard";
import { useAuthStore } from "./store/auth";

export function App() {
  const hydrate = useAuthStore((state) => state.hydrate);

  useEffect(() => {
    hydrate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="menu" element={<Menu />} />
        <Route path="gallery" element={<Gallery />} />
        <Route path="about" element={<About />} />
        <Route path="location" element={<Location />} />
        <Route path="book-a-table" element={<BookTable />} />
        <Route path="cart" element={<Cart />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="privacy" element={<PrivacyPolicy />} />
        <Route path="terms" element={<TermsOfService />} />

        <Route
          path="account/bookings"
          element={
            <RequireAuth>
              <MyBookings />
            </RequireAuth>
          }
        />
        <Route
          path="account/orders"
          element={
            <RequireAuth>
              <MyOrders />
            </RequireAuth>
          }
        />
        <Route
          path="staff/dashboard"
          element={
            <RequireStaff>
              <StaffDashboard />
            </RequireStaff>
          }
        />

        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
