import { defineMiddleware } from "astro:middleware";

/**
 * Astro 中间件
 * 处理尾部斜杠重定向，确保 URL 规范化
 */
export const onRequest = defineMiddleware(async (context, next) => {
  const { url } = context;
  const pathname = url.pathname;

  // 排除静态资源和 API 路径
  const excludedPaths = [
    "/_astro/",
    "/assets/",
    "/favicon",
    "/robots.txt",
    "/sitemap",
    "/rss",
    "/api/",
  ];

  const isExcluded = excludedPaths.some((path) => pathname.startsWith(path));

  // 如果路径以斜杠结尾（且不是根路径），重定向到无斜杠版本
  if (!isExcluded && pathname !== "/" && pathname.endsWith("/")) {
    const newPathname = pathname.slice(0, -1);
    const newUrl = new URL(newPathname + url.search, url.origin);
    return context.redirect(newUrl.toString(), 301);
  }

  // 继续处理请求
  return next();
});
