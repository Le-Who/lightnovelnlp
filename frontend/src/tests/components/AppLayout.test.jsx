import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppLayout } from "../../components/layout/AppLayout";

// Mock navigate and location
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: "/" }),
  };
});

describe("AppLayout Navigation", () => {
  it("renders navigation items as accessible links", () => {
    render(
      <MemoryRouter>
        <AppLayout>
          <div>Content</div>
        </AppLayout>
      </MemoryRouter>,
    );

    // Check Dashboard link
    // It should now be an anchor. `getByText` finds the text inside.
    const dashboardLink = screen.getByText("Dashboard");
    const dashboardAnchor = dashboardLink.closest("a");

    expect(dashboardAnchor).toBeInTheDocument();
    expect(dashboardAnchor).toHaveAttribute("href", "/");

    // Check SYS.OP link
    const sysOpLink = screen.getByText("SYS.OP");
    const sysOpAnchor = sysOpLink.closest("a");

    expect(sysOpAnchor).toBeInTheDocument();
    expect(sysOpAnchor).toHaveAttribute("href", "/");
  });
});
