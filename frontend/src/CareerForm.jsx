import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { api, getErrorMessage } from "./api";
import {
  initialAssessment,
  assessmentSteps,
  restoreAssessment,
  validResult,
  invalidAssessmentField,
} from "./assessment";
import { readLocal, writeLocal } from "./storage";
import Results from "./Results";
import Icon from "./Icon";

const DRAFT_KEY = "career-assessment-draft-v1";
const boundedStep = (value) =>
  Number.isInteger(value) ? Math.max(0, Math.min(5, value)) : 0;
const selectOptions = {
  age_range: [
    ["Under 18", "under_18"],
    ["18-20", "age_18_20"],
    ["21-23", "age_21_23"],
    ["24-26", "age_24_26"],
    ["27-30", "age_27_30"],
    ["31+", "age_31_plus"],
  ],
  education_level: [
    ["High School", "high_school"],
    ["Associate's", "associates"],
    ["Bachelor's", "bachelors"],
    ["Master's", "masters"],
    ["PhD", "phd"],
    ["Professional Certification", "professional_certification"],
    ["Other", "other"],
  ],
  year_of_study: [
    ["Freshman Year", "freshman"],
    ["Sophomore Year", "sophomore"],
    ["Junior Year", "junior"],
    ["Senior Year", "senior"],
    ["Graduate Year 1", "graduate_year_1"],
    ["Graduate Year 2+", "graduate_year_2_plus"],
    ["Graduate", "graduate"],
    ["Not applicable", "not_applicable"],
  ],
};

export default function CareerForm() {
  const { t } = useTranslation();
  const [draft] = useState(() => readLocal(DRAFT_KEY, {}));
  const [formData, setFormData] = useState(() => restoreAssessment(draft));
  const [step, setStep] = useState(() => boundedStep(draft?.step));
  const [furthest, setFurthest] = useState(() =>
    Math.max(boundedStep(draft?.step), boundedStep(draft?.furthest)),
  );
  const [result, setResult] = useState(() =>
    validResult(draft?.result) ? draft.result : null,
  );
  const [saveHistory, setSaveHistory] = useState(
    () => draft?.saveHistory !== false,
  );
  const [saved, setSaved] = useState(() => Boolean(draft?.saved));
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const [canStore, setCanStore] = useState(true);
  const formRef = useRef(null);
  const headingRef = useRef(null);
  const busy = useRef(false);
  const savingRef = useRef(false);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    setCanStore(
      writeLocal(DRAFT_KEY, {
        formData,
        step,
        furthest,
        result,
        saveHistory,
        saved,
      }),
    );
  }, [formData, step, furthest, result, saveHistory, saved]);
  useEffect(() => {
    const heading = result
      ? document.getElementById("results-heading")
      : headingRef.current;
    heading?.focus({ preventScroll: true });
  }, [step, result]);

  const changeValue = (key, value) =>
    setFormData((previous) => ({ ...previous, [key]: value }));
  const moveTo = (next) => {
    if (loading || (next > step && !formRef.current?.reportValidity())) return;
    setError(null);
    setStep(next);
    setFurthest((previous) => Math.max(previous, next));
    headingRef.current?.scrollIntoView?.({ block: "start" });
  };
  const saveResult = async (response) => {
    if (savingRef.current) return;
    savingRef.current = true;
    setSaving(true);
    setSaveError(null);
    try {
      await api.saveAssessment(formData, response);
      if (mounted.current) setSaved(true);
      else {
        const stored = readLocal(DRAFT_KEY);
        if (stored?.result?.id === response.id)
          writeLocal(DRAFT_KEY, { ...stored, saved: true });
      }
    } catch (failure) {
      if (mounted.current) setSaveError(getErrorMessage(failure));
    } finally {
      savingRef.current = false;
      if (mounted.current) setSaving(false);
    }
  };
  const handleSubmit = async (event) => {
    event.preventDefault();
    if (busy.current) return;
    if (step < 5) {
      moveTo(step + 1);
      return;
    }
    const invalid = invalidAssessmentField(formData);
    if (invalid) {
      setStep(Math.max(0, assessmentSteps.indexOf(invalid.split("_")[0])));
      setError(t("check_answer", { field: t(invalid) }));
      return;
    }
    busy.current = true;
    setLoading(true);
    setError(null);
    setSaved(false);
    setSaveError(null);
    try {
      const response = await api.recommendCareerWithExplanation(formData);
      if (!validResult(response)) throw new Error(t("invalid_response"));
      response.id =
        window.crypto?.randomUUID?.() ||
        `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      response.timestamp = new Date().toISOString();
      if (!mounted.current) return;
      setResult(response);
      if (saveHistory) await saveResult(response);
    } catch (failure) {
      if (mounted.current) setError(getErrorMessage(failure));
    } finally {
      busy.current = false;
      if (mounted.current) setLoading(false);
    }
  };
  const restart = () => {
    setFormData({ ...initialAssessment });
    setStep(0);
    setFurthest(0);
    setResult(null);
    setSaved(false);
    setError(null);
    setSaveError(null);
  };
  if (result)
    return (
      <Results
        result={result}
        saved={saved}
        saving={saving}
        saveError={saveError}
        onRetrySave={() => saveResult(result)}
        onEdit={() => {
          setResult(null);
          setStep(0);
        }}
        onRestart={restart}
      />
    );

  const group = assessmentSteps[step];
  const fields = Object.keys(initialAssessment).filter(
    (key) => key.startsWith(`${group}_`) && key !== "skill_gaps",
  );
  const today = new Date();
  const maxDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  return (
    <div className="assessment-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">{t("your_next_chapter")}</span>
          <h1>{t("assessment_headline")}</h1>
          <p>{t("assessment_intro")}</p>
        </div>
        <span className="quiet-badge">
          <Icon name="clock" size={16} />
          {t("your_own_pace")}
        </span>
      </div>
      <div className="assessment-layout">
        <aside
          className="assessment-outline"
          aria-label={t("assessment_progress")}
        >
          <div className="outline-heading">
            <span>{t("your_assessment")}</span>
            <span className="numeric">{step + 1} / 6</span>
          </div>
          <div
            className="track outline-track"
            role="progressbar"
            aria-label={t("assessment_progress")}
            aria-valuenow={step}
            aria-valuemin="0"
            aria-valuemax="6"
          >
            <span style={{ width: `${(step / 6) * 100}%` }} />
          </div>
          <ol className="step-list">
            {assessmentSteps.map((name, index) => (
              <li key={name}>
                <button
                  type="button"
                  className={`step-button ${index === step ? "current" : ""} ${index < step ? "complete" : ""}`}
                  aria-current={index === step ? "step" : undefined}
                  aria-label={t(`step_${name}`)}
                  disabled={index > furthest || loading}
                  onClick={() => moveTo(index)}
                >
                  <span className="step-number">
                    {index < step ? <Icon name="check" size={15} /> : index + 1}
                  </span>
                  <span>
                    <strong>{t(`step_${name}`)}</strong>
                    <small>{t(`step_${name}_short`)}</small>
                  </span>
                </button>
              </li>
            ))}
          </ol>
          <div className="outline-note">
            <Icon name="shield" />
            <p>{t("honest_answers")}</p>
          </div>
        </aside>
        <form
          ref={formRef}
          onSubmit={handleSubmit}
          className="assessment-panel panel"
        >
          <div className="step-heading">
            <span className="eyebrow">
              {t("step_count", { current: step + 1, total: 6 })}
            </span>
            <h2 ref={headingRef} tabIndex="-1">
              {t(`step_${group}_title`)}
            </h2>
            <p>{t(`step_${group}_description`)}</p>
          </div>
          <fieldset disabled={loading} className="step-fields">
            <legend className="sr-only">{t(`step_${group}`)}</legend>
            {step === 0 ? (
              <>
                <div className="background-grid">
                  {[
                    "age_range",
                    "education_level",
                    "field_of_study",
                    "year_of_study",
                  ].map((key) => (
                    <div className="field" key={key}>
                      <label htmlFor={key}>{t(key)}</label>
                      {selectOptions[key] ? (
                        <select
                          id={key}
                          name={key}
                          value={formData[key]}
                          onChange={(e) => changeValue(key, e.target.value)}
                        >
                          {selectOptions[key].map(([value, label]) => (
                            <option key={value} value={value}>
                              {t(label)}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          id={key}
                          name={key}
                          required
                          maxLength="100"
                          value={formData[key]}
                          onChange={(e) => changeValue(key, e.target.value)}
                          autoComplete="off"
                        />
                      )}
                    </div>
                  ))}
                </div>
                <div className="confidence-field">
                  <div className="row-between">
                    <label htmlFor="confidence_score">
                      {t("assessment_confidence")}
                    </label>
                    <output htmlFor="confidence_score" className="value-pill">
                      {Math.round(formData.confidence_score * 100)}%
                    </output>
                  </div>
                  <p>{t("confidence_help")}</p>
                  <input
                    id="confidence_score"
                    name="confidence_score"
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={formData.confidence_score}
                    onChange={(e) =>
                      changeValue("confidence_score", Number(e.target.value))
                    }
                  />
                  <div className="range-labels">
                    <span>{t("still_exploring")}</span>
                    <span>{t("very_confident")}</span>
                  </div>
                </div>
                <div className="inline-tip">
                  <Icon name="spark" />
                  <p>{t("assessment_tip")}</p>
                </div>
              </>
            ) : (
              <>
                <div className="scale-key">
                  <span>
                    {t(
                      group === "skill"
                        ? "skill_scale_low"
                        : group === "academic"
                          ? "knowledge_scale_low"
                          : "rating_scale_low",
                    )}
                  </span>
                  <span>
                    {t(
                      group === "skill"
                        ? "skill_scale_high"
                        : group === "academic"
                          ? "knowledge_scale_high"
                          : "rating_scale_high",
                    )}
                  </span>
                </div>
                <div
                  className={
                    group === "skill" ? "skill-input-grid" : "rating-list"
                  }
                >
                  {fields.map((key) =>
                    group === "skill" ? (
                      <div className="skill-input-card" key={key}>
                        <div className="row-between">
                          <label htmlFor={key}>{t(key)}</label>
                          <input
                            id={key}
                            className="skill-number numeric"
                            name={key}
                            type="number"
                            required
                            min="0"
                            max="5"
                            step="0.1"
                            value={formData[key]}
                            onChange={(e) =>
                              changeValue(
                                key,
                                e.target.value === ""
                                  ? ""
                                  : Number(e.target.value),
                              )
                            }
                          />
                        </div>
                        <input
                          type="range"
                          aria-label={t("adjust_skill", { skill: t(key) })}
                          min="0"
                          max="5"
                          step="0.1"
                          value={formData[key] === "" ? 0 : formData[key]}
                          onChange={(e) =>
                            changeValue(key, Number(e.target.value))
                          }
                        />
                        <details className="skill-recency">
                          <summary>{t("add_recency")}</summary>
                          <label htmlFor={`last_used_${key}`}>
                            {t("last_used")}
                          </label>
                          <input
                            id={`last_used_${key}`}
                            name={`last_used_${key}`}
                            type="date"
                            max={maxDate}
                            value={formData[`last_used_${key}`]}
                            onChange={(e) =>
                              changeValue(`last_used_${key}`, e.target.value)
                            }
                          />
                        </details>
                      </div>
                    ) : (
                      <div
                        className="rating-row"
                        role="radiogroup"
                        aria-labelledby={`${key}-label`}
                        key={key}
                      >
                        <span className="rating-label" id={`${key}-label`}>
                          {t(key)}
                        </span>
                        <div className="rating-options">
                          {[1, 2, 3, 4, 5].map((level) => (
                            <label className="rating-option" key={level}>
                              <input
                                type="radio"
                                aria-label={t("rating_for", {
                                  skill: t(key),
                                  level,
                                })}
                                name={key}
                                value={level}
                                checked={formData[key] === level}
                                onChange={() => changeValue(key, level)}
                              />
                              <span>{level}</span>
                              <span className="sr-only">
                                {t("rating_for", { skill: t(key), level })}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    ),
                  )}
                </div>
              </>
            )}
            {step === 5 && (
              <label className="save-preference">
                <input
                  type="checkbox"
                  checked={saveHistory}
                  onChange={(event) => setSaveHistory(event.target.checked)}
                />
                <span>
                  <strong>{t("save_to_dashboard")}</strong>
                  <small>{t("save_history_description")}</small>
                </span>
              </label>
            )}
          </fieldset>
          {error && (
            <div className="notice error" role="alert">
              <Icon name="refresh" />
              <div>
                <strong>{t("recommendation_failed")}</strong>
                <p>{error}</p>
              </div>
            </div>
          )}
          <div className="form-footer">
            <span className="draft-status">
              <Icon name={canStore ? "check" : "shield"} size={15} />
              {t(canStore ? "draft_saved" : "draft_session_only")}
            </span>
            <div className="form-navigation">
              {step > 0 && (
                <button
                  type="button"
                  className="button secondary"
                  disabled={loading}
                  onClick={() => moveTo(step - 1)}
                >
                  <Icon name="back" />
                  {t("back")}
                </button>
              )}
              <button
                type="submit"
                className="button primary"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner" />
                    {t("finding_matches")}
                  </>
                ) : (
                  <>
                    {t(step === 5 ? "find_matches" : "continue")}
                    <Icon name="arrow" />
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
      <div className="assessment-footnote">
        <Icon name="compass" size={16} />
        <p>{t("guidance_note")}</p>
      </div>
    </div>
  );
}
