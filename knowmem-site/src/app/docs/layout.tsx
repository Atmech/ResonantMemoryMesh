import { Navbar } from "@/components/navbar";
import { DocsSidebar } from "@/components/docs/sidebar";

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <div className="flex-1 relative flex">
        <DocsSidebar />
        <main className="flex-1 md:pl-72 w-full transition-all duration-300">
          <div className="mx-auto w-full max-w-4xl px-4 py-8 md:px-8 md:py-12 lg:py-16">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
