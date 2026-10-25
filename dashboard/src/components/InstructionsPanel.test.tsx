import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InstructionsPanel } from "./InstructionsPanel";

describe("InstructionsPanel", () => {
  it("renders instructions without an editor", () => {
    render(<InstructionsPanel instructions="Follow the policy wording." />);
    expect(screen.getByText("Follow the policy wording.")).toBeVisible();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });
});
