import { type CollectionEntry, getCollection } from "astro:content";
import I18nKey from "@i18n/i18nKey";
import { i18n } from "@i18n/translation";
import { getCategoryUrl } from "@utils/url-utils";

// Retrieve posts and sort them by publication date
async function getRawSortedPosts() {
	const allBlogPosts = await getCollection("posts", ({ data }) => {
		return import.meta.env.PROD ? data.draft !== true : true;
	});

	// Fetch dynamic posts from backend API if available
	let dynamicPosts: any[] = [];
	try {
		const API_URL = import.meta.env.PUBLIC_API_URL;
		const res = await fetch(`${API_URL}/posts/?all=true`);
		if (res.ok) {
			const data = await res.json();
			dynamicPosts = data
				.map((p: any) => ({
					id: `dynamic-${p.slug}`,  // 使用 dynamic-slug 格式，以便与前端路由匹配
					data: {
						title: p.title,
						published: new Date(p.published_at),
						description: p.description,
						content: p.content,
						image: p.image,
						tags: p.tags,
						category: p.category,
						draft: p.is_draft,
						pinned: p.pinned || false,
						pin_order: p.pin_order || 0,
						has_password: p.has_password,
					},
				}))
				.filter((p: any) => (import.meta.env.PROD ? p.data.draft !== true : true));
		}
	} catch {
		// 静默处理 API 错误，使用静态文章
	}

	const mergedPosts = [...allBlogPosts, ...dynamicPosts];

	const sorted = mergedPosts.sort((a, b) => {
		// 首先按置顶状态排序，置顶文章在前
		if (a.data.pinned && !b.data.pinned) return -1;
		if (!a.data.pinned && b.data.pinned) return 1;

		// 如果都是置顶文章，按 pin_order 排序（数字越小越靠前）
		if (a.data.pinned && b.data.pinned) {
			const orderA = a.data.pin_order || 0;
			const orderB = b.data.pin_order || 0;
			if (orderA !== orderB) return orderA - orderB;
		}

		// 如果置顶状态相同，则按发布日期排序
		const dateA = new Date(a.data.published);
		const dateB = new Date(b.data.published);
		return dateA > dateB ? -1 : 1;
	});
	return sorted;
}

export async function getSortedPosts() {
	const sorted = await getRawSortedPosts();

	for (let i = 1; i < sorted.length; i++) {
		sorted[i].data.nextSlug = sorted[i - 1].id;
		sorted[i].data.nextTitle = sorted[i - 1].data.title;
	}
	for (let i = 0; i < sorted.length - 1; i++) {
		sorted[i].data.prevSlug = sorted[i + 1].id;
		sorted[i].data.prevTitle = sorted[i + 1].data.title;
	}

	return sorted;
}
export type PostForList = {
	id: string;
	data: CollectionEntry<"posts">["data"];
};
export async function getSortedPostsList(): Promise<PostForList[]> {
	const sortedFullPosts = await getRawSortedPosts();

	// delete post.body
	const sortedPostsList = sortedFullPosts.map((post) => ({
		id: post.id,
		data: post.data,
	}));

	return sortedPostsList;
}
export type Tag = {
	name: string;
	count: number;
};

export async function getTagList(): Promise<Tag[]> {
	const allPosts = await getRawSortedPosts();

	const countMap: { [key: string]: number } = {};
	allPosts.forEach((post: any) => {
		const tags = post.data.tags || [];
		tags.forEach((tag: string) => {
			if (!countMap[tag]) countMap[tag] = 0;
			countMap[tag]++;
		});
	});

	// sort tags
	const keys: string[] = Object.keys(countMap).sort((a, b) => {
		return a.toLowerCase().localeCompare(b.toLowerCase());
	});

	return keys.map((key) => ({ name: key, count: countMap[key] }));
}

export type Category = {
	name: string;
	count: number;
	url: string;
};

export async function getCategoryList(): Promise<Category[]> {
	const allPosts = await getRawSortedPosts();
	const count: { [key: string]: number } = {};
	allPosts.forEach((post: any) => {
		if (!post.data.category) {
			const ucKey = i18n(I18nKey.uncategorized);
			count[ucKey] = count[ucKey] ? count[ucKey] + 1 : 1;
			return;
		}

		const categoryName =
			typeof post.data.category === "string"
				? post.data.category.trim()
				: String(post.data.category).trim();

		count[categoryName] = count[categoryName] ? count[categoryName] + 1 : 1;
	});

	const lst = Object.keys(count).sort((a, b) => {
		return a.toLowerCase().localeCompare(b.toLowerCase());
	});

	const ret: Category[] = [];
	for (const c of lst) {
		ret.push({
			name: c,
			count: count[c],
			url: getCategoryUrl(c),
		});
	}
	return ret;
}
