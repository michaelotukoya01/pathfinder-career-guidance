import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// Import translation files
import enTranslation from "./i18n/en.json";
import esTranslation from "./i18n/es.json";
import { readLocal } from "./storage";

// Translation resources
const resources = {
  en: {
    translation: enTranslation,
  },
  es: {
    translation: esTranslation,
  },
};

i18n
  .use(initReactI18next) // passes i18n down to react-i18next
  .init({
    resources,
    lng: readLocal("career-language") === "es" ? "es" : "en",
    fallbackLng: "en", // use when translation is missing
    interpolation: {
      escapeValue: false, // react already safes from xss
    },
  });

export default i18n;
