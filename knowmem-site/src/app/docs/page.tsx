import { redirect } from 'next/navigation';
import { getAllDocs } from '@/lib/docs';

export default function DocsIndex() {
  const docs = getAllDocs();
  
  if (docs.length > 0) {
    redirect(`/docs/${docs[0].slug}`);
  }

  return (
    <div className="flex items-center justify-center p-24 text-gray-500">
      <p>Documentation is currently unavailable.</p>
    </div>
  );
}
