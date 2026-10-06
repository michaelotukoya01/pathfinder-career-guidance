import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api, getErrorMessage } from "./api";
import { validResult } from "./assessment";
import { SkillGaps, LearningPriorities } from "./Results";
import Icon from "./Icon";
import ProfileControls from "./ProfileControls";

export function processSkillProgress(assessments) {
  const progress = {};
  assessments.forEach((assessment) => {
    if (!Number.isFinite(Date.parse(assessment.timestamp))) return;
    (assessment.skill_gap_analysis || []).forEach((gap) => {
      if (!Number.isFinite(gap.user_level)) return;
      const skill = gap.skill.replaceAll(" ", "_");
      if (!progress[skill]) progress[skill] = [];
      progress[skill].push({
        date: new Date(assessment.timestamp),
        level: gap.user_level,
      });
    });
  });
  Object.values(progress).forEach((points) =>
    points.sort((a, b) => a.date - b.date),
  );
  return progress;
}

function ProgressChart({ progress }) {
  const { t, i18n } = useTranslation();
  const [selection, setSelection] = useState("skill_python");
  const keys = Object.keys(progress);
  const skill = keys.includes(selection) ? selection : keys[0];
  const points = (progress[skill] || []).slice(-8);
  const position = (point, index) => [
    points.length === 1 ? 290 : 36 + (index / (points.length - 1)) * 508,
    166 - (point.level / 5) * 140,
  ];
  return (
    <section className="panel progress-panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">{t("over_time")}</span>
          <h3>{t("skill_progress_title")}</h3>
        </div>
        {keys.length > 0 && (
          <select
            aria-label={t("choose_skill")}
            className="compact-select"
            value={skill}
            onChange={(event) => setSelection(event.target.value)}
          >
            {keys.map((key) => (
              <option value={key} key={key}>
                {t(key)}
              </option>
            ))}
          </select>
        )}
      </div>
      {points.length > 0 ? (
        <>
          <div className="chart-summary">
            <strong className="numeric">
              {points[points.length - 1].level.toFixed(1)}
              <small> / 5</small>
            </strong>
            <span>{t("latest_skill_level")}</span>
            <span className="tag">
              {t("observations", { count: points.length })}
            </span>
          </div>
          <svg
            className="progress-chart"
            viewBox="0 0 580 200"
            role="img"
            aria-label={t("skill_chart_label", { skill: t(skill) })}
          >
            {[0, 1, 2, 3, 4, 5].map((level) => (
              <g key={level}>
                <line
                  x1="36"
                  x2="544"
                  y1={166 - level * 28}
                  y2={166 - level * 28}
                  stroke="var(--line)"
                  strokeDasharray="4 5"
                />
                <text
                  x="12"
                  y={170 - level * 28}
                  fill="var(--muted)"
                  fontSize="11"
                >
                  {level}
                </text>
              </g>
            ))}
            <polyline
              points={points
                .map((point, index) => position(point, index).join(","))
                .join(" ")}
              fill="none"
              stroke="var(--accent)"
              strokeWidth="3"
              strokeLinejoin="round"
            />
            {points.map((point, index) => (
              <circle
                key={index}
                cx={position(point, index)[0]}
                cy={position(point, index)[1]}
                r="5"
                fill="var(--accent)"
                stroke="white"
                strokeWidth="2"
              >
                <title>
                  {point.date.toLocaleDateString(i18n.language)}:{" "}
                  {point.level.toFixed(1)}
                </title>
              </circle>
            ))}
          </svg>
          <div className="range-labels chart-dates">
            <span>{points[0].date.toLocaleDateString(i18n.language)}</span>
            <span>
              {points[points.length - 1].date.toLocaleDateString(i18n.language)}
            </span>
          </div>
          <p className="fine-print">
            {t(
              points.length === 1
                ? "one_assessment_chart"
                : "chart_recency_note",
            )}
          </p>
          <ol className="sr-only">
            {points.map((point, index) => (
              <li key={index}>
                {point.date.toLocaleDateString(i18n.language)}:{" "}
                {point.level.toFixed(1)}
              </li>
            ))}
          </ol>
        </>
      ) : (
        <p>{t("no_skill_data")}</p>
      )}
    </section>
  );
}

export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const [data, setData] = useState({ profile: null, assessments: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    api
      .getDashboard()
      .then((result) => {
        if (active)
          setData({
            ...result,
            assessments: (result.assessments || [])
              .filter(validResult)
              .sort(
                (a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp),
              ),
          });
      })
      .catch((failure) => {
        if (active) setError(getErrorMessage(failure));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [attempt]);

  const heading = (
    <div className="page-heading">
      <div>
        <span className="eyebrow">{t("your_workspace")}</span>
        <h1>{t("dashboard_headline")}</h1>
        <p>{t("dashboard_intro")}</p>
      </div>
      <Link className="button primary" to="/">
        {t("nav_home")}
        <Icon name="arrow" />
      </Link>
    </div>
  );
  if (loading)
    return (
      <div>
        {heading}
        <div className="panel loading-state" role="status">
          <span className="spinner" />
          <p>{t("loading_dashboard")}</p>
        </div>
      </div>
    );
  if (error)
    return (
      <div>
        {heading}
        <div className="panel empty-state">
          <span className="empty-icon">
            <Icon name="refresh" size={32} />
          </span>
          <h2>{t("error_loading_dashboard")}</h2>
          <p role="alert">{error}</p>
          <button
            className="button primary"
            onClick={() => setAttempt((value) => value + 1)}
          >
            {t("try_again")}
          </button>
        </div>
        <ProfileControls onChange={() => setAttempt((value) => value + 1)} />
      </div>
    );
  const { assessments } = data;
  const latest = assessments[0];
  const progress = processSkillProgress(assessments);
  const date = (value) =>
    Number.isFinite(Date.parse(value))
      ? new Date(value).toLocaleDateString(i18n.language, {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : t("date_unavailable");
  const onTrack =
    latest?.skill_gap_analysis.filter((gap) => gap.gap <= 0).length || 0;
  return (
    <div className="dashboard-page">
      {heading}
      {!latest ? (
        <div className="panel empty-state">
          <span className="empty-icon">
            <Icon name="compass" size={38} />
          </span>
          <span className="eyebrow">{t("start_here")}</span>
          <h2>{t("empty_dashboard_title")}</h2>
          <p>{t("no_assessments_yet")}</p>
          <Link className="button primary" to="/">
            {t("start_assessment")}
            <Icon name="arrow" />
          </Link>
          <div className="empty-benefits">
            <span>
              <Icon name="target" size={17} />
              {t("personal_matches")}
            </span>
            <span>
              <Icon name="chart" size={17} />
              {t("track_growth")}
            </span>
            <span>
              <Icon name="book" size={17} />
              {t("clear_next_steps")}
            </span>
          </div>
        </div>
      ) : (
        <>
          <div className="stats-grid">
            <article className="stat-card featured-stat">
              <span>
                <Icon name="compass" />
                {t("latest_match")}
              </span>
              <h2>{latest.recommended_career}</h2>
              <p>
                {t("match_percentage", {
                  score: (latest.confidence * 100).toFixed(1),
                })}
              </p>
            </article>
            <article className="stat-card">
              <span>
                <Icon name="assessment" />
                {t("total_assessments")}
              </span>
              <strong className="stat-number">{assessments.length}</strong>
              <p>{t("latest_date", { date: date(latest.timestamp) })}</p>
            </article>
            <article className="stat-card">
              <span>
                <Icon name="target" />
                {t("skills_on_target")}
              </span>
              <strong className="stat-number">
                {onTrack}
                <small> / {latest.skill_gap_analysis.length}</small>
              </strong>
              <p>{t("skills_target_description")}</p>
            </article>
          </div>
          <div className="dashboard-grid">
            <ProgressChart progress={progress} />
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <span className="eyebrow">{t("your_next_steps")}</span>
                  <h3>{t("learning_priorities")}</h3>
                </div>
                <Icon name="book" />
              </div>
              <LearningPriorities gaps={latest.skill_gap_analysis} />
            </section>
          </div>
          <div className="dashboard-grid">
            <section className="panel">
              <div className="panel-heading">
                <h3>{t("skills_to_develop")}</h3>
                <span className="tag">{t("latest_assessment")}</span>
              </div>
              <SkillGaps gaps={latest.skill_gap_analysis} />
            </section>
            <section className="panel history-panel">
              <div className="panel-heading">
                <h3>{t("assessment_history")}</h3>
                <span className="count-badge">{assessments.length}</span>
              </div>
              <div className="history-list">
                {assessments.map((assessment, index) => (
                  <details
                    className="history-entry"
                    key={assessment.id || `${assessment.timestamp}-${index}`}
                  >
                    <summary>
                      <span className="history-marker">
                        <Icon name="compass" size={17} />
                      </span>
                      <span>
                        <strong>{assessment.recommended_career}</strong>
                        <small>{date(assessment.timestamp)}</small>
                      </span>
                      <span className="history-score numeric">
                        {(assessment.confidence * 100).toFixed(1)}%
                      </span>
                      <span className="history-chevron" aria-hidden="true">
                        +
                      </span>
                    </summary>
                    <div className="history-detail">
                      <h4>{t("career_matches")}</h4>
                      <ul>
                        {assessment.top_3_predictions.map((prediction) => (
                          <li key={prediction.career}>
                            <span>{prediction.career}</span>
                            <strong className="numeric">
                              {(prediction.probability * 100).toFixed(1)}%
                            </strong>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </details>
                ))}
              </div>
            </section>
          </div>
        </>
      )}
      <ProfileControls
        hasProfile={Boolean(data.profile)}
        onChange={() => setAttempt((value) => value + 1)}
      />
    </div>
  );
}
