'use client';

import Link from 'next/link';
import { useTranslations } from 'next-intl';

export default function Footer() {
  const t = useTranslations('Footer');
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-600">
          <div>
            {t('copyright')} &copy; {new Date().getFullYear()}{' '}
            <Link
              href="https://bosseconbizchamps.org">
                BOSSEconBizChamps
            </Link>
          </div>
          <div className="flex gap-6">
            <Link
              href="https://github.com/perctrix/portfolio_manager"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-gray-900 transition-colors"
            >
              GitHub
            </Link>
            <Link
              href="https://github.com/perctrix/portfolio_manager/blob/main/LICENSE"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-gray-900 transition-colors"
            >
              Apache License 2.0
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
