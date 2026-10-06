export const initialAssessment = {
  age_range: "21-23",
  education_level: "Bachelor's",
  field_of_study: "Computer Science",
  year_of_study: "Senior Year",
  confidence_score: 0.85,
  academic_mathematics: 3,
  academic_statistics: 3,
  academic_programming: 4,
  academic_computer_networking: 3,
  academic_database_management: 3,
  academic_web_development: 3,
  skill_python: 4,
  skill_javascript: 3,
  skill_java: 2,
  skill_c_cplusplus: 2,
  skill_sql: 3,
  skill_html_css: 3,
  skill_react: 2,
  skill_networking: 3,
  skill_linux: 3,
  skill_databases: 3,
  skill_cloud: 2,
  skill_cybersecurity: 2,
  skill_data_analysis: 3,
  skill_machine_learning: 3,
  interest_building_applications: 4,
  interest_analyzing_data: 3,
  interest_artificial_intelligence: 4,
  interest_cybersecurity: 2,
  interest_networking: 3,
  interest_cloud_computing: 2,
  interest_databases: 3,
  interest_ui_ux_design: 2,
  interest_research: 3,
  workpref_building_things: 4,
  workpref_analyzing_information: 3,
  workpref_solving_security_problems: 2,
  workpref_working_with_numbers: 3,
  workpref_designing_ui: 2,
  workpref_investigating_problems: 3,
  personality_analytical: 4,
  personality_creative: 2,
  personality_problem_solver: 4,
  personality_detail_oriented: 3,
  personality_collaborative: 3,
  personality_independent_worker: 3,
  skill_gaps: "{}",
  // Skill recency fields (last used dates)
  last_used_skill_python: "",
  last_used_skill_javascript: "",
  last_used_skill_java: "",
  last_used_skill_c_cplusplus: "",
  last_used_skill_sql: "",
  last_used_skill_html_css: "",
  last_used_skill_react: "",
  last_used_skill_networking: "",
  last_used_skill_linux: "",
  last_used_skill_databases: "",
  last_used_skill_cloud: "",
  last_used_skill_cybersecurity: "",
  last_used_skill_data_analysis: "",
  last_used_skill_machine_learning: "",
};

export const assessmentSteps = [
  "background",
  "academic",
  "skill",
  "interest",
  "workpref",
  "personality",
];

export function invalidAssessmentField(data) {
  return Object.keys(initialAssessment).find((key) => {
    const value = data[key];
    if (typeof initialAssessment[key] === "number") {
      const fractional = key.startsWith("skill_") || key === "confidence_score";
      return (
        !Number.isFinite(value) ||
        value < (fractional ? 0 : 1) ||
        value > (key === "confidence_score" ? 1 : 5) ||
        (!fractional && !Number.isInteger(value))
      );
    }
    return (
      [
        "age_range",
        "education_level",
        "field_of_study",
        "year_of_study",
      ].includes(key) &&
      (typeof value !== "string" || !value.trim() || value.length > 100)
    );
  });
}

export function restoreAssessment(draft) {
  const restored = { ...initialAssessment };
  if (!draft?.formData || typeof draft.formData !== "object") return restored;
  Object.entries(restored).forEach(([key, fallback]) => {
    const value = draft.formData[key];
    if (typeof fallback === "number") {
      const min =
        key.startsWith("skill_") || key === "confidence_score" ? 0 : 1;
      const max = key === "confidence_score" ? 1 : 5;
      if (
        typeof value === "number" &&
        Number.isFinite(value) &&
        value >= min &&
        value <= max &&
        (key.startsWith("skill_") ||
          key === "confidence_score" ||
          Number.isInteger(value))
      )
        restored[key] = value;
    } else if (
      typeof value === "string" &&
      value.length <= 200 &&
      (!key.startsWith("last_used_") ||
        value === "" ||
        /^\d{4}-\d{2}-\d{2}$/.test(value))
    ) {
      restored[key] = value;
    }
  });
  return restored;
}

export function validResult(result) {
  const score = (value) => Number.isFinite(value) && value >= 0 && value <= 1;
  return (
    result &&
    typeof result.recommended_career === "string" &&
    score(result.confidence) &&
    Array.isArray(result.top_3_predictions) &&
    result.top_3_predictions.length > 0 &&
    result.top_3_predictions.every(
      (p) => p && typeof p.career === "string" && score(p.probability),
    ) &&
    (result.explanation == null || typeof result.explanation === "string") &&
    (result.skill_decay_info == null ||
      (typeof result.skill_decay_info === "object" &&
        Object.values(result.skill_decay_info).every(
          (info) =>
            info &&
            Number.isFinite(info.original_level) &&
            Number.isFinite(info.decayed_level),
        ))) &&
    Array.isArray(result.skill_gap_analysis) &&
    result.skill_gap_analysis.every(
      (g) =>
        g &&
        typeof g.skill === "string" &&
        ["user_level", "career_average", "gap"].every((key) =>
          Number.isFinite(g[key]),
        ) &&
        g.user_level >= 0 &&
        g.user_level <= 5 &&
        g.career_average >= 0 &&
        g.career_average <= 5,
    )
  );
}
