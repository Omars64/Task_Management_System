import React, { createContext, useContext, useMemo, useState } from 'react';
import en from './locales/en.json';

const I18nContext = createContext({ t: (k) => k, locale: 'en', setLocale: () => {} });

const LOCALES = {
  en,
};

export function I18nProvider({ children, defaultLocale = 'en' }) {
  const [locale, setLocale] = useState(defaultLocale);
  const dict = LOCALES[locale] || en;
  const t = useMemo(() => {
    return (key, vars) => {
      let str = dict[key] || key;
      if (vars && typeof vars === 'object') {
        Object.entries(vars).forEach(([k, v]) => {
          str = str.replace(new RegExp(`{${k}}`, 'g'), String(v));
        });
      }
      return str;
    };
  }, [dict]);

  const value = useMemo(() => ({ t, locale, setLocale }), [t, locale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}


