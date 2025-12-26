import type { APIContext } from "astro";
import { getSortedPosts } from "@/utils/content-utils";
import { getPostUrlBySlug } from "@/utils/url-utils";
import { siteConfig } from "@/config";
import { fetchSiteSettings } from "@/services/siteSettings";

export const prerender = false;

export async function GET(context: APIContext) {
  if (!context.site) {
    throw new Error("site not set");
  }

  const siteUrl = context.site.toString().replace(/\/$/, "");

  // 获取动态配置
  let dynamicSettings: Record<string, any> = {};
  try {
    dynamicSettings = await fetchSiteSettings();
  } catch {
    // 使用静态配置
  }

  // 获取所有已发布的文章
  const posts = await getSortedPosts();
  const publishedPosts = posts.filter(p => !p.data.draft);

  // 获取所有分类和标签
  const categories = new Set<string>();
  const tags = new Set<string>();

  for (const post of publishedPosts) {
    if (post.data.category) {
      categories.add(post.data.category);
    }
    if (post.data.tags) {
      for (const tag of post.data.tags) {
        tags.add(tag);
      }
    }
  }

  // 构建 Sitemap XML
  const urls: string[] = [];

  // 首页
  urls.push(`
  <url>
    <loc>${siteUrl}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>`);

  // 归档页
  urls.push(`
  <url>
    <loc>${siteUrl}/archive</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>`);

  // 友链页
  const featureFriends = dynamicSettings.feature_friends ?? true;
  if (featureFriends) {
    urls.push(`
  <url>
    <loc>${siteUrl}/friends</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>`);
  }

  // RSS 页
  const featureRss = dynamicSettings.feature_rss ?? true;
  if (featureRss) {
    urls.push(`
  <url>
    <loc>${siteUrl}/rss</loc>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>`);
  }

  // 赞助页
  const pageSponsor = dynamicSettings.page_sponsor ?? siteConfig.pages?.sponsor;
  if (pageSponsor) {
    urls.push(`
  <url>
    <loc>${siteUrl}/sponsor</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>`);
  }

  // 留言板
  const pageGuestbook = dynamicSettings.page_guestbook ?? siteConfig.pages?.guestbook;
  if (pageGuestbook) {
    urls.push(`
  <url>
    <loc>${siteUrl}/guestbook</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>`);
  }

  // 追番页
  const pageBangumi = dynamicSettings.page_bangumi ?? siteConfig.pages?.bangumi;
  if (pageBangumi) {
    urls.push(`
  <url>
    <loc>${siteUrl}/bangumi</loc>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>`);
  }

  // 文章页面
  for (const post of publishedPosts) {
    const postUrl = getPostUrlBySlug(post.id);
    const lastmod = post.data.updated || post.data.published;
    const lastmodStr = lastmod ? `
    <lastmod>${lastmod.toISOString().split('T')[0]}</lastmod>` : '';

    urls.push(`
  <url>
    <loc>${siteUrl}${postUrl}</loc>${lastmodStr}
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>`);
  }

  // 分类页面
  for (const category of categories) {
    const categorySlug = encodeURIComponent(category.toLowerCase().replace(/\s+/g, '-'));
    urls.push(`
  <url>
    <loc>${siteUrl}/category/${categorySlug}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>`);
  }

  // 标签页面
  for (const tag of tags) {
    const tagSlug = encodeURIComponent(tag.toLowerCase().replace(/\s+/g, '-'));
    urls.push(`
  <url>
    <loc>${siteUrl}/tag/${tagSlug}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>`);
  }

  // 分页页面（假设每页10篇文章）
  const postsPerPage = dynamicSettings.post_per_page || siteConfig.pagination?.postsPerPage || 10;
  const totalPages = Math.ceil(publishedPosts.length / postsPerPage);

  for (let i = 2; i <= totalPages; i++) {
    urls.push(`
  <url>
    <loc>${siteUrl}/${i}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>`);
  }

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
${urls.join('')}
</urlset>`;

  return new Response(sitemap, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}
