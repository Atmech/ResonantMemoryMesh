import { getAllDocs } from '@/lib/docs';
import Link from 'next/link';

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const docs = getAllDocs();

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      {/* Sidebar Navigation */}
      <aside className="w-full md:w-64 border-r border-gray-200 dark:border-gray-800 p-6 flex-shrink-0">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
          Handbook
        </h2>
        <nav className="space-y-1">
          {docs.map((doc) => (
            <Link
              key={doc.slug}
              href={`/docs/${doc.slug}`}
              className="block py-2 text-sm text-gray-700 dark:text-gray-300 hover:text-black dark:hover:text-white transition-colors"
            >
              {doc.order}. {doc.title}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-6 md:p-12 lg:p-24 max-w-4xl">
        {children}
      </main>
    </div>
  );
}
