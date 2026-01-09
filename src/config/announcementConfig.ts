import type { AnnouncementConfig } from "../types/config";

export const announcementConfig: AnnouncementConfig = {
	// 公告标题
	title: "公告",

	// 公告内容
	content: "欢迎来到我的博客！这是一则示例公告。",

	// 是否允许用户关闭公告
	closable: true,

	link: {
		enable: true, // 启用链接
		text: "了解更多", // 链接文本
		url: "/about", // 链接 URL
		external: false, // 内部链接
	},
};
