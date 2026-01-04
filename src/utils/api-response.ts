export interface ApiResponse<T> {
	code: number;
	msg: string;
	data: T;
}

export function isApiResponse<T>(payload: any): payload is ApiResponse<T> {
	return (
		payload &&
		typeof payload === "object" &&
		"code" in payload &&
		"msg" in payload &&
		"data" in payload
	);
}

export async function parseApiResponse<T>(
	response: Response,
): Promise<ApiResponse<T>> {
	let payload: any = null;
	try {
		payload = await response.json();
	} catch {
		payload = null;
	}

	if (isApiResponse<T>(payload)) {
		return payload;
	}

	const msg =
		payload && typeof payload === "object"
			? payload.msg || payload.message || payload.detail
			: null;

	return {
		code: response.status,
		msg: msg || (response.ok ? "操作成功" : "请求失败"),
		data: payload as T,
	};
}

export async function fetchApiData<T>(
	input: RequestInfo | URL,
	init?: RequestInit,
): Promise<ApiResponse<T>> {
	const response = await fetch(input, init);
	return parseApiResponse<T>(response);
}
