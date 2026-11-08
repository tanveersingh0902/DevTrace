import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { AppRoutes } from "./AppRoutes";

describe("AppRoutes", () => {
  it("renders the DevTrace application shell", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: /^devtrace$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /understand the shape/i })).toBeInTheDocument();
  });

  it("renders the main dashboard route", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(screen.getByText("No projects yet")).toBeInTheDocument();
  });
});
