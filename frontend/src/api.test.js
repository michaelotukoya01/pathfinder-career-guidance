import { vi, beforeEach, test, expect } from "vitest";
import axios from "axios";
import { api, getErrorMessage } from "./api";

vi.mock("axios", () => {
  const client = { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() };
  return { default: { create: vi.fn(() => client) } };
});
const client = axios.create();
const credentials = { headers: { Authorization: "Bearer device-token" } };
beforeEach(() => {
  vi.resetAllMocks();
  localStorage.clear();
  localStorage.setItem("career-profile-token", "device-token");
});

test("explanation is requested via query parameter", async () => {
  client.post.mockResolvedValue({ data: {} });
  await api.recommendCareerWithExplanation({ skill_python: 4 });
  expect(client.post).toHaveBeenCalledWith(
    "/recommend",
    { skill_python: 4 },
    { params: { include_explanation: true } },
  );
});
test("a missing saved profile is recreated with a private token", async () => {
  localStorage.setItem("career-profile-id", "old");
  client.put.mockRejectedValue({ response: { status: 404 } });
  client.post
    .mockResolvedValueOnce({
      data: { id: "new", access_token: "device-token" },
    })
    .mockResolvedValueOnce({ data: {} });
  const result = { recommended_career: "Data Scientist" };
  await api.saveAssessment({}, result);
  expect(localStorage.getItem("career-profile-id")).toBe("new");
  expect(client.post).toHaveBeenLastCalledWith(
    "/profiles/new/assessments",
    result,
    credentials,
  );
});
test("invalid credentials do not silently replace an existing history", async () => {
  localStorage.setItem("career-profile-id", "existing");
  client.put.mockRejectedValue({ response: { status: 401 } });
  await expect(api.saveAssessment({}, {})).rejects.toEqual({
    response: { status: 401 },
  });
  expect(client.post).not.toHaveBeenCalled();
  expect(localStorage.getItem("career-profile-id")).toBe("existing");
});
test("dashboard reads complete history with the device token", async () => {
  localStorage.setItem("career-profile-id", "existing");
  client.get.mockResolvedValue({
    data: {
      id: "existing",
      assessments: Array.from({ length: 61 }, (_, id) => ({ id })),
    },
  });
  expect((await api.getDashboard()).assessments).toHaveLength(61);
  expect(client.get).toHaveBeenCalledWith("/profiles/existing", credentials);
});
test("dashboard clears a deleted profile link and token", async () => {
  localStorage.setItem("career-profile-id", "missing");
  client.get.mockRejectedValue({ response: { status: 404 } });
  expect(await api.getDashboard()).toEqual({ profile: null, assessments: [] });
  expect(localStorage.getItem("career-profile-id")).toBeNull();
  expect(localStorage.getItem("career-profile-token")).toBeNull();
});
test("restoring access validates credentials before replacing local state", async () => {
  client.get.mockRejectedValueOnce({ response: { status: 401 } });
  await expect(api.restoreProfile("bad", "bad-token")).rejects.toBeTruthy();
  expect(localStorage.getItem("career-profile-token")).toBe("device-token");
  client.get.mockResolvedValueOnce({ data: { id: "restored" } });
  await api.restoreProfile("restored", "valid-token");
  expect(localStorage.getItem("career-profile-token")).toBe("valid-token");
});
test("deleting history clears local data only after the server succeeds", async () => {
  localStorage.setItem("career-profile-id", "existing");
  localStorage.setItem("career-assessment-draft-v1", "{}");
  client.delete
    .mockRejectedValueOnce(new Error("Offline"))
    .mockResolvedValueOnce({ data: {} });
  await expect(api.deleteProfile()).rejects.toThrow("Offline");
  expect(localStorage.getItem("career-profile-id")).toBe("existing");
  await api.deleteProfile();
  expect(localStorage.getItem("career-profile-id")).toBeNull();
  expect(localStorage.getItem("career-assessment-draft-v1")).toBeNull();
});
test("validation and connection failures have actionable messages", () => {
  expect(
    getErrorMessage({
      response: {
        data: {
          errors: [{ loc: ["body", "skill_python"], msg: "must be at most 5" }],
        },
      },
    }),
  ).toBe("skill_python: must be at most 5");
  expect(getErrorMessage({ message: "Network Error" })).toContain(
    "backend is running",
  );
  expect(getErrorMessage({ code: "ECONNABORTED" })).toContain("try again");
});
