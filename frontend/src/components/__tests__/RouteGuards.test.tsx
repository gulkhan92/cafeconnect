import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { useAuthStore } from "../../store/auth";
import { RequireAuth, RequireStaff } from "../RouteGuards";

function renderWithRoute(guardedElement: React.ReactNode, initialPath = "/protected") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/" element={<div>Home page</div>} />
        <Route path="/protected" element={guardedElement} />
      </Routes>
    </MemoryRouter>,
  );
}

const baseAuthState = {
  accessToken: null,
  refreshToken: null,
  user: null,
  isHydrating: false,
};

describe("RequireAuth", () => {
  afterEach(() => {
    useAuthStore.setState(baseAuthState);
  });

  it("redirects an unauthenticated visitor to /login", () => {
    useAuthStore.setState({ ...baseAuthState, user: null });
    renderWithRoute(
      <RequireAuth>
        <div>Secret content</div>
      </RequireAuth>,
    );
    expect(screen.getByText("Login page")).toBeInTheDocument();
    expect(screen.queryByText("Secret content")).not.toBeInTheDocument();
  });

  it("renders children for a logged-in customer", () => {
    useAuthStore.setState({
      ...baseAuthState,
      user: { id: "1", name: "A Customer", email: "a@example.com", role: "customer", phone: null },
    });
    renderWithRoute(
      <RequireAuth>
        <div>Secret content</div>
      </RequireAuth>,
    );
    expect(screen.getByText("Secret content")).toBeInTheDocument();
  });

  it("shows a spinner while auth is still hydrating, not the login redirect", () => {
    useAuthStore.setState({ ...baseAuthState, isHydrating: true });
    renderWithRoute(
      <RequireAuth>
        <div>Secret content</div>
      </RequireAuth>,
    );
    expect(screen.queryByText("Login page")).not.toBeInTheDocument();
    expect(screen.queryByText("Secret content")).not.toBeInTheDocument();
  });
});

describe("RequireStaff", () => {
  afterEach(() => {
    useAuthStore.setState(baseAuthState);
  });

  it("redirects an unauthenticated visitor to /login", () => {
    useAuthStore.setState({ ...baseAuthState, user: null });
    renderWithRoute(
      <RequireStaff>
        <div>Dashboard</div>
      </RequireStaff>,
    );
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("redirects a logged-in customer (wrong role) to home, not the dashboard", () => {
    useAuthStore.setState({
      ...baseAuthState,
      user: { id: "1", name: "A Customer", email: "a@example.com", role: "customer", phone: null },
    });
    renderWithRoute(
      <RequireStaff>
        <div>Dashboard</div>
      </RequireStaff>,
    );
    expect(screen.getByText("Home page")).toBeInTheDocument();
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });

  it("renders children for a logged-in staff_admin", () => {
    useAuthStore.setState({
      ...baseAuthState,
      user: { id: "2", name: "Staff Member", email: "staff@example.com", role: "staff_admin", phone: null },
    });
    renderWithRoute(
      <RequireStaff>
        <div>Dashboard</div>
      </RequireStaff>,
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });
});
