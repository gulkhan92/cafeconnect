import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuthStore } from "../store/auth";
import { Spinner } from "./ui/Spinner";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, isHydrating } = useAuthStore();
  const location = useLocation();

  if (isHydrating) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner className="h-8 w-8 text-primary-600" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

export function RequireStaff({ children }: { children: ReactNode }) {
  const { user, isHydrating } = useAuthStore();

  if (isHydrating) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner className="h-8 w-8 text-primary-600" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== "staff_admin") {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
