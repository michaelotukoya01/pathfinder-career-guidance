import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  timeout: 60000,
});
const PROFILE_KEY = "career-profile-id";
const TOKEN_KEY = "career-profile-token";

function profileHeaders() {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token)
    throw new Error(
      "This saved profile needs its device access token. Use Restore access on the dashboard, or start a new private history.",
    );
  return { headers: { Authorization: `Bearer ${token}` } };
}
function clearProfileLink() {
  localStorage.removeItem(PROFILE_KEY);
  localStorage.removeItem(TOKEN_KEY);
}
export function getErrorMessage(error) {
  if (error.code === "ECONNABORTED")
    return "The service took too long to respond. Please try again.";
  if (error.message === "Network Error")
    return "Unable to reach the career service. Check that the backend is running and try again.";
  const data = error.response?.data;
  if (Array.isArray(data?.errors))
    return data.errors
      .map((item) => `${item.loc?.slice(1).join(".")}: ${item.msg}`)
      .join("; ");
  if (error.response?.status === 401)
    return "Access to this profile has expired or its device token is missing. Restore access from the dashboard.";
  if (typeof data?.detail === "string") return data.detail;
  return error.message || "Unable to complete the request.";
}

export const api = {
  recommendCareer: async (formData) =>
    (await client.post("/recommend", formData)).data,
  recommendCareerWithExplanation: async (formData) =>
    (
      await client.post("/recommend", formData, {
        params: { include_explanation: true },
      })
    ).data,
  saveAssessment: async (formData, result) => {
    let profileId = localStorage.getItem(PROFILE_KEY);
    const profile = Object.fromEntries(
      [
        "age_range",
        "education_level",
        "field_of_study",
        "year_of_study",
        "confidence_score",
      ].map((key) => [key, formData[key]]),
    );
    if (profileId) {
      try {
        await client.put(
          `/profiles/${encodeURIComponent(profileId)}`,
          profile,
          profileHeaders(),
        );
      } catch (error) {
        if (error.response?.status !== 404) throw error;
        clearProfileLink();
        profileId = null;
      }
    }
    if (!profileId) {
      const { data } = await client.post("/profiles", profile);
      if (!data.id || !data.access_token)
        throw new Error(
          "The service did not return valid profile credentials.",
        );
      // Write the credential before the ID so incomplete local writes cannot link an unprotected profile.
      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(PROFILE_KEY, data.id);
      profileId = data.id;
    }
    await client.post(
      `/profiles/${encodeURIComponent(profileId)}/assessments`,
      result,
      profileHeaders(),
    );
  },
  getDashboard: async () => {
    const profileId = localStorage.getItem(PROFILE_KEY);
    if (!profileId) return { profile: null, assessments: [] };
    try {
      const { data: profile } = await client.get(
        `/profiles/${encodeURIComponent(profileId)}`,
        profileHeaders(),
      );
      return {
        profile,
        assessments: Array.isArray(profile.assessments)
          ? profile.assessments
          : [],
      };
    } catch (error) {
      if ([404, 422].includes(error.response?.status)) {
        clearProfileLink();
        return { profile: null, assessments: [] };
      }
      throw error;
    }
  },
  restoreProfile: async (profileId, token) => {
    const { data } = await client.get(
      `/profiles/${encodeURIComponent(profileId.trim())}`,
      { headers: { Authorization: `Bearer ${token.trim()}` } },
    );
    localStorage.setItem(TOKEN_KEY, token.trim());
    localStorage.setItem(PROFILE_KEY, data.id);
  },
  deleteProfile: async () => {
    const profileId = localStorage.getItem(PROFILE_KEY);
    if (profileId)
      await client.delete(
        `/profiles/${encodeURIComponent(profileId)}`,
        profileHeaders(),
      );
    clearProfileLink();
    localStorage.removeItem("career-assessment-draft-v1");
    localStorage.removeItem("career-learning-progress-v1");
  },
  startPrivateHistory: () => {
    clearProfileLink();
    const draft = localStorage.getItem("career-assessment-draft-v1");
    if (draft) {
      try {
        localStorage.setItem(
          "career-assessment-draft-v1",
          JSON.stringify({ ...JSON.parse(draft), saved: false }),
        );
      } catch {
        /* A malformed draft will be discarded by the form. */
      }
    }
  },
};
