import { defineConfig } from "vitepress";

export default defineConfig({
  lang: "zh-CN",
  // GitHub Pages 项目站部署在子路径,资源引用必须带此前缀,否则样式全丢
  base: "/xr-h1-ros2-pub/",
  title: "XR-AIH1 使用教程",
  description: "XR-H1 双臂升降整机控制台客户手册：状态监控、标定、双臂操控、建图导航、工作流编排、HTTP API 与 ROS 话题速查",
  rewrites: {
    "README.md": "index.md",
  },
  srcExcludes: ["pipeline/**", "build_site.py"],
  themeConfig: {
    siteTitle: "XR-AIH1 使用教程",
    outline: { level: [2, 3], label: "本页目录" },
    docFooter: { prev: "上一章", next: "下一章" },
    darkModeSwitchLabel: "外观",
    sidebarMenuLabel: "章节",
    returnToTopLabel: "回到顶部",
    socialLinks: [],
    search: {
      provider: "local",
      options: {
        translations: {
          button: { buttonText: "搜索教程", buttonAriaLabel: "搜索教程" },
          modal: {
            noResultsText: "没有找到结果",
            resetButtonTitle: "清空关键词",
            footer: { selectText: "选择", navigateText: "切换", closeText: "关闭" },
          },
        },
      },
    },
    sidebar: [
      {
        text: "XR-AIH1 控制台使用教程",
        items: [
          { text: "课程首页", link: "/" },
          { text: "01 · 快速上手与总览", link: "/01-overview" },
          { text: "02 · 手柄状态监控", link: "/02-gamepad" },
          { text: "03 · 标定中心", link: "/03-calibration" },
          { text: "04 · 双臂操控", link: "/04-dual-arm" },
          { text: "05 · 建图导航", link: "/05-navigation" },
          { text: "06 · 工作流编排", link: "/06-workflow" },
          { text: "07 · HTTP API 速查", link: "/07-api" },
          { text: "08 · ROS 话题速查", link: "/08-topics" },
        ],
      },
    ],
  },
});
