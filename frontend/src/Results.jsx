import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import Icon from "./Icon";
import LearningPlan from "./LearningPlan";

export function SkillGaps({ gaps = [] }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  return (
    <>
      <div className="chart-legend">
        <span>
          <i className="legend-current" />
          {t("your_level")}
        </span>
        <span>
          <i className="legend-target" />
          {t("target_level")}
        </span>
        <span>{t("scale_five")}</span>
      </div>
      <ul className="skill-comparison">
        {gaps.slice(0, expanded ? gaps.length : 5).map((gap) => (
          <li key={gap.skill}>
            <div className="row-between">
              <span>{t(gap.skill.replaceAll(" ", "_"))}</span>
              <span className="numeric muted">
                {gap.user_level.toFixed(1)} / {gap.career_average.toFixed(1)}
              </span>
            </div>
            <div className="comparison-bars" aria-hidden="true">
              <div
                style={{
                  width: `${Math.min(100, Math.max(0, gap.career_average * 20))}%`,
                }}
                className="target-bar"
              />
              <div
                style={{
                  width: `${Math.min(100, Math.max(0, gap.user_level * 20))}%`,
                }}
                className="current-bar"
              />
            </div>
          </li>
        ))}
      </ul>
      {gaps.length > 5 && (
        <button
          className="text-button"
          type="button"
          onClick={() => setExpanded((value) => !value)}
          aria-expanded={expanded}
        >
          {t(expanded ? "show_less" : "show_all_skills")}
        </button>
      )}
    </>
  );
}

export function LearningPriorities({ gaps = [] }) {
  const { t } = useTranslation();
  const priorities = [...gaps]
    .filter((gap) => gap.gap > 0)
    .sort((a, b) => b.gap - a.gap)
    .slice(0, 3);
  return priorities.length ? (
    <ol className="learning-list">
      {priorities.map((gap, index) => (
        <li key={gap.skill}>
          <span className="learning-number">
            {String(index + 1).padStart(2, "0")}
          </span>
          <div>
            <h4>{t(gap.skill.replaceAll(" ", "_"))}</h4>
            <p>
              {t("practice_skill", {
                skill: t(gap.skill.replaceAll(" ", "_")),
              })}
            </p>
            <span className="tag">
              {t("level_goal", {
                current: gap.user_level.toFixed(1),
                target: gap.career_average.toFixed(1),
              })}
            </span>
            <LearningPlan skill={gap.skill} />
          </div>
        </li>
      ))}
    </ol>
  ) : (
    <p className="empty-copy">{t("skills_on_track")}</p>
  );
}

export default function Results({
  result,
  saved,
  saving,
  saveError,
  onRetrySave,
  onEdit,
  onRestart,
}) {
  const { t } = useTranslation();
  const strengths = result.skill_gap_analysis
    .filter((gap) => gap.gap <= 0)
    .slice(0, 4);
  const exportResult = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "career-assessment.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return (
    <div className="results-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">{t("your_next_chapter")}</span>
          <h1 tabIndex="-1" id="results-heading">
            {t("results_title")}
          </h1>
          <p>{t("results_description")}</p>
        </div>
        <button className="button secondary" disabled={saving} onClick={onEdit}>
          <Icon name="back" />
          {t("edit_answers")}
        </button>
      </div>
      <div className="match-hero">
        <div>
          <span className="light-eyebrow">
            <Icon name="spark" size={16} />
            {t("strongest_match")}
          </span>
          <h2>{result.recommended_career}</h2>
          <p>{t("match_hero_description")}</p>
        </div>
        <div className="match-score">
          <strong>
            {Math.round(result.confidence * 100)}
            <span>%</span>
          </strong>
          <span>{t("match_score")}</span>
        </div>
      </div>
      <div className="save-status" role="status">
        <Icon name={saved ? "check" : "shield"} size={17} />
        {t(
          saving
            ? "saving_assessment"
            : saved
              ? "assessment_saved"
              : "assessment_not_saved",
        )}
        {saved && (
          <Link to="/dashboard">
            {t("view_dashboard")} <Icon name="arrow" size={14} />
          </Link>
        )}
      </div>
      {saveError && (
        <div className="notice error" role="alert">
          <div>
            <strong>{t("save_failed")}</strong>
            <p>{saveError}</p>
          </div>
          <button
            className="button secondary"
            disabled={saving}
            onClick={onRetrySave}
          >
            {t("retry_save")}
          </button>
        </div>
      )}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">{t("keep_options_open")}</span>
            <h3>{t("career_matches")}</h3>
          </div>
          <span className="tag">{t("top_three")}</span>
        </div>
        <div className="match-grid">
          {result.top_3_predictions.map((prediction, index) => (
            <article
              className={`match-card ${index === 0 ? "is-best" : ""}`}
              key={prediction.career}
            >
              <span className="match-rank">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h4>{prediction.career}</h4>
              <div className="row-between">
                <span className="muted">{t("match_score")}</span>
                <strong className="numeric">
                  {(prediction.probability * 100).toFixed(1)}%
                </strong>
              </div>
              <div className="track" aria-hidden="true">
                <span style={{ width: `${prediction.probability * 100}%` }} />
              </div>
            </article>
          ))}
        </div>
        <p className="fine-print">{t("score_explanation")}</p>
      </section>
      <div className="results-grid">
        <section className="panel">
          <div className="panel-heading">
            <h3>{t("skills_to_develop")}</h3>
            <Icon name="chart" />
          </div>
          <SkillGaps gaps={result.skill_gap_analysis} />
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h3>{t("learning_priorities")}</h3>
            <Icon name="book" />
          </div>
          <LearningPriorities gaps={result.skill_gap_analysis} />
        </section>
      </div>
      {strengths.length > 0 && (
        <section className="strengths-panel">
          <div>
            <Icon name="shield" />
            <h3>{t("build_on_strengths")}</h3>
          </div>
          <p>{t("strengths_description")}</p>
          <div className="chip-list">
            {strengths.map((gap) => (
              <span className="strength-chip" key={gap.skill}>
                <Icon name="check" size={15} />
                {t(gap.skill.replaceAll(" ", "_"))}
              </span>
            ))}
          </div>
        </section>
      )}
      {result.explanation &&
        !result.explanation.startsWith(
          "LLM explanations are not available",
        ) && (
          <section className="panel">
            <h3>{t("ai_explanation")}</h3>
            <p className="explanation-copy">{result.explanation}</p>
          </section>
        )}
      {result.skill_decay_info && (
        <details className="panel decay-details">
          <summary>{t("recency_details")}</summary>
          <p>{t("recency_description")}</p>
          <ul>
            {Object.entries(result.skill_decay_info).map(([skill, info]) => (
              <li key={skill}>
                {t(skill)}: {info.original_level.toFixed(1)} →{" "}
                {info.decayed_level.toFixed(1)}
              </li>
            ))}
          </ul>
        </details>
      )}
      <div className="result-actions">
        {!saved && !saveError && (
          <button
            className="button secondary"
            disabled={saving}
            onClick={onRetrySave}
          >
            <Icon name="shield" />
            {t("save_to_dashboard")}
          </button>
        )}
        <button className="button secondary" onClick={exportResult}>
          <Icon name="download" />
          {t("download_results")}
        </button>
        <button
          className="button primary"
          disabled={saving}
          onClick={onRestart}
        >
          {t("new_assessment")}
          <Icon name="arrow" />
        </button>
      </div>
    </div>
  );
}
