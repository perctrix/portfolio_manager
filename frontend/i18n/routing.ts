import { defineRouting } from 'next-intl/routing';
import { locales, defaultLocale } from './request';

export const routing = defineRouting({
  locales,
  defaultLocale,
  localePrefix: 'always'
});
