import { vi, beforeEach, test, expect } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ProfileControls from "./ProfileControls";
import LearningPlan from "./LearningPlan";
import { api } from "./api";
import i18n from "./i18n";

vi.mock("./api", () => ({
  api: {
    deleteProfile: vi.fn(),
    restoreProfile: vi.fn(),
    startPrivateHistory: vi.fn(),
  },
  getErrorMessage: (error) => error.message,
}));
beforeEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
  i18n.changeLanguage("en");
});

test("deletion requires confirmation and failures remain recoverable", async () => {
  const changed = vi.fn();
  api.deleteProfile
    .mockRejectedValueOnce(new Error("Offline"))
    .mockResolvedValueOnce();
  render(<ProfileControls hasProfile onChange={changed} />);
  fireEvent.click(screen.getByRole("button", { name: "Delete my saved data" }));
  expect(api.deleteProfile).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Offline");
  fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
  await waitFor(() => expect(changed).toHaveBeenCalledTimes(1));
});

test("restoring a history validates the supplied private code", async () => {
  api.restoreProfile.mockResolvedValue();
  const changed = vi.fn();
  render(<ProfileControls onChange={changed} />);
  fireEvent.click(screen.getByRole("button", { name: "Restore access" }));
  fireEvent.change(screen.getByLabelText("Profile ID"), {
    target: { value: "profile-id" },
  });
  fireEvent.change(screen.getByLabelText("Private access code"), {
    target: { value: "private-code" },
  });
  fireEvent.click(screen.getAllByRole("button", { name: "Restore access" })[1]);
  await waitFor(() =>
    expect(api.restoreProfile).toHaveBeenCalledWith(
      "profile-id",
      "private-code",
    ),
  );
  await waitFor(() => expect(changed).toHaveBeenCalledTimes(1));
});

test("learning milestones persist independently for different skills", () => {
  const first = render(<LearningPlan skill="skill_python" />);
  fireEvent.click(screen.getByText("Open your practice plan"));
  fireEvent.click(
    screen.getByRole("checkbox", {
      name: "Review the fundamentals and complete an example",
    }),
  );
  first.unmount();
  const second = render(<LearningPlan skill="skill_sql" />);
  fireEvent.click(screen.getByText("Open your practice plan"));
  expect(screen.getAllByRole("checkbox")[0]).not.toBeChecked();
  fireEvent.click(screen.getAllByRole("checkbox")[1]);
  second.unmount();
  render(<LearningPlan skill="skill_python" />);
  fireEvent.click(screen.getByText("Open your practice plan"));
  expect(screen.getAllByRole("checkbox")[0]).toBeChecked();
  expect(screen.getByRole("link", { name: /Python tutorial/ })).toHaveAttribute(
    "rel",
    "noopener noreferrer",
  );
  expect(
    JSON.parse(localStorage.getItem("career-learning-progress-v1"))[
      "skill_sql:build"
    ],
  ).toBe(true);
});
