import Key from "../i18nKey";
import type { Translation } from "../translation";

export const en: Translation = {
	[Key.home]: "Home",
	[Key.about]: "About",
	[Key.archive]: "Archive",
	[Key.search]: "Search",
	[Key.searchNoResults]: "No results found.",
	[Key.searchTypeSomething]: "Type something to search...",
	[Key.searchLoading]: "Searching...",
	[Key.searchSummary]: "Summary",
	[Key.searchContent]: "Content",
	[Key.searchViewMore]: "View more results ({count} more)",
	[Key.other]: "Other",
	[Key.all]: "All",

	[Key.tags]: "Tags",
	[Key.categories]: "Categories",
	[Key.recentPosts]: "Recent Posts",
	[Key.postList]: "Post List",
	[Key.tableOfContents]: "Table of Contents",
	[Key.postPasswordTitle]: "Protected post",
	[Key.postPasswordDescription]: "Enter the password to view this content",
	[Key.postPasswordPlaceholder]: "Enter password",
	[Key.postPasswordUnlock]: "Unlock",
	[Key.postPasswordRequired]: "Please enter a password",
	[Key.postPasswordInvalid]: "Incorrect password",
	[Key.postPasswordVerifyFailed]:
		"Failed to verify password. Please try again later.",
	[Key.postPasswordError]: "An error occurred. Please try again later.",

	// Announcement
	[Key.announcement]: "Announcement",
	[Key.announcementClose]: "Close",

	[Key.comments]: "Comments",
	[Key.commentSection]: "Comments",
	[Key.commentSubtitle]: "Share your thoughts and discuss with everyone",
	[Key.commentNotConfigured]: "Comment system not configured",
	[Key.guestbookCommentHint]:
		"You have not enabled the comment system in the configuration file yet. After enabling it, visitors will be able to leave messages here",
	[Key.friends]: "Friends",
	[Key.friendsDescription]:
		"Here are my friends, welcome to visit and communicate with each other",
	[Key.guestbook]: "Guestbook",
	[Key.guestbookDescription]:
		"Welcome to leave your mark here, share your thoughts and suggestions",
	[Key.untitled]: "Untitled",
	[Key.uncategorized]: "Uncategorized",
	[Key.noTags]: "No Tags",

	[Key.wordCount]: "word",
	[Key.wordsCount]: "words",
	[Key.minuteCount]: "minute",
	[Key.minutesCount]: "minutes",
	[Key.postCount]: "post",
	[Key.postsCount]: "posts",

	[Key.themeColor]: "Theme Color",

	[Key.lightMode]: "Light",
	[Key.darkMode]: "Dark",
	[Key.systemMode]: "System",

	[Key.more]: "More",

	[Key.author]: "Author",
	[Key.publishedAt]: "Published at",
	[Key.license]: "License",
	[Key.bangumi]: "Bangumi",

	// Bangumi Filter and Status Text
	[Key.bangumiTitle]: "My Bangumi",
	[Key.bangumiSubtitle]: "Record my ACG journey",
	[Key.bangumiFilterAll]: "All",
	[Key.bangumiFilterWatched]: "Watched",
	[Key.bangumiFilterWatching]: "Watching",
	[Key.bangumiFilterWish]: "Wish",
	[Key.bangumiFilterOnHold]: "On Hold",
	[Key.bangumiFilterDropped]: "Dropped",
	[Key.bangumiFilterGamePlayed]: "Played",
	[Key.bangumiFilterGamePlaying]: "Playing",
	[Key.bangumiFilterGameWish]: "Wish to Play",
	[Key.bangumiFilterBookRead]: "Read",
	[Key.bangumiFilterBookReading]: "Reading",
	[Key.bangumiFilterBookWish]: "Wish to Read",
	[Key.bangumiFilterMusicListened]: "Listened",
	[Key.bangumiFilterMusicListening]: "Listening",
	[Key.bangumiFilterMusicWish]: "Wish to Listen",
	[Key.bangumiStatusWish]: "Wish",
	[Key.bangumiStatusWatched]: "Watched",
	[Key.bangumiStatusWatching]: "Watching",
	[Key.bangumiStatusOnHold]: "On Hold",
	[Key.bangumiStatusDropped]: "Dropped",
	[Key.bangumiStatusGameWish]: "Wish to Play",
	[Key.bangumiStatusGamePlayed]: "Played",
	[Key.bangumiStatusGamePlaying]: "Playing",
	[Key.bangumiStatusBookWish]: "Wish to Read",
	[Key.bangumiStatusBookRead]: "Read",
	[Key.bangumiStatusBookReading]: "Reading",
	[Key.bangumiStatusMusicWish]: "Wish to Listen",
	[Key.bangumiStatusMusicListened]: "Listened",
	[Key.bangumiStatusMusicListening]: "Listening",
	[Key.bangumiStatusUnknown]: "Unknown",
	[Key.bangumiNoData]: "No Data",
	[Key.bangumiNoDataDescription]: "No items in this category",
	[Key.bangumiEmpty]: "No Data",
	[Key.bangumiEmptyReason]:
		"Possible reasons: username does not exist, network connection issue, or API limit",
	[Key.bangumiUsername]: "Username",
	[Key.bangumiApi]: "API",
	[Key.bangumiConfigTip]:
		"Tip: Please set the correct Bangumi username in the page configuration",
	[Key.bangumiPrevPage]: "Previous",
	[Key.bangumiNextPage]: "Next",
	[Key.bangumiCurrentPage]: "Page",
	[Key.bangumiTotalPages]: "of",
	[Key.bangumiPage]: "page",

	// Bangumi Categories
	[Key.bangumiCategoryBook]: "Book",
	[Key.bangumiCategoryAnime]: "Anime",
	[Key.bangumiCategoryMusic]: "Music",
	[Key.bangumiCategoryGame]: "Game",
	[Key.bangumiCategoryReal]: "Real",

	// Bangumi Data Update
	[Key.bangumiLastUpdated]: "Data updated at",
	[Key.bangumiUpdatedAt]: "Build time",
	[Key.bangumiDataStatic]: "Static data",

	// Pagination
	[Key.paginationFirst]: "First",
	[Key.paginationPrev]: "Previous",
	[Key.paginationNext]: "Next",
	[Key.paginationLast]: "Last",
	[Key.paginationPage]: "Page",
	[Key.paginationOf]: "of",
	[Key.paginationTotal]: ", Total",
	[Key.paginationRecords]: " records",

	// 404 Page
	[Key.notFound]: "404",
	[Key.notFoundTitle]: "Page Not Found",
	[Key.notFoundDescription]:
		"Sorry, the page you visited does not exist or has been moved.",
	[Key.backToHome]: "Back to Home",

	// RSS Page
	[Key.rss]: "RSS Feed",
	[Key.rssDescription]: "Subscribe to get latest updates",
	[Key.rssSubtitle]:
		"Subscribe via RSS to get the latest articles and updates imediately",
	[Key.rssLink]: "RSS Link",
	[Key.rssCopyToReader]: "Copy link to your RSS reader",
	[Key.rssCopyLink]: "Copy Link",
	[Key.rssLatestPosts]: "Latest Posts",
	[Key.rssWhatIsRSS]: "What is RSS?",
	[Key.rssWhatIsRSSDescription]:
		"RSS (Really Simple Syndication) is a standard format for publishing frequently updated content. With RSS, you can:",
	[Key.rssBenefit1]:
		"Get the latest website content in time without manually visiting",
	[Key.rssBenefit2]: "Manage subscriptions to multiple websites in one place",
	[Key.rssBenefit3]: "Avoid missing important updates and articles",
	[Key.rssBenefit4]: "Enjoy an ad-free, clean reading experience",
	[Key.rssHowToUse]:
		"It is recommended to use Feedly, Inoreader or other RSS readers to subscribe to this site.",
	[Key.rssCopied]: "RSS link copied to clipboard!",
	[Key.rssCopyFailed]: "Copy failed, please copy the link manually",

	// Last Modified Time Card
	[Key.lastModifiedPrefix]: "Last updated on ",
	[Key.lastModifiedOutdated]: "Some content may be outdated",
	[Key.lastModifiedDaysAgo]: "{days} days ago",
	[Key.year]: "year",
	[Key.month]: "month",
	[Key.day]: "day",
	[Key.hour]: "hour",
	[Key.minute]: "minute",
	[Key.second]: "second",

	// Page Views Statistics
	[Key.pageViews]: "Views",
	[Key.pageViewsLoading]: "Loading...",
	[Key.pageViewsError]: "Stats unavailable",

	// Pinned
	[Key.pinned]: "Pinned",

	// Wallpaper Mode
	[Key.wallpaperMode]: "Wallpaper Mode",
	[Key.wallpaperBannerMode]: "Banner Wallpaper",
	[Key.wallpaperOverlayMode]: "Transparent",
	[Key.wallpaperNoneMode]: "Solid Color Background",

	// Sponsor Page
	[Key.sponsor]: "Sponsor",
	[Key.sponsorTitle]: "Support Me",
	[Key.sponsorDescription]:
		"If my content has been helpful to you, welcome to sponsor me through the following methods. Your support is the driving force for my continued creation!",
	[Key.sponsorMethods]: "Payment Methods",
	[Key.sponsorList]: "Sponsors",
	[Key.sponsorEmpty]: "No sponsors yet",
	[Key.sponsorAmount]: "Amount",
	[Key.sponsorDate]: "Date",
	[Key.sponsorMessage]: "Message",
	[Key.sponsorAnonymous]: "Anonymous",
	[Key.scanToSponsor]: "Scan to Sponsor",
	[Key.sponsorGoTo]: "Go to Sponsor",
	[Key.sponsorButton]: "Support & Share",
	[Key.sponsorButtonText]:
		"If this article helped you, please share or support!",

	[Key.shareOnSocial]: "Share Article",
	[Key.shareOnSocialDescription]:
		"If this article helped you, please share it with others!",

	// Site Statistics
	[Key.siteStats]: "Site Statistics",
	[Key.siteStatsPostCount]: "Posts",
	[Key.siteStatsCategoryCount]: "Categories",
	[Key.siteStatsTagCount]: "Tags",
	[Key.siteStatsTotalWords]: "Total Words",
	[Key.siteStatsRunningDays]: "Running Days",
	[Key.siteStatsLastUpdate]: "Last Activity",
	[Key.siteStatsDaysAgo]: "{days} days ago",
	[Key.siteStatsDays]: "{days} days",
	[Key.today]: "Today",

	// Calendar Component
	[Key.calendarSunday]: "Sun",
	[Key.calendarMonday]: "Mon",
	[Key.calendarTuesday]: "Tue",
	[Key.calendarWednesday]: "Wed",
	[Key.calendarThursday]: "Thu",
	[Key.calendarFriday]: "Fri",
	[Key.calendarSaturday]: "Sat",
	[Key.calendarJanuary]: "Jan",
	[Key.calendarFebruary]: "Feb",
	[Key.calendarMarch]: "Mar",
	[Key.calendarApril]: "Apr",
	[Key.calendarMay]: "May",
	[Key.calendarJune]: "Jun",
	[Key.calendarJuly]: "Jul",
	[Key.calendarAugust]: "Aug",
	[Key.calendarSeptember]: "Sep",
	[Key.calendarOctober]: "Oct",
	[Key.calendarNovember]: "Nov",
	[Key.calendarDecember]: "Dec",

	[Key.shareArticle]: "Share",
	[Key.generatingPoster]: "Generating Poster...",
	[Key.copied]: "Copied",
	[Key.copyLink]: "Copy Link",
	[Key.savePoster]: "Save Poster",
	[Key.scanToRead]: "Scan to Read",

	// Admin Panel
	[Key.adminTitle]: "Admin Panel",
	[Key.adminPostManagement]: "Post Management",
	[Key.adminNewPost]: "New Post",
	[Key.adminPost]: "Post",
	[Key.adminEditPost]: "Edit Post",
	[Key.adminLogout]: "Logout",
	[Key.adminLogin]: "Login",
	[Key.adminLoginTitle]: "Admin Login",
	[Key.adminLoginSubtitle]: "Sign in to manage your blog content",
	[Key.adminUsername]: "Username",
	[Key.adminPassword]: "Password",
	[Key.adminLoginButton]: "Sign In",
	[Key.adminLoggingIn]: "Signing in...",

	// Post List
	[Key.adminPostTitle]: "Title",
	[Key.adminPostStatus]: "Status",
	[Key.adminPostCategory]: "Category",
	[Key.adminPostDate]: "Date",
	[Key.adminPostActions]: "Actions",
	[Key.adminPostDraft]: "Draft",
	[Key.adminPostProtected]: "Protected",
	[Key.adminPostPublic]: "Public",
	[Key.adminPostUncategorized]: "Uncategorized",
	[Key.adminPostEmpty]: "No posts yet. Start creating your first post!",
	[Key.adminPostLoadFailed]:
		"Failed to load. Please check your network connection or backend service.",

	// Post Editor
	[Key.adminPostTitlePlaceholder]: "Enter post title...",
	[Key.adminPostSlug]: "Slug",
	[Key.adminPostSlugPlaceholder]: "url-slug",
	[Key.adminPostCategoryLabel]: "Category",
	[Key.adminPostCategoryPlaceholder]: "Default Category",
	[Key.adminPostTags]: "Tags",
	[Key.adminPostTagsPlaceholder]: "tag1, tag2",
	[Key.adminPostTagsHint]: "Click tags to select, multiple selection allowed",
	[Key.adminPostImage]: "Cover Image URL",
	[Key.adminPostImagePlaceholder]: "https://...",
	[Key.adminPostPassword]: "Post Password",
	[Key.adminPostPasswordPlaceholder]: "Optional password",
	[Key.adminPostDraftToggle]: "Save as Draft",
	[Key.adminPostPinOrder]: "Pin Order",
	[Key.adminPostPinOrderPlaceholder]: "Lower number = higher priority",
	[Key.adminPostDescription]: "Description",
	[Key.adminPostDescriptionPlaceholder]: "Brief description...",
	[Key.adminPostPublish]: "Publish Post",
	[Key.adminPostUpdate]: "Update Post",
	[Key.adminPostPublishing]: "Publishing...",
	[Key.adminPostUpdating]: "Updating...",

	// Section Titles
	[Key.adminSectionBasicInfo]: "Basic Info",
	[Key.adminSectionAppearance]: "Appearance",
	[Key.adminSectionAdvanced]: "Advanced Settings",

	// Action Messages
	[Key.adminConfirmDelete]:
		"Are you sure you want to delete this post? This action cannot be undone.",
	[Key.adminConfirmInitSettings]:
		"Initialize default settings? Existing custom values will be kept.",
	[Key.adminDeleteSuccess]: "Deleted successfully",
	[Key.adminDeleteFailed]: "Delete failed, please try again later",
	[Key.adminSaveSuccess]: "Saved successfully",
	[Key.adminSaveFailed]: "Save failed",
	[Key.adminLoginExpired]: "Session expired, please login again",
	[Key.adminLoginFailed]: "Invalid username or password",
	[Key.adminRequiredFields]: "Title and slug are required",
	[Key.adminContentEmpty]: "Content cannot be empty",

	// Dashboard
	[Key.adminDashboard]: "Dashboard",

	// Common Admin UI
	[Key.adminAdd]: "Add",
	[Key.adminEdit]: "Edit",
	[Key.adminDelete]: "Delete",
	[Key.adminSave]: "Save",
	[Key.adminCancel]: "Cancel",
	[Key.adminLoading]: "Loading...",
	[Key.adminEnabled]: "Enabled",
	[Key.adminDisabled]: "Disabled",
	[Key.adminActive]: "Active",
	[Key.adminManageBlogPosts]: "Manage blog posts",
	[Key.adminManageBlogCategories]: "Manage blog categories",
	[Key.adminManageBlogTags]: "Manage blog tags",
	[Key.adminManageFriendLinks]: "Manage friend links",
	[Key.adminManageSiteSettings]: "Manage site settings",
	[Key.adminSettings]: "Setting",

	// Admin Menu
	[Key.adminCategoryManagement]: "Categories",
	[Key.adminTagManagement]: "Tags",
	[Key.adminFriendManagement]: "Friends",
	[Key.adminSystemManagement]: "System",
	[Key.adminLogManagement]: "Access Logs",

	// Access Logs
	[Key.adminManageAccessLogs]: "View and manage access logs",
	[Key.adminLogType]: "Log Type",
	[Key.adminLogTypeAll]: "All",
	[Key.adminLogTypeLoginSuccess]: "Login Success",
	[Key.adminLogTypeLoginFailed]: "Login Failed",
	[Key.adminLogTypeApiAccess]: "API Access",
	[Key.adminLogIpAddress]: "IP Address",
	[Key.adminLogUserAgent]: "User Agent",
	[Key.adminLogRequestPath]: "Request Path",
	[Key.adminLogRequestMethod]: "Method",
	[Key.adminLogStatusCode]: "Status",
	[Key.adminLogTime]: "Time",
	[Key.adminLogDetail]: "Detail",
	[Key.adminLogNoLogs]: "No logs yet",
	[Key.adminLogLoadFailed]: "Failed to load logs",
	[Key.adminLogCleanup]: "Cleanup Logs",
	[Key.adminLogCleanupConfirm]: "Are you sure to cleanup logs older than 30 days?",
	[Key.adminLogCleanupSuccess]: "Logs cleaned up successfully",
	[Key.adminLogStats]: "Log Statistics",
	[Key.adminLogTotalLogs]: "Total Logs",
	[Key.adminLogTodayLogs]: "Today's Logs",
	[Key.adminLogUniqueIps]: "Unique IPs",

	// Admin Pagination
	[Key.adminPaginationPrev]: "Previous",
	[Key.adminPaginationNext]: "Next",
	[Key.adminPaginationInfo]: "Page {page} of {total}",
	[Key.adminPaginationPerPage]: "Per page",

	// Admin Category/Form Fields
	[Key.adminName]: "Name",
	[Key.adminSlug]: "Slug",
	[Key.adminAutoGenerated]: "auto-generated",
	[Key.adminDescription]: "Description",
	[Key.adminColor]: "Color",
	[Key.adminSortOrder]: "Sort Order",
	[Key.adminNoCategoriesYet]: "No categories yet",
	[Key.adminCategoryLoadFailed]: "Failed to load categories",
	[Key.adminConfirmDeleteCategory]: "Delete category \"{name}\"?",
	[Key.adminNoCategories]: "No categories",
	[Key.adminPosts]: "posts",
};
