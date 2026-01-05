/*
 Navicat Premium Dump SQL

 Source Server         : 本地数据库
 Source Server Type    : MySQL
 Source Server Version : 80027 (8.0.27)
 Source Host           : localhost:3306
 Source Schema         : firefly_cms

 Target Server Type    : MySQL
 Target Server Version : 80027 (8.0.27)
 File Encoding         : 65001

 Date: 27/12/2025 18:57:31
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for access_logs
-- ----------------------------
DROP TABLE IF EXISTS `access_logs`;
CREATE TABLE `access_logs`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '日志ID(UUID)',
  `log_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '日志类型(login_success/login_failed/api_access)',
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '用户名',
  `ip_address` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'IP地址',
  `user_agent` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '客户端User-Agent',
  `request_path` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '请求路径',
  `request_method` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '请求方法',
  `status_code` int NULL DEFAULT NULL COMMENT '响应状态码',
  `detail` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '详细信息',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_access_logs_request_path`(`request_path` ASC) USING BTREE,
  INDEX `ix_access_logs_created_at`(`created_at` ASC) USING BTREE,
  INDEX `ix_access_logs_log_type`(`log_type` ASC) USING BTREE,
  INDEX `ix_access_logs_username`(`username` ASC) USING BTREE,
  INDEX `ix_access_logs_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '访问日志表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for admins
-- ----------------------------
DROP TABLE IF EXISTS `admins`;
CREATE TABLE `admins`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '管理员ID(UUID)',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '登录用户名',
  `hashed_password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码哈希值(PBKDF2)',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_admins_username`(`username` ASC) USING BTREE,
  INDEX `ix_admins_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '管理员账户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of admins
-- ----------------------------
INSERT INTO `admins` VALUES ('edb6b049-1fd2-4975-8493-554aa344e84a', 'admin', '$pbkdf2-sha256$29000$m1MK4ZxzDsH4/1.r9d67tw$hrwyBl5Rq3CCJAVe2Y.kolAOp0sPHy3BPaCFn9dyn8A');

-- ----------------------------
-- Table structure for categories
-- ----------------------------
DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '分类ID(UUID)',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '分类名称',
  `slug` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '分类URL别名',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '分类描述',
  `icon` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '分类图标(iconify格式)',
  `color` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '分类颜色(HEX)',
  `sort_order` int NULL DEFAULT NULL COMMENT '排序权重(越大越靠前)',
  `enabled` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_categories_name`(`name` ASC) USING BTREE,
  UNIQUE INDEX `ix_categories_slug`(`slug` ASC) USING BTREE,
  INDEX `ix_categories_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文章分类表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of categories
-- ----------------------------
INSERT INTO `categories` VALUES ('010c5a5b-2b06-44a1-9cf0-37957ed578e7', '', NULL, NULL, NULL, NULL, 0, 1, '2025-12-27 10:02:58');
INSERT INTO `categories` VALUES ('2c55fab7-8585-4246-b3e2-f7de29fbe768', '博客指南', 'blog-guide', 'Firefly 博客使用指南和教程', NULL, '#10b981', 0, 1, '2025-12-26 02:51:50');
INSERT INTO `categories` VALUES ('35690f3e-50bb-4220-b2b3-2cc3a966bf86', 'General', NULL, NULL, NULL, NULL, 0, 1, '2025-12-27 10:03:16');
INSERT INTO `categories` VALUES ('cacebf06-dd14-4163-8bbe-5fb227699f08', '文章示例', 'article-examples', '各种 Markdown 和功能演示文章', NULL, '#3b82f6', 0, 1, '2025-12-26 02:51:50');

-- ----------------------------
-- Table structure for friend_links
-- ----------------------------
DROP TABLE IF EXISTS `friend_links`;
CREATE TABLE `friend_links`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '链接ID(UUID)',
  `title` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '网站名称',
  `url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '网站URL',
  `avatar` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '网站头像/Logo URL',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '网站描述',
  `tags` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '标签(逗号分隔)',
  `weight` int NULL DEFAULT NULL COMMENT '排序权重(越大越靠前)',
  `enabled` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_friend_links_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '友情链接表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of friend_links
-- ----------------------------
INSERT INTO `friend_links` VALUES ('01ce528a-116b-450d-9977-32d7920f3f6f', 'Astro', 'https://github.com/withastro/astro', 'https://avatars.githubusercontent.com/u/44914786?v=4&s=640', 'The web framework for content-driven websites. ⭐️ Star to support our work!', 'Framework', 8, 1, '2025-12-26 02:02:09', '2025-12-26 02:02:09');
INSERT INTO `friend_links` VALUES ('078ed53c-3b7c-43af-af39-6308c62d1c81', 'Firefly Docs', 'https://docs-firefly.cuteleaf.cn', 'https://docs-firefly.cuteleaf.cn/logo.png', 'Firefly主题模板文档', 'Docs', 9, 1, '2025-12-26 02:02:09', '2025-12-26 02:02:09');
INSERT INTO `friend_links` VALUES ('1e6fa62e-a5e9-4fc8-a8bf-68a73ac4b5e5', '夏夜流萤', 'https://blog.cuteleaf.cn', 'https://q1.qlogo.cn/g?b=qq&nk=7618557&s=640', '飞萤之火自无梦的长夜亮起，绽放在终竟的明天。', 'Blog', 10, 1, '2025-12-26 02:02:09', '2025-12-26 04:24:31');

-- ----------------------------
-- Table structure for post_tags
-- ----------------------------
DROP TABLE IF EXISTS `post_tags`;
CREATE TABLE `post_tags`  (
  `post_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章ID',
  `tag_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '标签ID',
  PRIMARY KEY (`post_id`, `tag_id`) USING BTREE,
  INDEX `tag_id`(`tag_id` ASC) USING BTREE,
  CONSTRAINT `post_tags_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `post_tags_ibfk_2` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文章标签关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of post_tags
-- ----------------------------
INSERT INTO `post_tags` VALUES ('1d94856a-8630-471d-b247-43fa7a020f8c', '22fe616a-8ff0-4e77-81bf-9ed54491c409');
INSERT INTO `post_tags` VALUES ('3c5eb044-4674-46b2-b22e-64b08ed27cde', '22fe616a-8ff0-4e77-81bf-9ed54491c409');
INSERT INTO `post_tags` VALUES ('5a14bb22-50f6-4f40-b16f-6af621b43e07', '22fe616a-8ff0-4e77-81bf-9ed54491c409');
INSERT INTO `post_tags` VALUES ('64bbf6e0-599e-432d-9537-1ace8489698b', '22fe616a-8ff0-4e77-81bf-9ed54491c409');
INSERT INTO `post_tags` VALUES ('7e58d199-93c8-41cb-8c58-2d2fc411cc93', '22fe616a-8ff0-4e77-81bf-9ed54491c409');
INSERT INTO `post_tags` VALUES ('9135c2c9-0214-4fe2-83a4-14017915c261', '22fe616a-8ff0-4e77-81bf-9ed54491c409');
INSERT INTO `post_tags` VALUES ('a79f576d-93fb-457e-ba5c-54db9f1591da', '22fe616a-8ff0-4e77-81bf-9ed54491c409');
INSERT INTO `post_tags` VALUES ('7e58d199-93c8-41cb-8c58-2d2fc411cc93', '4f71863e-965a-4984-b3ab-23b5ad560368');
INSERT INTO `post_tags` VALUES ('1d94856a-8630-471d-b247-43fa7a020f8c', '533c99b3-1bec-4ade-b5a9-70d3dccb8762');
INSERT INTO `post_tags` VALUES ('9135c2c9-0214-4fe2-83a4-14017915c261', '533c99b3-1bec-4ade-b5a9-70d3dccb8762');
INSERT INTO `post_tags` VALUES ('7e58d199-93c8-41cb-8c58-2d2fc411cc93', '5ba00411-b644-412d-9e58-eb3cbca2ab03');
INSERT INTO `post_tags` VALUES ('1d94856a-8630-471d-b247-43fa7a020f8c', '5cb9bb81-6109-4973-8fcd-2e466b1105ba');
INSERT INTO `post_tags` VALUES ('3c5eb044-4674-46b2-b22e-64b08ed27cde', '5cb9bb81-6109-4973-8fcd-2e466b1105ba');
INSERT INTO `post_tags` VALUES ('5a14bb22-50f6-4f40-b16f-6af621b43e07', '5cb9bb81-6109-4973-8fcd-2e466b1105ba');
INSERT INTO `post_tags` VALUES ('64bbf6e0-599e-432d-9537-1ace8489698b', '5cb9bb81-6109-4973-8fcd-2e466b1105ba');
INSERT INTO `post_tags` VALUES ('7e58d199-93c8-41cb-8c58-2d2fc411cc93', '5cb9bb81-6109-4973-8fcd-2e466b1105ba');
INSERT INTO `post_tags` VALUES ('272c5420-6301-4451-86cb-feee40e98af2', '62a4f14a-90c1-4eec-9250-5d08ee6f68b3');
INSERT INTO `post_tags` VALUES ('3c5eb044-4674-46b2-b22e-64b08ed27cde', '62a4f14a-90c1-4eec-9250-5d08ee6f68b3');
INSERT INTO `post_tags` VALUES ('484d1966-533a-4a8b-b8a8-fc8d002e844f', '62a4f14a-90c1-4eec-9250-5d08ee6f68b3');
INSERT INTO `post_tags` VALUES ('a79f576d-93fb-457e-ba5c-54db9f1591da', '62a4f14a-90c1-4eec-9250-5d08ee6f68b3');
INSERT INTO `post_tags` VALUES ('9135c2c9-0214-4fe2-83a4-14017915c261', '8dc71448-a83e-4364-924e-d9d4b9ca30eb');
INSERT INTO `post_tags` VALUES ('a79f576d-93fb-457e-ba5c-54db9f1591da', '9756ca46-88b4-458a-b502-d356c05af42e');
INSERT INTO `post_tags` VALUES ('5a14bb22-50f6-4f40-b16f-6af621b43e07', '9934decd-a5dc-44fd-93a7-bf01814c75cb');
INSERT INTO `post_tags` VALUES ('7e58d199-93c8-41cb-8c58-2d2fc411cc93', 'bbd812ac-e7c5-444c-895a-5ca6dc5e4607');
INSERT INTO `post_tags` VALUES ('1d94856a-8630-471d-b247-43fa7a020f8c', 'c3f8996d-93f8-497b-86d7-2592ce198c36');
INSERT INTO `post_tags` VALUES ('5a14bb22-50f6-4f40-b16f-6af621b43e07', 'c3f8996d-93f8-497b-86d7-2592ce198c36');
INSERT INTO `post_tags` VALUES ('7e58d199-93c8-41cb-8c58-2d2fc411cc93', 'c3f8996d-93f8-497b-86d7-2592ce198c36');
INSERT INTO `post_tags` VALUES ('9135c2c9-0214-4fe2-83a4-14017915c261', 'c3f8996d-93f8-497b-86d7-2592ce198c36');
INSERT INTO `post_tags` VALUES ('484d1966-533a-4a8b-b8a8-fc8d002e844f', 'd762bcde-dc4b-4d17-b00c-e7de2983bedc');
INSERT INTO `post_tags` VALUES ('3c5eb044-4674-46b2-b22e-64b08ed27cde', 'eb53689f-54c6-4281-8731-b259727d94ff');
INSERT INTO `post_tags` VALUES ('484d1966-533a-4a8b-b8a8-fc8d002e844f', 'ed23ec0c-35a2-43c2-b150-16858cdcfedf');

-- ----------------------------
-- Table structure for posts
-- ----------------------------
DROP TABLE IF EXISTS `posts`;
CREATE TABLE `posts`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章唯一标识(UUID)',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章标题',
  `slug` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章URL别名',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '文章摘要描述',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章正文内容(Markdown)',
  `image` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文章封面图片URL',
  `published_at` datetime NULL DEFAULT NULL COMMENT '发布时间',
  `category_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属分类ID',
  `is_draft` int NULL DEFAULT NULL COMMENT '是否为草稿(0:否, 1:是)',
  `pinned` tinyint(1) NULL DEFAULT NULL COMMENT '是否置顶',
  `pin_order` int NULL DEFAULT NULL COMMENT '置顶排序(数字越小越靠前)',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文章访问密码(明文,可选)',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'draft' COMMENT '发布状态(draft/published/scheduled)',
  `scheduled_at` datetime NULL DEFAULT NULL COMMENT '定时发布时间',
  `autosave_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '自动保存内容(JSON)',
  `autosave_at` datetime NULL DEFAULT NULL COMMENT '自动保存时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '最后更新时间',
  `deleted_at` datetime NULL DEFAULT NULL COMMENT '软删除时间(NULL表示未删除)',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_posts_slug`(`slug` ASC) USING BTREE,
  INDEX `category_id`(`category_id` ASC) USING BTREE,
  INDEX `ix_posts_title`(`title` ASC) USING BTREE,
  INDEX `ix_posts_id`(`id` ASC) USING BTREE,
  INDEX `ix_posts_pinned`(`pinned` ASC) USING BTREE,
  INDEX `ix_posts_pin_order`(`pin_order` ASC) USING BTREE,
  INDEX `ix_posts_status`(`status` ASC) USING BTREE,
  INDEX `ix_posts_scheduled_at`(`scheduled_at` ASC) USING BTREE,
  INDEX `ix_posts_deleted_at`(`deleted_at` ASC) USING BTREE,
  CONSTRAINT `posts_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文章表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of posts
-- ----------------------------
INSERT INTO `posts` VALUES ('00000000-0000-0000-0000-000000000001', '关于我', 'about', '关于本站和博主的介绍', '# 关于我 / About Me\n\n你好！我是 **夏叶** ，一个在数字世界中默默无闻的一片叶子。\n\n## 🛠️ 关于本站\n\n这个网站使用 **Astro** 框架构建，采用了 [Firefly](https://github.com/CuteLeaf/Firefly) 模板，Firefly 是基于 [Fuwari](https://github.com/saicaca/fuwari) 的二次开发。\n\n**Firefly** 是一款基于 Astro 框架和 Fuwari 模板开发的清新美观且现代化个人博客主题模板，专为技术爱好者和内容创作者设计。该主题融合了现代 Web 技术栈，提供了丰富的功能模块和高度可定制的界面，让您能够轻松打造出专业且美观的个人博客网站。\n\n**🖥️在线预览： [Firefly - Demo site](https://firefly.cuteleaf.cn/)**\n\n**🏠我的博客： [https://blog.cuteleaf.cn](https://blog.cuteleaf.cn/)**\n\n**📝Firefly使用文档： [https://docs-firefly.cuteleaf.cn](https://docs-firefly.cuteleaf.cn/)**\n\n**⭐Firefly开源地址：[https://github.com/CuteLeaf/Firefly](https://github.com/CuteLeaf/Firefly)**\n\n**⭐Fuwari开源地址：[https://github.com/saicaca/fuwari](https://github.com/saicaca/fuwari)**\n\n::github{repo=\"CuteLeaf/Firefly\"}\n\n::github{repo=\"saicaca/fuwari\"}\n\n## 📫 联系方式\n\n如果你想和我交流技术问题，分享有趣的想法，或者只是想打个招呼，欢迎通过以下方式联系我：\n\n- 💻 **GitHub**: [CuteLeaf](https://github.com/CuteLeaf)\n- ✉️ **Email**: [xiaye@msn.com](mailto:xiaye@msn.com)\n\n---\n\n*感谢你的来访！希望在这里能找到对你有用的内容！*\n', NULL, '2025-01-01 00:00:00', '35690f3e-50bb-4220-b2b3-2cc3a966bf86', 0, 0, 0, NULL, '2025-12-27 10:03:16', NULL, NULL, NULL, NULL, NULL);
INSERT INTO `posts` VALUES ('1d94856a-8630-471d-b247-43fa7a020f8c', 'Firefly 简单使用指南', 'firefly-guide', '如何使用 Firefly 博客模板。', '这个博客模板是基于 [Astro](https://astro.build/) 构建的。对于本指南中未提及的内容，您可以在 [Astro 文档](https://docs.astro.build/) 中找到答案。\n\n## 文章的 Front-matter\n\n```yaml\n---\ntitle: 我的第一篇博客文章\npublished: 2023-09-09\ndescription: 这是我新 Astro 博客的第一篇文章。\nimage: ./cover.jpg\ntags: [前端, 开发]\ncategory: 前端开发\ndraft: false\n---\n```\n\n| 属性 | 描述 |\n|------|------|\n| `title` | 文章标题。 |\n| `published` | 文章发布日期。 |\n| `pinned` | 是否将此文章置顶在文章列表顶部。 |\n| `description` | 文章的简短描述。显示在首页上。 |\n| `image` | 文章封面图片路径。 |\n| `tags` | 文章标签。 |\n| `category` | 文章分类。 |\n| `draft` | 如果这篇文章仍是草稿，则不会显示。 |\n| `slug` | 自定义文章 URL 路径。 |\n\n## 文章文件的放置位置\n\n您的文章文件应放置在 `src/content/posts/` 目录中。您也可以创建子目录来更好地组织您的文章和资源。\n\n```\nsrc/content/posts/\n├── post-1.md\n└── post-2/\n    ├── cover.png\n    └── index.md\n```\n\n## 自定义文章 URL (Slug)\n\n### 什么是 Slug？\n\nSlug 是文章 URL 路径的自定义部分。如果不设置 slug，系统将使用文件名作为 URL。\n\n### Slug 使用建议\n\n1. **使用英文和连字符**：`my-awesome-post` 而不是 `my awesome post`\n2. **保持简洁**：避免过长的 slug\n3. **具有描述性**：让 URL 能够反映文章内容\n4. **避免特殊字符**：只使用字母、数字和连字符\n', NULL, '2025-01-02 00:00:00', '2c55fab7-8585-4246-b3e2-f7de29fbe768', 0, 1, 0, NULL, '2025-12-26 03:13:54', NULL, NULL, NULL, NULL);
INSERT INTO `posts` VALUES ('272c5420-6301-4451-86cb-feee40e98af2', '测试加密', 'test', '', '加密内容\n', NULL, '2025-12-26 05:17:36', 'cacebf06-dd14-4163-8bbe-5fb227699f08', 0, 1, 0, 'dear7575', '2025-12-26 06:37:49', NULL, NULL, NULL, NULL);
INSERT INTO `posts` VALUES ('3c5eb044-4674-46b2-b22e-64b08ed27cde', 'Markdown 扩展功能', 'markdown-extended', '了解 Firefly 中的 Markdown 功能', '## GitHub 仓库卡片\n\n您可以添加链接到 GitHub 仓库的动态卡片，在页面加载时，仓库信息会从 GitHub API 获取。\n\n::github{repo=\"CuteLeaf/Firefly\"}\n\n使用代码 `::github{repo=\"CuteLeaf/Firefly\"}` 创建 GitHub 仓库卡片。\n\n## 提醒框\n\n支持以下类型的提醒框：`note` `tip` `important` `warning` `caution`\n\n:::note\n突出显示用户应该考虑的信息，即使在快速浏览时也是如此。\n:::\n\n:::tip\n可选信息，帮助用户更成功。\n:::\n\n:::important\n用户成功所必需的关键信息。\n:::\n\n:::warning\n由于潜在风险需要用户立即注意的关键内容。\n:::\n\n:::caution\n行动的负面潜在后果。\n:::\n\n### 基本语法\n\n```markdown\n:::note\n这是一个提示信息。\n:::\n```\n\n## 折叠块\n\n您可以创建可折叠的内容块：\n\n:::collapse{title=\"点击展开更多内容\"}\n这里是隐藏的详细内容，点击标题即可展开或收起。\n:::\n', NULL, '2025-01-01 00:00:00', 'cacebf06-dd14-4163-8bbe-5fb227699f08', 0, 0, 0, NULL, '2025-12-26 02:53:54', NULL, NULL, NULL, NULL);
INSERT INTO `posts` VALUES ('484d1966-533a-4a8b-b8a8-fc8d002e844f', 'KaTeX 数学公式示例', 'katex-math-example', '展示 Firefly 主题对 KaTeX 数学公式的支持，包括行内公式、块级公式和复杂数学符号。', '本文展示了 [Firefly](https://github.com/CuteLeaf/Firefly) 主题对 KaTeX 数学公式的渲染支持。\n\n## 行内公式 (Inline)\n\n行内公式使用单个 `$` 符号包裹。\n\n例如：欧拉公式 $e^{i\\pi} + 1 = 0$ 是数学中最优美的公式之一。\n\n质能方程 $E = mc^2$ 也是家喻户晓。\n\n## 块级公式 (Block)\n\n块级公式使用两个 `$$` 符号包裹，会居中显示。\n\n$$\n\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}\n$$\n\n$$\nx = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}\n$$\n\n## 复杂示例\n\n### 矩阵 (Matrices)\n\n$$\n\\begin{pmatrix}\na & b \\\\\nc & d\n\\end{pmatrix}\n\\begin{pmatrix}\n\\alpha & \\beta \\\\\n\\gamma & \\delta\n\\end{pmatrix} =\n\\begin{pmatrix}\na\\alpha + b\\gamma & a\\beta + b\\delta \\\\\nc\\alpha + d\\gamma & c\\beta + d\\delta\n\\end{pmatrix}\n$$\n\n### 求和与积分\n\n$$\n\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}\n$$\n', NULL, '2025-01-01 00:00:00', 'cacebf06-dd14-4163-8bbe-5fb227699f08', 0, 0, 0, NULL, '2025-12-26 02:53:54', NULL, NULL, NULL, NULL);
INSERT INTO `posts` VALUES ('5a14bb22-50f6-4f40-b16f-6af621b43e07', 'Markdown Mermaid 图表', 'markdown-mermaid', '一个包含 Mermaid 的 Markdown 博客文章简单示例。', '# Markdown 中 Mermaid 图表完整指南\n\n本文演示如何在 Markdown 文档中使用 Mermaid 创建各种复杂图表，包括流程图、时序图、甘特图、类图和状态图。\n\n## 流程图示例\n\n流程图非常适合表示流程或算法步骤。\n\n```mermaid\ngraph TD\n    A[开始] --> B{条件检查}\n    B -->|是| C[处理步骤 1]\n    B -->|否| D[处理步骤 2]\n    C --> E[结束]\n    D --> E\n```\n\n## 时序图示例\n\n时序图显示对象之间随时间的交互。\n\n```mermaid\nsequenceDiagram\n    participant User as 用户\n    participant Server as 服务器\n    participant Database as 数据库\n\n    User->>Server: 发送请求\n    Server->>Database: 查询数据\n    Database-->>Server: 返回结果\n    Server-->>User: 响应数据\n```\n\n## 甘特图示例\n\n```mermaid\ngantt\n    title 项目开发计划\n    dateFormat  YYYY-MM-DD\n    section 设计阶段\n    需求分析    :a1, 2024-01-01, 7d\n    UI设计      :a2, after a1, 5d\n    section 开发阶段\n    前端开发    :b1, after a2, 14d\n    后端开发    :b2, after a2, 14d\n```\n', NULL, '2025-01-01 00:00:00', 'cacebf06-dd14-4163-8bbe-5fb227699f08', 0, 0, 0, NULL, '2025-12-26 02:53:54', NULL, NULL, NULL, NULL);
INSERT INTO `posts` VALUES ('64bbf6e0-599e-432d-9537-1ace8489698b', 'Firefly 代码块示例', 'code-examples', '在Firefly中使用表达性代码的代码块在 Markdown 中的外观。', '在这里，我们将探索如何使用 [Expressive Code](https://expressive-code.com/) 展示代码块。\n\n## 表达性代码\n\n### 语法高亮\n\n#### 常规语法高亮\n\n```js\nconsole.log(\'此代码有语法高亮!\')\n```\n\n```python\ndef hello_world():\n    print(\"Hello, World!\")\n    return True\n\nif __name__ == \"__main__\":\n    hello_world()\n```\n\n### 代码编辑器框架\n\n```js title=\"my-script.js\"\nconsole.log(\'Hello World!\')\n```\n\n### 终端框架\n\n```bash\nnpm install astro\n```\n\n### 行高亮与标记\n\n```js {1, 4-5}\nconsole.log(\'行 1 被高亮\')\nconsole.log(\'行 2\')\nconsole.log(\'行 3\')\nconsole.log(\'行 4 被高亮\')\nconsole.log(\'行 5 被高亮\')\n```\n\n### 差异对比\n\n```js\nfunction greet(name) {\n-  return \"Hello, \" + name;\n+  return `Hello, ${name}!`;\n}\n```\n', NULL, '2025-01-02 00:00:00', 'cacebf06-dd14-4163-8bbe-5fb227699f08', 0, 0, 0, NULL, '2025-12-26 03:13:56', NULL, NULL, NULL, NULL);
INSERT INTO `posts` VALUES ('7e58d199-93c8-41cb-8c58-2d2fc411cc93', 'Firefly 一款清新美观的 Astro 博客主题模板', 'firefly-intro', 'Firefly 是一款基于 Astro 框架和 Fuwari 模板开发的清新美观且现代化个人博客主题模板，专为技术爱好者和内容创作者设计。', '## 🌟 项目概述\n\n**Firefly** 是一款基于 Astro 框架和 Fuwari 模板开发的清新美观且现代化个人博客主题模板，专为技术爱好者和内容创作者设计。该主题融合了现代 Web 技术栈，提供了丰富的功能模块和高度可定制的界面，让您能够轻松打造出专业且美观的个人博客网站。\n\n**🖥️在线预览： [Firefly - Demo site](https://firefly.cuteleaf.cn/)**\n\n**🏠我的博客： [https://blog.cuteleaf.cn](https://blog.cuteleaf.cn/)**\n\n**📝Firefly使用文档： [https://docs-firefly.cuteleaf.cn](https://docs-firefly.cuteleaf.cn/)**\n\n**⭐Firefly开源地址：[https://github.com/CuteLeaf/Firefly](https://github.com/CuteLeaf/Firefly)**\n\n::github{repo=\"CuteLeaf/Firefly\"}\n\n## 🚀 技术架构\n\n- **静态站点生成**: 基于 Astro ，提供极快的加载速度和优秀的 SEO 优化\n- **TypeScript 支持**: 完整的类型安全，提升开发体验和代码质量\n- **响应式设计**: 使用 Tailwind CSS 构建，完美适配桌面端和移动端\n- **组件化开发**: 支持 Astro、Svelte 组件，灵活可扩展\n\n## 📖 配置说明\n\n> 📚 **详细配置文档**: 查看 [Firefly使用文档](https://docs-firefly.cuteleaf.cn/) 获取完整的配置指南\n\n## ✨ 主要特性\n\n- 🎨 精美的视觉设计与流畅的动画效果\n- 📱 响应式布局，完美适配各种设备\n- 🔍 内置搜索功能\n- 📊 代码高亮与 Markdown 扩展支持\n- 🏷️ 标签与分类系统\n- 📅 归档页面\n- 🌙 深色模式支持\n- 💬 评论系统集成\n- 📈 SEO 优化\n', NULL, '2025-01-02 00:00:00', 'cacebf06-dd14-4163-8bbe-5fb227699f08', 0, 1, 0, NULL, '2025-12-26 02:53:54', NULL, NULL, NULL, NULL);
INSERT INTO `posts` VALUES ('9135c2c9-0214-4fe2-83a4-14017915c261', 'Firefly 布局系统详解', 'firefly-layout-system', '深入了解 Firefly 的布局系统，包括侧边栏布局和文章列表布局。', '## 📖 概述\n\nFirefly 提供了灵活的布局系统，允许您根据内容需求和个人喜好自定义博客的视觉呈现方式。布局系统主要包括**侧边栏布局**和**文章列表布局**两个维度。\n\n## 一、侧边栏布局系统\n\n侧边栏是博客页面的重要组成部分，用于展示导航、分类、标签、统计信息等辅助内容。\n\n### 1.1 左侧边栏模式\n\n- 侧边栏固定在页面左侧\n- 主内容区域位于右侧\n- 符合从左到右的阅读习惯\n\n### 1.2 双侧边栏模式\n\n- 左侧和右侧各有一个侧边栏\n- 主内容区域居中\n- 提供更丰富的信息展示空间\n\n## 二、文章列表布局\n\n### 2.1 列表模式 (List)\n\n- 单列布局，文章垂直排列\n- 每篇文章占据完整宽度\n- 适合长描述和详细预览\n\n### 2.2 网格模式 (Grid)\n\n- 双列布局，文章并排显示\n- 每篇文章占据一半宽度\n- 适合封面图片展示\n\n## 三、布局配置\n\n```typescript\n// src/config/sidebarConfig.ts\nexport const sidebarLayoutConfig = {\n  enable: true,\n  position: \"left\", // \"left\" 或 \"both\"\n};\n```\n\n```typescript\n// src/config/siteConfig.ts\nexport const siteConfig = {\n  postListLayout: {\n    defaultMode: \"list\", // \"list\" 或 \"grid\"\n    allowSwitch: true,\n  },\n};\n```\n', NULL, '2025-01-02 00:00:00', '2c55fab7-8585-4246-b3e2-f7de29fbe768', 0, 0, 0, NULL, '2025-12-26 02:53:54');
INSERT INTO `posts` VALUES ('a79f576d-93fb-457e-ba5c-54db9f1591da', '在文章中嵌入视频', 'embed-video', '这篇文章演示如何在博客文章中嵌入视频。', '只需从 YouTube 或其他平台复制嵌入代码，然后将其粘贴到 markdown 文件中。\n\n## 嵌入代码示例\n\n```yaml\n---\ntitle: 在文章中嵌入视频\npublished: 2023-10-19\n---\n\n<iframe width=\"100%\" height=\"468\" src=\"https://www.youtube.com/embed/VIDEO_ID\" frameborder=\"0\" allowfullscreen></iframe>\n```\n\n## YouTube\n\n您可以直接嵌入 YouTube 视频，只需复制嵌入代码即可。\n\n## Bilibili\n\n同样支持 Bilibili 视频嵌入：\n\n```html\n<iframe width=\"100%\" height=\"468\" src=\"//player.bilibili.com/player.html?bvid=VIDEO_ID&p=1&autoplay=0\" scrolling=\"no\" border=\"0\" frameborder=\"no\" framespacing=\"0\" allowfullscreen=\"true\"></iframe>\n```\n\n## 提示\n\n- 建议设置 `width=\"100%\"` 以适应不同屏幕尺寸\n- 设置合适的高度，如 `height=\"468\"`\n- 添加 `allowfullscreen` 属性支持全屏播放\n', NULL, '2025-01-01 00:00:00', 'cacebf06-dd14-4163-8bbe-5fb227699f08', 0, 0, 0, NULL, '2025-12-26 02:53:54');

-- ----------------------------
-- Table structure for post_revisions
-- ----------------------------
DROP TABLE IF EXISTS `post_revisions`;
CREATE TABLE `post_revisions`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '版本ID(UUID)',
  `post_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章ID',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '版本标题',
  `slug` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '版本Slug',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '版本摘要',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '版本内容',
  `editor` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '编辑者用户名',
  `created_at` datetime NULL DEFAULT NULL COMMENT '版本创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_post_revisions_post_id`(`post_id` ASC) USING BTREE,
  CONSTRAINT `post_revisions_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文章版本历史' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for media_files
-- ----------------------------
DROP TABLE IF EXISTS `media_files`;
CREATE TABLE `media_files`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '媒体ID(UUID)',
  `filename` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '存储文件名',
  `original_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '原始文件名',
  `mime_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件类型',
  `size` int NULL DEFAULT 0 COMMENT '文件大小(字节)',
  `url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '访问URL',
  `path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '服务器路径',
  `uploader` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '上传者',
  `width` int NULL DEFAULT NULL COMMENT '图片宽度',
  `height` int NULL DEFAULT NULL COMMENT '图片高度',
  `usage_count` int NULL DEFAULT 0 COMMENT '引用次数',
  `created_at` datetime NULL DEFAULT NULL COMMENT '上传时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_media_files_filename`(`filename` ASC) USING BTREE,
  INDEX `ix_media_files_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '媒体文件元数据' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for post_media
-- ----------------------------
DROP TABLE IF EXISTS `post_media`;
CREATE TABLE `post_media`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '关联ID',
  `post_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章ID',
  `media_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '媒体ID',
  `context` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '使用场景',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_post_media_post_id`(`post_id` ASC) USING BTREE,
  INDEX `ix_post_media_media_id`(`media_id` ASC) USING BTREE,
  CONSTRAINT `post_media_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `post_media_ibfk_2` FOREIGN KEY (`media_id`) REFERENCES `media_files` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文章与媒体文件关联' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for post_view_stats
-- ----------------------------
DROP TABLE IF EXISTS `post_view_stats`;
CREATE TABLE `post_view_stats`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '统计ID',
  `post_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章ID',
  `date` date NOT NULL COMMENT '统计日期',
  `views` int NULL DEFAULT 0 COMMENT '浏览次数',
  `unique_views` int NULL DEFAULT 0 COMMENT '访客数',
  `created_at` datetime NULL DEFAULT NULL COMMENT '记录创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_post_view_stats_post_id`(`post_id` ASC) USING BTREE,
  INDEX `ix_post_view_stats_date`(`date` ASC) USING BTREE,
  CONSTRAINT `post_view_stats_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文章访问统计表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for post_view_clients
-- ----------------------------
DROP TABLE IF EXISTS `post_view_clients`;
CREATE TABLE `post_view_clients`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '记录ID',
  `post_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文章ID',
  `date` date NOT NULL COMMENT '日期',
  `client_hash` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '客户端哈希',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_post_client_date`(`post_id` ASC, `date` ASC, `client_hash` ASC) USING BTREE,
  INDEX `ix_post_view_clients_client_hash`(`client_hash` ASC) USING BTREE,
  CONSTRAINT `post_view_clients_ibfk_1` FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文章访问客户端记录' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for site_settings
-- ----------------------------
DROP TABLE IF EXISTS `site_settings`;
CREATE TABLE `site_settings`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '设置ID(UUID)',
  `key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '设置键名',
  `value` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '设置值',
  `type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '值类型(string/number/boolean/json)',
  `group` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '设置分组',
  `label` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '显示标签',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '设置描述',
  `sort_order` int NULL DEFAULT NULL COMMENT '排序权重',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_site_settings_key`(`key` ASC) USING BTREE,
  INDEX `ix_site_settings_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '站点设置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of site_settings
-- ----------------------------
INSERT INTO `site_settings` VALUES ('01f1ab77-ab67-4b29-b78a-fcc3c0e0daf8', 'feature_comment', 'true', 'boolean', 'feature', '评论功能', '是否启用评论功能', 100, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('0518c90e-d40a-479b-9b6f-bf60e4be8b6b', 'footer_icp', '', 'string', 'footer', 'ICP备案号', '网站ICP备案号', 100, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('08c2922a-bc53-4b77-ae52-19b498883b5a', 'feature_friends', 'true', 'boolean', 'feature', '友链页面', '是否启用友链页面', 96, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('08e7eb8b-12eb-4533-8f25-519727b51878', 'profile_name', '北港不夏', 'string', 'profile', '昵称', '显示在侧边栏的昵称', 99, '2025-12-26 04:29:32');
INSERT INTO `site_settings` VALUES ('0e0c5200-2fc3-4a45-9867-1f52cac5e497', 'waves_mobile_enable', 'true', 'boolean', 'waves', '移动端波浪', '移动端是否启用波浪动画', 99, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('12fefc77-aa25-45a5-96d5-76a30058f5f6', 'brand_navbar_title', '北港不夏', 'string', 'brand', '导航栏标题', '导航栏显示的标题', 97, '2025-12-26 04:37:34');
INSERT INTO `site_settings` VALUES ('145af7fc-0ece-4461-8897-b003765fdd8c', 'banner_text_enable', 'true', 'boolean', 'banner', '显示横幅文字', '是否显示横幅主标题', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('14911610-57c9-4360-b810-8aa079d00d58', 'banner_subtitle', '[\"In Reddened Chrysalis, I Once Rest\",\"From Shattered Sky, I Free Fall\",\"Amidst Silenced Stars, I Deep Sleep\",\"Upon Lighted Fyrefly, I Soon Gaze\",\"From Undreamt Night, I Thence Shine\",\"In Finalized Morrow, I Full Bloom\"]', 'json', 'banner', '横幅副标题', '副标题列表(JSON数组)', 98, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('171cb989-6eb7-44a3-b50a-81497cc93ee9', 'page_sponsor', 'true', 'boolean', 'page', '赞助页面', '是否启用赞助页面', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('1dd64443-af3f-4a35-8bc2-c0df2437d377', 'wallpaper_position', '0% 20%', 'string', 'wallpaper', '图片位置', 'Banner模式图片位置', 96, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('1e7f8707-ea61-4583-b5e0-874bfcd69f30', 'banner_credit_desktop_enable', 'true', 'boolean', 'banner', '桌面端显示来源', '桌面端是否显示图片来源', 90, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('227abbf2-7c94-4e34-bc7b-d20ce64980ec', 'announcement_title', '公告', 'string', 'announcement', 'Title', NULL, 0, '2025-12-27 09:50:08');
INSERT INTO `site_settings` VALUES ('25df22af-fd91-40f3-94c8-461698d9abc1', 'site_lang', 'zh_CN', 'string', 'basic', '站点语言', '网站的默认语言', 95, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('b1c2d3e4-f5a6-4b7c-8d9e-0f1a2b3c4d5e', 'brand_navbar_layout', 'space-between', 'string', 'brand', '导航栏布局', 'left=左对齐, center=居中, space-between=两端对齐', 95, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('32851742-3b78-4f68-bc50-4870a28eb967', 'brand_navbar_width_full', 'false', 'boolean', 'brand', '导航栏全宽', NULL, 94, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('39aef70b-67e4-4fa6-a498-726ac90daaf4', 'brand_logo', '/assets/images/LiuYingPure3.svg', 'string', 'brand', '网站Logo', '导航栏Logo图片URL', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('3be93de2-027e-4209-9417-04b36fbcbfe2', 'wallpaper_mode', 'banner', 'string', 'wallpaper', '壁纸模式', '壁纸模式: banner/overlay/none', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('439db07e-1902-45d3-8842-46500a94cf7e', 'footer_custom_html', '', 'text', 'footer', '自定义HTML', '页脚自定义HTML内容', 96, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('44cc51de-c720-41b3-8954-5a82c95ec561', 'theme_hue', '165', 'number', 'theme', '主题色相', '主题颜色的色相值(0-360)', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('45615e2c-5cde-43b1-b72d-67d6f47eab97', 'theme_default_mode', 'system', 'string', 'theme', '默认主题模式', '默认主题模式: light/dark/system', 98, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('47e2e164-f460-46df-9e37-d94901e76d86', 'announcement_link_enable', 'True', 'boolean', 'announcement', 'Link Enable', NULL, 0, '2025-12-27 09:50:08');
INSERT INTO `site_settings` VALUES ('4a10f535-72eb-41ea-8365-f2cfffcde9ca', 'profile_bio', 'Hello, I`m 北港不夏.', 'text', 'profile', '个人签名', '个人简介或签名', 98, '2025-12-26 04:29:39');
INSERT INTO `site_settings` VALUES ('4ae48bb4-47d9-4157-b8c4-f81e61f51c99', 'banner_credit_desktop_url', 'https://www.pixiv.net/artworks/135490046', 'string', 'banner', '桌面端来源链接', '桌面端艺术品链接', 86, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('4b0569c6-2469-4a9f-b14b-bbb731c50343', 'site_title', '北港不夏', 'string', 'basic', '站点标题', '网站的主标题', 100, '2025-12-26 04:29:00');
INSERT INTO `site_settings` VALUES ('4beded86-68ba-4efc-bf2c-dc8fb4d1c9f0', 'banner_credit_mobile_text', 'Pixiv - KiraraShss', 'string', 'banner', '移动端来源文本', '移动端图片来源文本', 87, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('4f11164a-7af8-44bb-b909-682426888a49', 'brand_favicon', '/assets/images/favicon.ico', 'string', 'brand', '网站图标', '浏览器标签页图标', 98, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('50521eb4-5fc3-466a-a590-504597df55c3', 'site_url', 'https://firefly.cuteleaf.cn', 'string', 'basic', '站点URL', '网站的完整URL地址', 98, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('67e0c4e2-bb1c-40d9-af7a-d335a95a268e', 'wallpaper_mobile', '/assets/images/m1.webp', 'string', 'wallpaper', '移动壁纸', '移动端背景图片', 97, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('6e9ae577-bd02-4a8c-ac78-e5e7f4a58374', 'bangumi_user_id', '1163581', 'string', 'bangumi', 'Bangumi用户ID', 'Bangumi用户ID', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('72e09a1b-9f5a-4884-bfe4-680ceee921c7', 'wallpaper_desktop', '/assets/images/d1.webp', 'string', 'wallpaper', '桌面壁纸', '桌面端背景图片', 98, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('8233287f-4057-4dff-8c9d-66e5497f294e', 'announcement_content', '欢迎来到我的博客！这是一则示例公告。', 'string', 'announcement', 'Content', NULL, 0, '2025-12-27 09:50:08');
INSERT INTO `site_settings` VALUES ('839f4bd8-e2e9-48fd-9029-61646c2f8625', 'site_description', 'Firefly 是一款基于 Astro 框架和 Fuwari 模板开发的清新美观且现代化个人博客主题模板，专为技术爱好者和内容创作者设计。该主题融合了现代 Web 技术栈，提供了丰富的功能模块和高度可定制的界面，让您能够轻松打造出专业且美观的个人博客网站。', 'text', 'basic', '站点描述', '用于SEO的网站描述', 97, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('860d9805-1135-418e-88b6-362cc865cf49', 'banner_typewriter_enable', 'false', 'boolean', 'banner', '打字机效果', '是否启用副标题打字机效果', 97, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('8887ddce-aaeb-4dd1-a3fb-e1ffd3245e25', 'banner_credit_mobile_enable', 'true', 'boolean', 'banner', '移动端显示来源', '移动端是否显示图片来源', 89, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('918ca1d2-0b0f-4831-9245-231c6c75b8f6', 'brand_logo_type', 'image', 'string', 'brand', 'Logo类型', 'Logo类型: icon 或 image', 99, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('91c226aa-56f8-40e0-bd06-10c9f9a57721', 'feature_rss', 'true', 'boolean', 'feature', 'RSS订阅', '是否启用RSS订阅', 98, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('91f15ea3-fec3-428d-a6b3-6045d3e8ef5c', 'announcement_link_text', '了解更多', 'string', 'announcement', 'Link Text', NULL, 0, '2025-12-27 09:50:08');
INSERT INTO `site_settings` VALUES ('9327afca-9b0a-4cac-9bf2-1e038f67ecef', 'theme_fixed', 'false', 'boolean', 'theme', '固定主题色', '是否固定主题色', 99, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('98dd2ce8-c53b-4182-af42-1edb697a8682', 'api_url', 'http://localhost:8000', 'string', 'api', 'API地址', '后端API服务器地址', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('99905929-12d7-4ae3-a287-68024a6427c0', 'footer_icp_url', 'https://beian.miit.gov.cn/', 'string', 'footer', '备案链接', '备案查询链接', 99, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('a031839b-3905-4284-bc54-1a1a17d57ecb', 'banner_typewriter_speed', '100', 'number', 'banner', '打字速度', '打字速度(毫秒)', 96, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('a147eea5-84a2-4e01-ada5-39d78586f43e', 'post_show_last_modified', 'true', 'boolean', 'post', '显示更新时间', '是否显示上次编辑时间卡片', 96, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('a56467ab-097c-4b8d-9009-82b450de02bd', 'wallpaper_switchable', 'true', 'boolean', 'wallpaper', '允许切换', '是否允许用户切换壁纸模式', 99, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('a58cc76f-f2d6-4cc4-bf98-b45160459b07', 'profile_avatar', '/assets/images/avatar.webp', 'string', 'profile', '头像', '个人头像图片URL', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('ad242f31-3926-40aa-9e1f-ad0b9285d9b1', 'waves_desktop_enable', 'true', 'boolean', 'waves', '桌面端波浪', '桌面端是否启用波浪动画', 100, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('b3502bd2-33cd-4035-86bb-26b6f50a40ba', 'feature_search', 'true', 'boolean', 'feature', '搜索功能', '是否启用搜索功能', 99, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('b4909820-3a43-483b-91ca-6283da5be9cc', 'site_keywords', 'Firefly,Fuwari,Astro,ACGN,博客,技术博客,静态博客', 'string', 'basic', '站点关键词', '用于SEO的关键词', 96, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('b6006b72-5ccb-4f02-9b6b-bdb5352a986a', 'post_show_toc', 'true', 'boolean', 'post', '显示目录', '是否在文章页显示目录', 98, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('bbcb0508-3100-4cd9-9259-fd6c79b3bb95', 'banner_credit_desktop_text', 'Pixiv - 晚晚喵', 'string', 'banner', '桌面端来源文本', '桌面端图片来源文本', 88, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('bc366063-62d4-4ad7-9919-11436ba5d5b6', 'announcement_link_url', '/about', 'string', 'announcement', 'Link Url', NULL, 0, '2025-12-27 09:50:08');
INSERT INTO `site_settings` VALUES ('c272219f-a527-4078-8da2-a6ce37c3cc30', 'waves_quality', 'high', 'string', 'waves', '波浪质量', '波浪质量: high/medium/low', 98, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('c5fa1040-9359-46f1-be8f-4b61f2284ce3', 'page_bangumi', 'true', 'boolean', 'page', '番组计划页面', '是否启用番组计划页面', 98, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('c804ab49-e94e-4bac-908e-ef04ec942154', 'post_outdated_threshold', '30', 'number', 'post', '过期阈值', '文章过期阈值(天数)', 95, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('c96b7e3a-4c97-4e30-88e3-02db69e6c39a', 'site_start_date', '2024-01-01', 'string', 'basic', '建站日期', '网站创建日期', 94, '2025-12-26 04:20:18');
INSERT INTO `site_settings` VALUES ('ca2a8429-824b-47c3-ad2f-cd9a90357baf', 'banner_credit_mobile_url', 'https://www.pixiv.net/users/42715864', 'string', 'banner', '移动端来源链接', '移动端艺术家链接', 85, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('d57b8b2b-f702-424b-9551-02cbdec8293f', 'footer_copyright', '', 'string', 'footer', '版权信息', '自定义版权信息', 98, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('d8985dfb-aeeb-477d-8600-22dc08e54a62', 'post_generate_og_images', 'false', 'boolean', 'post', '生成OG图片', '是否生成OpenGraph图片', 94, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('e6e379bc-99a0-4e2f-aed3-243c93543736', 'announcement_closable', 'True', 'boolean', 'announcement', 'Closable', NULL, 0, '2025-12-27 09:50:08');
INSERT INTO `site_settings` VALUES ('ecc8b8df-ccf9-44f9-8e04-9d061464e6a5', 'page_guestbook', 'true', 'boolean', 'page', '留言板页面', '是否启用留言板页面', 99, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('ee23e58d-3834-4916-a0cb-9186eb5eeb29', 'post_default_layout', 'list', 'string', 'post', '默认布局', '文章列表默认布局: list/grid', 99, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('ef39ff33-2ee2-419c-a7f4-88bd470ef563', 'announcement_link_external', 'False', 'boolean', 'announcement', 'Link External', NULL, 0, '2025-12-27 09:50:08');
INSERT INTO `site_settings` VALUES ('f0c88abc-9c35-4958-aa5a-31715072d92e', 'post_show_updated', 'true', 'boolean', 'post', '显示更新时间', '是否显示文章更新时间', 97, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('f0cf2b05-49ea-45a8-8497-ed5aa063c255', 'feature_archive', 'true', 'boolean', 'feature', '归档页面', '是否启用归档页面', 97, '2025-12-26 01:53:39');
INSERT INTO `site_settings` VALUES ('f21b7e06-4558-4d23-9ba9-c7bed22e0309', 'post_allow_switch_layout', 'true', 'boolean', 'post', '允许切换布局', '是否允许用户切换布局', 98, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('f37b6309-06cf-4cea-b698-dde00d3499c8', 'post_per_page', '5', 'number', 'post', '每页文章数', '文章列表每页显示的文章数量', 100, '2025-12-26 15:02:43');
INSERT INTO `site_settings` VALUES ('f4d89b8c-bd3c-4215-950b-fb890209c388', 'banner_title', 'Lovely firefly!', 'string', 'banner', '横幅标题', '主页横幅主标题', 99, '2025-12-26 02:02:09');
INSERT INTO `site_settings` VALUES ('fcc763a3-23da-48e8-b56a-c5eb9c272eb4', 'footer_powered_by', 'true', 'boolean', 'footer', '显示Powered by', NULL, 97, '2025-12-26 01:47:42');
INSERT INTO `site_settings` VALUES ('fccaaf19-2175-4438-a73b-a6d834ba8105', 'site_subtitle', '个人博客', 'string', 'basic', '站点副标题', '网站的副标题', 99, '2025-12-26 04:36:54');
INSERT INTO `site_settings` VALUES ('fe652da4-69d1-4ba0-a78c-30a208075db3', 'post_grid_masonry', 'true', 'boolean', 'post', '瀑布流布局', '网格布局是否启用瀑布流', 97, '2025-12-26 02:02:09');

-- ----------------------------
-- Table structure for social_links
-- ----------------------------
DROP TABLE IF EXISTS `social_links`;
CREATE TABLE `social_links`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '链接ID(UUID)',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '平台名称',
  `icon` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '图标(iconify格式)',
  `url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '链接URL',
  `show_name` tinyint(1) NULL DEFAULT NULL COMMENT '是否显示名称',
  `sort_order` int NULL DEFAULT NULL COMMENT '排序权重(越大越靠前)',
  `enabled` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_social_links_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '社交链接表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of social_links
-- ----------------------------
INSERT INTO `social_links` VALUES ('213a98da-fad9-4066-823a-4676d89b53ac', 'Bilibli', 'fa6-brands:bilibili', 'https://space.bilibili.com/38932988', 0, 100, 1, '2025-12-26 02:02:09');
INSERT INTO `social_links` VALUES ('6ece0eee-c555-4c5f-a982-aef116af9332', 'Email', 'fa6-solid:envelope', 'mailto:xiaye@msn.com', 0, 98, 1, '2025-12-26 02:02:09');
INSERT INTO `social_links` VALUES ('ee8da68c-4f74-4557-b76d-378cbf440887', 'GitHub', 'fa6-brands:github', 'https://github.com/CuteLeaf', 0, 99, 1, '2025-12-26 02:02:09');
INSERT INTO `social_links` VALUES ('f35f7294-16b9-4a4d-9f4d-0b8014f2d94a', 'RSS', 'fa6-solid:rss', '/rss/', 0, 97, 1, '2025-12-26 02:02:09');

-- ----------------------------
-- Table structure for tags
-- ----------------------------
DROP TABLE IF EXISTS `tags`;
CREATE TABLE `tags`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '标签ID(UUID)',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '标签名称',
  `slug` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '标签URL别名',
  `color` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '标签颜色(HEX)',
  `enabled` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_tags_name`(`name` ASC) USING BTREE,
  UNIQUE INDEX `ix_tags_slug`(`slug` ASC) USING BTREE,
  INDEX `ix_tags_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文章标签表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of tags
-- ----------------------------
INSERT INTO `tags` VALUES ('22fe616a-8ff0-4e77-81bf-9ed54491c409', 'Firefly', 'firefly', '#f59e0b', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('4f71863e-965a-4984-b3ab-23b5ad560368', '主题', 'theme', '#22c55e', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('533c99b3-1bec-4ade-b5a9-70d3dccb8762', '使用指南', 'guide', '#14b8a6', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('5ba00411-b644-412d-9e58-eb3cbca2ab03', '模板', 'template', '#0ea5e9', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('5cb9bb81-6109-4973-8fcd-2e466b1105ba', 'Markdown', 'markdown', '#6366f1', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('62a4f14a-90c1-4eec-9250-5d08ee6f68b3', '示例', 'demo', '#f97316', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('818a1963-5d8c-48c5-ad6d-85f554d613f7', '文章示例', 'examples', '#8b5cf6', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('8dc71448-a83e-4364-924e-d9d4b9ca30eb', '布局', 'layout', '#d946ef', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('9756ca46-88b4-458a-b502-d356c05af42e', '视频', 'video', '#ef4444', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('9934decd-a5dc-44fd-93a7-bf01814c75cb', 'Mermaid', 'mermaid', '#a855f7', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('bbd812ac-e7c5-444c-895a-5ca6dc5e4607', '开源', 'opensource', '#64748b', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('c3f8996d-93f8-497b-86d7-2592ce198c36', '博客', 'blog', '#ec4899', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('d762bcde-dc4b-4d17-b00c-e7de2983bedc', 'KaTeX', 'katex', '#06b6d4', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('eb53689f-54c6-4281-8731-b259727d94ff', '演示', 'showcase', '#fb923c', 1, '2025-12-26 02:51:50');
INSERT INTO `tags` VALUES ('ed23ec0c-35a2-43c2-b150-16858cdcfedf', 'Math', 'math', '#84cc16', 1, '2025-12-26 02:51:50');

SET FOREIGN_KEY_CHECKS = 1;
