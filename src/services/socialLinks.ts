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
let pendingRequest: Promise<SocialLink[]> | null = null;

async function requestSocialLinks(enabledOnly = true): Promise<SocialLink[]> {
	const apiUrl = getApiUrl();
	const query = enabledOnly ? "?enabled_only=true" : "";
	const response = await fetch(`${apiUrl}/social-links${query}`);
	const payload = await parseApiResponse<SocialLink[]>(response);
	return payload.data || [];
}

export async function fetchSocialLinks(enabledOnly = true): Promise<SocialLink[]> {
	if (cachedLinks && enabledOnly) {
		return cachedLinks.filter((link) => (link.enabled ? true : !enabledOnly));
	}

	if (pendingRequest) {
		return pendingRequest;
	}

	pendingRequest = requestSocialLinks(enabledOnly)
		.then((links) => {
			cachedLinks = links;
			return links;
		})
		.catch((error) => {
			console.warn("[SocialLinks] 获取失败：", error);
			return [];
		})
		.finally(() => {
			pendingRequest = null;
		});

	return pendingRequest;
}
