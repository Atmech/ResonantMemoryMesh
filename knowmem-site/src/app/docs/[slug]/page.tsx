import { getDocBySlug, getAllDocs } from '@/lib/docs';
import { notFound } from 'next/navigation';
import { MDXRemote } from 'next-mdx-remote/rsc';
import remarkGfm from 'remark-gfm';

// Optional: Custom components for MDX (styling code blocks, links, etc.)
const components = {
  h1: (props: any) => <h1 className="text-4xl font-bold mb-6 font-display" {...props} />,
  h2: (props: any) => <h2 className="text-2xl font-semibold mt-12 mb-4" {...props} />,
  h3: (props: any) => <h3 className="text-xl font-medium mt-8 mb-3" {...props} />,
  p: (props: any) => <p className="text-gray-700 dark:text-gray-300 mb-4 leading-relaxed" {...props} />,
  ul: (props: any) => <ul className="list-disc pl-6 mb-4 space-y-2 text-gray-700 dark:text-gray-300" {...props} />,
  ol: (props: any) => <ol className="list-decimal pl-6 mb-4 space-y-2 text-gray-700 dark:text-gray-300" {...props} />,
  li: (props: any) => <li className="" {...props} />,
  a: (props: any) => <a className="text-blue-600 hover:text-blue-800 underline decoration-blue-300 underline-offset-2" {...props} />,
  blockquote: (props: any) => (
    <blockquote className="border-l-4 border-gray-300 pl-4 italic my-6 text-gray-600 dark:text-gray-400" {...props} />
  ),
  pre: (props: any) => (
    <pre className="bg-gray-100 dark:bg-gray-900 rounded-lg p-4 overflow-x-auto my-6 border border-gray-200 dark:border-gray-800" {...props} />
  ),
  code: (props: any) => (
    <code className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded font-mono text-sm" {...props} />
  ),
};

export async function generateStaticParams() {
  const docs = getAllDocs();
  return docs.map((doc) => ({
    slug: doc.slug,
  }));
}

export default async function DocPage(props: { params: Promise<{ slug: string }> }) {
  const params = await props.params;
  const doc = getDocBySlug(params.slug);

  if (!doc) {
    notFound();
  }

  return (
    <article className="prose prose-slate dark:prose-invert max-w-none">
      <MDXRemote 
        source={doc.content} 
        components={components}
        options={{
          mdxOptions: {
            remarkPlugins: [remarkGfm],
          }
        }}
      />
    </article>
  );
}
