import { useState } from "react";
import { useTranslation } from "react-i18next";
import { api, getErrorMessage } from "./api";
import Icon from "./Icon";

export default function ProfileControls({ onChange, hasProfile = false }) {
  const { t } = useTranslation();
  const [mode, setMode] = useState(null);
  const [profileId, setProfileId] = useState(() => {
    try {
      return localStorage.getItem("career-profile-id") || "";
    } catch {
      return "";
    }
  });
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const perform = async (action) => {
    setBusy(true);
    setError(null);
    try {
      await action();
      setMode(null);
      setToken("");
      onChange();
    } catch (failure) {
      setError(getErrorMessage(failure));
    } finally {
      setBusy(false);
    }
  };
  const exportAccess = () => {
    try {
      const id = localStorage.getItem("career-profile-id");
      const accessToken = localStorage.getItem("career-profile-token");
      if (!id || !accessToken) throw new Error(t("missing_access"));
      const url = URL.createObjectURL(
        new Blob(
          [
            JSON.stringify(
              { profile_id: id, access_token: accessToken },
              null,
              2,
            ),
          ],
          { type: "application/json" },
        ),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = "pathfinder-private-access.json";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (failure) {
      setError(getErrorMessage(failure));
    }
  };
  return (
    <section className="panel profile-controls">
      <div className="panel-heading">
        <div>
          <h3>{t("your_data")}</h3>
          <p>{t("device_access_description")}</p>
        </div>
        <Icon name="shield" />
      </div>
      <div className="profile-actions">
        <button
          className="button secondary"
          disabled={busy}
          onClick={() => setMode(mode === "restore" ? null : "restore")}
        >
          {t("restore_access")}
        </button>
        {hasProfile && (
          <button
            className="button secondary"
            disabled={busy}
            onClick={exportAccess}
          >
            <Icon name="download" />
            {t("download_access")}
          </button>
        )}
        <button
          className="text-button"
          disabled={busy}
          onClick={() => setMode("disconnect")}
        >
          {t("new_private_history")}
        </button>
        {hasProfile && (
          <button
            className="text-button danger-text"
            disabled={busy}
            onClick={() => setMode("delete")}
          >
            {t("delete_history")}
          </button>
        )}
      </div>
      {mode === "restore" && (
        <form
          className="access-form"
          onSubmit={(event) => {
            event.preventDefault();
            perform(() => api.restoreProfile(profileId, token));
          }}
        >
          <p>{t("restore_access_help")}</p>
          <div className="background-grid">
            <div className="field">
              <label htmlFor="restore-profile-id">{t("profile_id")}</label>
              <input
                id="restore-profile-id"
                required
                value={profileId}
                onChange={(event) => setProfileId(event.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="field">
              <label htmlFor="restore-token">{t("access_code")}</label>
              <input
                id="restore-token"
                type="password"
                required
                value={token}
                onChange={(event) => setToken(event.target.value)}
                autoComplete="off"
              />
            </div>
          </div>
          <button className="button primary" disabled={busy}>
            {t(busy ? "working" : "restore_access")}
          </button>
        </form>
      )}
      {(mode === "delete" || mode === "disconnect") && (
        <div className="notice">
          <div>
            <strong>
              {t(
                mode === "delete"
                  ? "delete_history_confirm"
                  : "disconnect_confirm",
              )}
            </strong>
            <p>
              {t(
                mode === "delete"
                  ? "delete_history_detail"
                  : "disconnect_detail",
              )}
            </p>
          </div>
          <div className="profile-actions">
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => setMode(null)}
            >
              {t("cancel")}
            </button>
            <button
              className="button primary"
              disabled={busy}
              onClick={() =>
                perform(
                  mode === "delete"
                    ? api.deleteProfile
                    : api.startPrivateHistory,
                )
              }
            >
              {t(busy ? "working" : "confirm")}
            </button>
          </div>
        </div>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
    </section>
  );
}
