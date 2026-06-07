import React, { createContext, useContext, useEffect, useState } from 'react';
import en from './locales/en.json';
import ar from './locales/ar.json';

const I18nContext = createContext();

export const useI18n = () => useContext(I18nContext);

const translationsMap = { en, ar };

export const I18nProvider = ({ children }) => {
  const [locale, setLocale] = useState(() => {
    return localStorage.getItem('moshtari-locale') || 'en';
  });

  const dir = locale === 'ar' ? 'rtl' : 'ltr';

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = dir;
    document.documentElement.setAttribute('data-locale', locale);
    document.title = locale === 'ar' ? 'مشتري - توقعات الطلب' : 'Moshtari - Demand Forecast';
    localStorage.setItem('moshtari-locale', locale);
  }, [locale, dir]);

  const t = (key, params = {}) => {
    const translations = translationsMap[locale] || en;
    let str = translations[key];
    if (str === undefined) {
      str = en[key];
      if (str === undefined) str = key;
    }
    for (const [k, v] of Object.entries(params)) {
      str = str.replace(new RegExp(`\\{\\{${k}\\}\\}`, 'g'), v);
    }
    return str;
  };

  return (
    <I18nContext.Provider value={{ locale, setLocale, dir, t }}>
      {children}
    </I18nContext.Provider>
  );
};
