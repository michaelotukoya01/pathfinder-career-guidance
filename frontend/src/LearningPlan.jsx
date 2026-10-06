import { useState } from "react";
import { useTranslation } from "react-i18next";
import { readLocal, writeLocal } from "./storage";
import { learningResources } from "./learningResources";

const KEY = "career-learning-progress-v1";
export default function LearningPlan({ skill }) {
  const { t } = useTranslation();
  const [completed, setCompleted] = useState(() => readLocal(KEY, {}) || {});
  const [canStore, setCanStore] = useState(true);
  const normalized = skill.replaceAll(" ", "_");
  const resource = learningResources[normalized];
  const toggle = (step) => {
    const latest = readLocal(KEY, {}) || {};
    const next = {
      ...latest,
      [`${normalized}:${step}`]: !completed[`${normalized}:${step}`],
    };
    setCompleted(next);
    setCanStore(writeLocal(KEY, next));
  };
  return (
    <details className="learning-plan">
      <summary>{t("open_learning_plan")}</summary>
      <p className="project-brief">
        <strong>{t("practice_project")}</strong>
        {t(`project_${normalized}`)}
      </p>
      {resource && (
        <a href={resource[1]} target="_blank" rel="noopener noreferrer">
          {resource[0]} <span className="sr-only">{t("opens_new_tab")}</span>
        </a>
      )}
      <ul className="milestone-list">
        {["learn", "build", "reflect"].map((step) => (
          <li key={step}>
            <label>
              <input
                type="checkbox"
                checked={Boolean(completed[`${normalized}:${step}`])}
                onChange={() => toggle(step)}
              />
              <span>{t(`milestone_${step}`)}</span>
            </label>
          </li>
        ))}
      </ul>
      <p className="fine-print" role="status">
        {t(canStore ? "milestones_local" : "draft_session_only")}
      </p>
    </details>
  );
}
