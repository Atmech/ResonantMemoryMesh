import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

// Point outside knowmem-site to the repo's docs directory
const docsDirectory = path.join(process.cwd(), '../docs/handbook');

export type DocData = {
    slug: string;
    content: string;
    title: string;
    order: number;
};

export function getDocSlugs() {
    if (!fs.existsSync(docsDirectory)) return [];
    return fs.readdirSync(docsDirectory).filter((file) => file.endsWith('.md'));
}

export function getDocBySlug(slug: string): DocData | null {
    const realSlug = slug.replace(/\.md$/, '');

    // Handbooks are named with numbers e.g. "01-Introduction.md"
    // So we need to find the file that matches the suffix
    const files = getDocSlugs();
    const matchedFile = files.find((file) => file.toLowerCase().includes(realSlug.toLowerCase()));

    if (!matchedFile) {
        return null;
    }

    const fullPath = path.join(docsDirectory, matchedFile);
    const fileContents = fs.readFileSync(fullPath, 'utf8');

    // We are not using frontmatter currently in the MD files, but matter helps us 
    // safely extract content if we do in the future.
    const { data, content } = matter(fileContents);

    // Extract a title from the first heading if present
    let title = matchedFile.replace('.md', '').split('-').slice(1).join(' ');
    const titleMatch = content.match(/^#\s+(.*)/m);
    if (titleMatch) {
        title = titleMatch[1];
    }

    // Parse order from prefix (e.g. "01-...")
    const orderMatch = matchedFile.match(/^(\d+)-/);
    const order = orderMatch ? parseInt(orderMatch[1], 10) : 99;

    return {
        slug: realSlug,
        title,
        order,
        content,
        ...data,
    };
}

export function getAllDocs(): DocData[] {
    const slugs = getDocSlugs();
    const docs = slugs
        .map((slug) => getDocBySlug(slug))
        .filter((doc): doc is DocData => doc !== null)
        .sort((a, b) => a.order - b.order);
    return docs;
}
