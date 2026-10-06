import { vi, beforeEach, test, expect } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

import { MemoryRouter } from "react-router-dom";
import App from "./App";
import CareerForm from "./CareerForm";
import Dashboard, { processSkillProgress } from "./Dashboard";
import { api } from "./api";
import i18n from "./i18n";

vi.mock("./api", () => ({
  api: {
    recommendCareerWithExplanation: vi.fn(),
    saveAssessment: vi.fn(),
    getDashboard: vi.fn(),
  },
  getErrorMessage: (error) => error.message,
}));
const result = {
  recommended_career: "Data Scientist",
  confidence: 0.8,
  top_3_predictions: [{ career: "Data Scientist", probability: 0.8 }],
  skill_gap_analysis: [
    { skill: "skill_python", user_level: 3.5, career_average: 4, gap: 0.5 },
  ],
};
const wrapper = ({ children }) => (
  <MemoryRouter
    future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
  >
    {children}
  </MemoryRouter>
);
const next = () =>
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
const finish = () => {
  while (screen.queryByRole("button", { name: "Continue" })) next();
  fireEvent.click(
    screen.getByRole("button", { name: "Find my career matches" }),
  );
};
beforeEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
  window.history.replaceState({}, "", "/");
  i18n.changeLanguage("en");
  api.recommendCareerWithExplanation.mockImplementation(async () => ({
    ...result,
  }));
  api.saveAssessment.mockResolvedValue();
});

test("guided assessment submits editable ratings and fractional skills, then saves results", async () => {
  render(<CareerForm />, { wrapper });
  expect(
    screen.getByRole("heading", { name: "Let's start with you." }),
  ).toBeInTheDocument();
  next();
  expect(screen.getAllByRole("radiogroup")).toHaveLength(6);
  fireEvent.click(
    screen.getByRole("radio", { name: "Mathematics: 5 out of 5" }),
  );
  next();
  expect(screen.getAllByRole("spinbutton")).toHaveLength(14);
  fireEvent.change(screen.getByLabelText("Python"), {
    target: { value: "3.5" },
  });
  finish();
  await waitFor(() => expect(api.saveAssessment).toHaveBeenCalledTimes(1));
  const payload = api.recommendCareerWithExplanation.mock.calls[0][0];
  expect(payload.skill_python).toBe(3.5);
  expect(payload.academic_mathematics).toBe(5);
  expect(
    Object.keys(payload).filter(
      (key) =>
        /^(academic|skill|interest|workpref|personality)_/.test(key) &&
        key !== "skill_gaps",
    ),
  ).toHaveLength(41);
  expect(
    await screen.findByText("Saved to your dashboard"),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "View dashboard" })).toHaveAttribute(
    "href",
    "/dashboard",
  );
});

test("invalid required background blocks advancing and draft restores step and values", () => {
  const view = render(<CareerForm />, { wrapper });
  fireEvent.change(screen.getByLabelText("Field of Study"), {
    target: { value: "" },
  });
  next();
  expect(screen.getByLabelText("Field of Study")).toBeInvalid();
  fireEvent.change(screen.getByLabelText("Field of Study"), {
    target: { value: "Engineering" },
  });
  next();
  next();
  fireEvent.change(screen.getByLabelText("Python"), {
    target: { value: "2.7" },
  });
  view.unmount();
  render(<CareerForm />, { wrapper });
  expect(
    screen.getByRole("heading", { name: "Make your skills visible." }),
  ).toBeInTheDocument();
  expect(screen.getByLabelText("Python")).toHaveValue(2.7);
  fireEvent.click(screen.getByRole("button", { name: "Back" }));
  fireEvent.click(screen.getByRole("button", { name: "Back" }));
  expect(screen.getByLabelText("Field of Study")).toHaveValue("Engineering");
});

test("saving failure preserves results and retry uses the same assessment without predicting again", async () => {
  api.saveAssessment
    .mockRejectedValueOnce(new Error("Server unavailable"))
    .mockResolvedValueOnce();
  render(<CareerForm />, { wrapper });
  finish();
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "saving it failed",
  );
  expect(
    screen.getByRole("heading", { name: "Your next chapter starts here." }),
  ).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Retry saving" }));
  expect(
    await screen.findByText("Saved to your dashboard"),
  ).toBeInTheDocument();
  expect(api.saveAssessment).toHaveBeenCalledTimes(2);
  expect(api.saveAssessment.mock.calls[0][1].id).toBeTruthy();
  expect(api.saveAssessment.mock.calls[0][1].id).toBe(
    api.saveAssessment.mock.calls[1][1].id,
  );
  expect(api.recommendCareerWithExplanation).toHaveBeenCalledTimes(1);
});

test("request failure can be retried and saving can be turned off", async () => {
  api.recommendCareerWithExplanation
    .mockRejectedValueOnce(new Error("Service unavailable"))
    .mockResolvedValueOnce({ ...result });
  render(<CareerForm />, { wrapper });
  for (let index = 0; index < 5; index++) next();
  fireEvent.click(screen.getByRole("checkbox"));
  finish();
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Service unavailable",
  );
  finish();
  expect(
    await screen.findByRole("heading", {
      name: "Your next chapter starts here.",
    }),
  ).toBeInTheDocument();
  expect(api.saveAssessment).not.toHaveBeenCalled();
  expect(
    screen.getByRole("button", {
      name: "Save this assessment to my dashboard",
    }),
  ).toBeInTheDocument();
});

test("pending submission cannot be repeated and result actions wait for saving", async () => {
  let completeSave;
  api.saveAssessment.mockReturnValue(
    new Promise((resolve) => {
      completeSave = resolve;
    }),
  );
  render(<CareerForm />, { wrapper });
  finish();
  expect(
    await screen.findByRole("button", { name: "Edit answers" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Start a new assessment" }),
  ).toBeDisabled();
  expect(api.recommendCareerWithExplanation).toHaveBeenCalledTimes(1);
  completeSave();
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Edit answers" })).toBeEnabled(),
  );
});

test("corrupt saved result falls back to a usable assessment", () => {
  localStorage.setItem(
    "career-assessment-draft-v1",
    JSON.stringify({
      result: { ...result, explanation: {} },
      step: 99,
      formData: { skill_python: -1 },
    }),
  );
  render(<CareerForm />, { wrapper });
  expect(
    screen.getByRole("button", { name: "Find my career matches" }),
  ).toBeInTheDocument();
  expect(screen.queryByText("Data Scientist")).not.toBeInTheDocument();
});

test("submission returns to an invalid earlier section instead of sending incomplete answers", () => {
  render(<CareerForm />, { wrapper });
  for (let index = 0; index < 5; index++) next();
  fireEvent.click(screen.getByRole("button", { name: "Technical skills" }));
  fireEvent.change(screen.getByLabelText("Python"), { target: { value: "" } });
  fireEvent.click(screen.getByRole("button", { name: "Back" }));
  fireEvent.click(
    screen.getByRole("button", {
      name: "Your working style",
    }),
  );
  finish();
  expect(screen.getByRole("alert")).toHaveTextContent(
    "Please check your answer for Python",
  );
  expect(screen.getByLabelText("Python")).toBeInvalid();
  expect(api.recommendCareerWithExplanation).not.toHaveBeenCalled();
});

test("assessment remains usable when device storage is unavailable", () => {
  const storage = vi
    .spyOn(Storage.prototype, "setItem")
    .mockImplementation(() => {
      throw new Error("Storage unavailable");
    });
  try {
    render(<CareerForm />, { wrapper });
    expect(screen.getByText(/Device storage unavailable/)).toBeInTheDocument();
    next();
    expect(
      screen.getByRole("heading", { name: "What have you learned?" }),
    ).toBeInTheDocument();
  } finally {
    storage.mockRestore();
  }
});

test("results export as JSON and a new assessment clears the previous result", async () => {
  URL.createObjectURL = vi.fn(() => "blob:assessment");
  URL.revokeObjectURL = vi.fn();
  const click = vi
    .spyOn(HTMLAnchorElement.prototype, "click")
    .mockImplementation(() => {});
  try {
    render(<CareerForm />, { wrapper });
    finish();
    await screen.findByText("Saved to your dashboard");
    fireEvent.click(screen.getByRole("button", { name: "Download results" }));
    expect(URL.createObjectURL.mock.calls[0][0]).toBeInstanceOf(Blob);
    expect(click).toHaveBeenCalledTimes(1);
    fireEvent.click(
      screen.getByRole("button", { name: "Start a new assessment" }),
    );
    expect(
      screen.getByRole("heading", { name: "Let's start with you." }),
    ).toBeInTheDocument();
    expect(
      JSON.parse(localStorage.getItem("career-assessment-draft-v1")).result,
    ).toBeNull();
  } finally {
    click.mockRestore();
  }
});

test("dashboard error is retryable and empty state does not invent progress", async () => {
  api.getDashboard
    .mockRejectedValueOnce(new Error("Offline"))
    .mockResolvedValueOnce({ profile: null, assessments: [] });
  render(<Dashboard />, { wrapper });
  expect(await screen.findByRole("alert")).toHaveTextContent("Offline");
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(
    await screen.findByText(/No saved assessments yet/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
  expect(api.getDashboard).toHaveBeenCalledTimes(2);
});

test("dashboard shows actual saved history and a single observed skill point", async () => {
  api.getDashboard.mockResolvedValue({
    profile: {},
    assessments: [{ ...result, id: "assessment-1", timestamp: "2026-01-02" }],
  });
  render(<Dashboard />, { wrapper });
  expect(await screen.findByText("Saved assessments")).toBeInTheDocument();
  expect(screen.getByText(/Your first data point/)).toBeInTheDocument();
  expect(
    screen
      .getByRole("img", { name: "Python level across saved assessments" })
      .querySelectorAll("circle"),
  ).toHaveLength(1);
  expect(
    screen.getByRole("heading", { name: "Your learning priorities" }),
  ).toBeInTheDocument();
});

test("progress is chronological and excludes missing dates or invalid levels", () => {
  const progress = processSkillProgress([
    {
      timestamp: "2026-01-02",
      skill_gap_analysis: [{ skill: "skill_data analysis", user_level: 4 }],
    },
    {
      timestamp: "2026-01-01",
      skill_gap_analysis: [{ skill: "skill_data_analysis", user_level: 2 }],
    },
    {
      timestamp: "invalid",
      skill_gap_analysis: [{ skill: "skill_python", user_level: 5 }],
    },
    {
      timestamp: "2026-01-03",
      skill_gap_analysis: [{ skill: "skill_python", user_level: null }],
    },
  ]);
  expect(Object.keys(progress)).toEqual(["skill_data_analysis"]);
  expect(progress.skill_data_analysis.map((point) => point.level)).toEqual([
    2, 4,
  ]);
});

test("navigation handles unknown pages and language changes persist", async () => {
  window.history.replaceState({}, "", "/missing");
  render(<App />);
  expect(
    screen.getByRole("heading", { name: "This path doesn't lead anywhere." }),
  ).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Language"), {
    target: { value: "es" },
  });
  expect(
    await screen.findByRole("heading", {
      name: "Esta ruta no lleva a ninguna página.",
    }),
  ).toBeInTheDocument();
  expect(document.documentElement.lang).toBe("es");
  expect(JSON.parse(localStorage.getItem("career-language"))).toBe("es");
});
