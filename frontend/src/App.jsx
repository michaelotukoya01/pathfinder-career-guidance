import React, { useEffect, useRef } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Link,
  useLocation,
} from "react-router-dom";
import { useTranslation } from "react-i18next";
import CareerForm from "./CareerForm";
import Dashboard from "./Dashboard";
import Icon from "./Icon";
import { writeLocal } from "./storage";
import "./App.css";

function FailureScreen() {
  const { t } = useTranslation();
  return (
    <div className="panel empty-state">
      <Icon name="refresh" size={36} />
      <h1>{t("unexpected_error")}</h1>
      <p>{t("unexpected_error_help")}</p>
      <button
        className="button primary"
        onClick={() => window.location.reload()}
      >
        {t("reload_page")}
      </button>
    </div>
  );
}
class ErrorBoundary extends React.Component {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? <FailureScreen /> : this.props.children;
  }
}
function Guide() {
  const { t } = useTranslation();
  return (
    <div className="guide-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">{t("made_for_exploration")}</span>
          <h1>{t("guide_headline")}</h1>
          <p>{t("guide_intro")}</p>
        </div>
      </div>
      <div className="guide-grid">
        {["assessment", "compass", "chart"].map((icon, index) => (
          <section className="panel guide-card" key={icon}>
            <span className="guide-icon">
              <Icon name={icon} size={26} />
            </span>
            <span className="eyebrow">0{index + 1}</span>
            <h2>{t(`guide_${index + 1}_title`)}</h2>
            <p>{t(`guide_${index + 1}_body`)}</p>
          </section>
        ))}
      </div>
      <section className="panel guide-notes">
        <h2>{t("things_to_know")}</h2>
        {["scores", "recency", "privacy", "limitations"].map((topic) => (
          <details key={topic}>
            <summary>{t(`guide_${topic}_title`)}</summary>
            <p>{t(`guide_${topic}_body`)}</p>
          </details>
        ))}
      </section>
      <div className="guide-cta">
        <div>
          <h2>{t("ready_to_explore")}</h2>
          <p>{t("your_own_pace")}</p>
        </div>
        <Link to="/" className="button primary">
          {t("start_assessment")}
          <Icon name="arrow" />
        </Link>
      </div>
    </div>
  );
}
function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="panel empty-state">
      <span className="eyebrow">404</span>
      <h1>{t("page_not_found")}</h1>
      <p>{t("page_not_found_help")}</p>
      <Link to="/" className="button primary">
        {t("back_to_assessment")}
        <Icon name="arrow" />
      </Link>
    </div>
  );
}
function Workspace() {
  const { t, i18n } = useTranslation();
  const { pathname } = useLocation();
  const mainRef = useRef(null);
  const language = i18n.resolvedLanguage === "es" ? "es" : "en";
  const page =
    pathname === "/dashboard"
      ? "nav_dashboard"
      : pathname === "/guide"
        ? "how_it_works"
        : "nav_home";
  useEffect(() => {
    document.documentElement.lang = language;
    document.title = `${t(page)} | Pathfinder`;
  }, [language, page, t]);
  useEffect(() => {
    mainRef.current?.focus({ preventScroll: true });
  }, [pathname]);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        {t("skip_to_content")}
      </a>
      <aside className="sidebar">
        <Link className="brand" to="/" aria-label={t("brand_home")}>
          <span className="brand-mark">
            <Icon name="compass" size={27} />
          </span>
          <span>
            Pathfinder<small>{t("brand_subtitle")}</small>
          </span>
        </Link>
        <span className="nav-caption">{t("workspace")}</span>
        <nav aria-label={t("main_navigation")} className="main-nav">
          {[
            ["/", "assessment", "nav_home"],
            ["/dashboard", "dashboard", "nav_dashboard"],
            ["/guide", "book", "how_it_works"],
          ].map(([path, icon, label]) => (
            <NavLink
              key={path}
              to={path}
              end={path === "/"}
              className={({ isActive }) =>
                `nav-item${isActive ? " active" : ""}`
              }
            >
              <Icon name={icon} />
              <span>{t(label)}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="note-symbol">
            <Icon name="spark" size={25} />
          </span>
          <h2>{t("sidebar_note_title")}</h2>
          <p>{t("sidebar_note_body")}</p>
          <Link to="/guide">
            {t("learn_how")}
            <Icon name="arrow" size={15} />
          </Link>
        </div>
        <div className="sidebar-footer">
          <span className="small-mark">
            <Icon name="compass" size={16} />
          </span>
          <span>{t("thoughtful_guidance")}</span>
        </div>
      </aside>
      <div className="workspace-body">
        <header className="topbar">
          <div className="breadcrumb">
            <span>{t("workspace")}</span>
            <span aria-hidden="true">/</span>
            <strong>{t(page)}</strong>
          </div>
          <div className="language-control">
            <Icon name="globe" size={17} />
            <label className="sr-only" htmlFor="language">
              {t("language")}
            </label>
            <select
              id="language"
              value={language}
              onChange={(event) => {
                i18n.changeLanguage(event.target.value);
                writeLocal("career-language", event.target.value);
              }}
            >
              <option value="en">English</option>
              <option value="es">Español</option>
            </select>
          </div>
        </header>
        <main id="main-content" ref={mainRef} tabIndex="-1">
          <ErrorBoundary key={pathname}>
            <Routes>
              <Route path="/" element={<CareerForm />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/guide" element={<Guide />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </ErrorBoundary>
        </main>
        <footer className="workspace-footer">
          <span>Pathfinder</span>
          <p>{t("footer_note")}</p>
          <Link to="/guide">
            {t("how_it_works")}
            <Icon name="arrow" size={13} />
          </Link>
        </footer>
      </div>
    </div>
  );
}
export default function App() {
  return (
    <BrowserRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Workspace />
    </BrowserRouter>
  );
}
