import { getApiUrl } from "@/utils/api-utils";
import { parseApiResponse } from "@/utils/api-response";

export type SocialLink = {
	id: string;
	name: string;
	icon: string;
	url: string;
	show_name: boolean;
	sort_order: number;
	enabled: boolean;
};

let cachedLinks: SocialLink[] | null = null;
let pendingRequest: Promise<SocialLink[] | null> | null = null;
let cacheTimestamp = 0;
const CACHE_TTL = 60 * 1000;

async function requestSocialLinks(enabledOnly = true): Promise<SocialLink[]> {
	const apiUrl = getApiUrl();
	const query = enabledOnly ? "?enabled_only=true" : "";
	const response = await fetch(`${apiUrl}/social-links${query}`);
	const payload = await parseApiResponse<SocialLink[]>(response);
	if (payload.code < 200 || payload.code >= 300) {
		throw new Error(payload.msg || "请求失败");
	}
	return payload.data || [];
}

export async function fetchSocialLinks(
	enabledOnly = true,
): Promise<SocialLink[] | null> {
	const isBrowser = typeof window !== "undefined";

	if (!isBrowser) {
		try {
			return await requestSocialLinks(enabledOnly);
		} catch (error) {
			console.warn("[SocialLinks] 获取失败：", error);
			return null;
		}
	}

	if (cachedLinks && enabledOnly && Date.now() - cacheTimestamp < CACHE_TTL) {
		return cachedLinks.filter((link) => (link.enabled ? true : !enabledOnly));
	}

	if (pendingRequest) {
		return pendingRequest;
	}

	pendingRequest = requestSocialLinks(enabledOnly)
		.then((links) => {
			cachedLinks = links;
			cacheTimestamp = Date.now();
			return links;
		})
		.catch((error) => {
			console.warn("[SocialLinks] 获取失败：", error);
			return null;
		})
		.finally(() => {
			pendingRequest = null;
		});

	return pendingRequest;
}
