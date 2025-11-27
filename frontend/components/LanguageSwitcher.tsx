'use client';

import { useLocale } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { locales } from '@/i18n/request';

export default function LanguageSwitcher() {
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  const handleChange = (newLocale: string) => {
    // Remove current locale from pathname and add new one
    const segments = pathname.split('/');
    segments[1] = newLocale;
    const newPath = segments.join('/');
    router.push(newPath);
  };

  return (
    <select
      value={locale}
      onChange={(e) => handleChange(e.target.value)}
      className="bg-white border border-gray-300 rounded-lg px-3 py-1.5 text-sm text-gray-900 shadow-sm hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
    >
      {locales.map((loc) => (
        <option key={loc} value={loc}>
          {loc === 'en' ? 'English' : '中文'}
        </option>
      ))}
    </select>
  );
}
