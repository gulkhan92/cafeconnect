import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

import { useAuthStore } from "../../store/auth";
import { useCartStore } from "../../store/cart";
import { Button } from "../ui/Button";
import { Container } from "../ui/Container";

const NAV_LINKS = [
  { to: "/", label: "Home" },
  { to: "/menu", label: "Menu" },
  { to: "/gallery", label: "Gallery" },
  { to: "/about", label: "Our Story" },
  { to: "/location", label: "Location" },
];

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, logout } = useAuthStore();
  const cartCount = useCartStore((state) => state.totalCount());
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium transition-colors hover:text-primary-600 ${
      isActive ? "text-primary-600" : "text-cream-800"
    }`;

  return (
    <header className="sticky top-0 z-40 border-b border-cream-200 bg-cream-50/90 backdrop-blur-md">
      <Container className="flex h-18 items-center justify-between">
        <Link to="/" className="font-display text-xl font-semibold tracking-tight text-cream-900">
          CafeConnect
        </Link>

        <nav className="hidden items-center gap-8 md:flex" aria-label="Primary">
          {NAV_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} className={linkClass}>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <Link to="/cart" className="relative rounded-md p-2 text-cream-800 hover:bg-cream-200" aria-label="Cart">
            <CartIcon />
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4.5 w-4.5 items-center justify-center rounded-full bg-primary-600 text-[10px] font-semibold text-cream-50">
                {cartCount}
              </span>
            )}
          </Link>

          {user ? (
            <UserMenu name={user.name} role={user.role} onLogout={handleLogout} />
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-cream-800 hover:text-primary-600">
                Log in
              </Link>
              <Button size="sm" onClick={() => navigate("/book-a-table")}>
                Book a table
              </Button>
            </>
          )}
        </div>

        <button
          className="rounded-md p-2 text-cream-900 md:hidden"
          onClick={() => setMenuOpen((v) => !v)}
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
        >
          {menuOpen ? <CloseIcon /> : <MenuIcon />}
        </button>
      </Container>

      <AnimatePresence>
        {menuOpen && (
          <motion.nav
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-cream-200 bg-cream-50 md:hidden"
            aria-label="Mobile"
          >
            <Container className="flex flex-col gap-1 py-4">
              {NAV_LINKS.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  onClick={() => setMenuOpen(false)}
                  className="rounded-md px-2 py-2.5 text-sm font-medium text-cream-800 hover:bg-cream-200"
                >
                  {link.label}
                </NavLink>
              ))}
              <NavLink
                to="/cart"
                onClick={() => setMenuOpen(false)}
                className="rounded-md px-2 py-2.5 text-sm font-medium text-cream-800 hover:bg-cream-200"
              >
                Cart {cartCount > 0 ? `(${cartCount})` : ""}
              </NavLink>
              <div className="mt-2 flex flex-col gap-2 border-t border-cream-200 pt-3">
                {user ? (
                  <>
                    <Link to="/account/bookings" onClick={() => setMenuOpen(false)} className="px-2 py-1 text-sm">
                      My bookings
                    </Link>
                    <Link to="/account/orders" onClick={() => setMenuOpen(false)} className="px-2 py-1 text-sm">
                      My orders
                    </Link>
                    {user.role === "staff_admin" && (
                      <Link to="/staff/dashboard" onClick={() => setMenuOpen(false)} className="px-2 py-1 text-sm">
                        Staff dashboard
                      </Link>
                    )}
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        handleLogout();
                      }}
                      className="px-2 py-1 text-left text-sm text-primary-700"
                    >
                      Log out
                    </button>
                  </>
                ) : (
                  <>
                    <Link to="/login" onClick={() => setMenuOpen(false)} className="px-2 py-1 text-sm font-medium">
                      Log in
                    </Link>
                    <Button size="sm" onClick={() => { setMenuOpen(false); navigate("/book-a-table"); }}>
                      Book a table
                    </Button>
                  </>
                )}
              </div>
            </Container>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  );
}

function UserMenu({ name, role, onLogout }: { name: string; role: string; onLogout: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium text-cream-900 hover:bg-cream-200"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-100 text-xs font-semibold text-primary-700">
          {name.charAt(0).toUpperCase()}
        </span>
        {name.split(" ")[0]}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            role="menu"
            className="absolute right-0 mt-2 w-48 rounded-lg border border-cream-200 bg-cream-50 py-1.5 shadow-medium"
            onMouseLeave={() => setOpen(false)}
          >
            <Link to="/account/bookings" role="menuitem" className="block px-4 py-2 text-sm hover:bg-cream-100">
              My bookings
            </Link>
            <Link to="/account/orders" role="menuitem" className="block px-4 py-2 text-sm hover:bg-cream-100">
              My orders
            </Link>
            {role === "staff_admin" && (
              <Link to="/staff/dashboard" role="menuitem" className="block px-4 py-2 text-sm hover:bg-cream-100">
                Staff dashboard
              </Link>
            )}
            <button
              onClick={onLogout}
              role="menuitem"
              className="block w-full px-4 py-2 text-left text-sm text-primary-700 hover:bg-cream-100"
            >
              Log out
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function MenuIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
    </svg>
  );
}

function CartIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path
        d="M3 4h2l2.4 12.4a2 2 0 0 0 2 1.6h7.2a2 2 0 0 0 2-1.6L20 8H6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="9" cy="20" r="1.3" />
      <circle cx="17" cy="20" r="1.3" />
    </svg>
  );
}
