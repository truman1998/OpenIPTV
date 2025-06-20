# OpenIPTV - 社区驱动的私有化IPTV服务平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
![Stars](https://img.shields.io/github/stars/truman1998/OpenIPTV?style=social)

**OpenIPTV** 是一个开源项目，旨在构建一个强大、灵活且完全由您自己掌控的IPTV服务平台。它采用先进的“中央-客户端”架构，让平台管理员可以轻松地管理海量用户，同时为用户提供稳定、可靠的直播源服务。

---

## 核心功能 ✨

* **动态用户管理**: 通过图形化的Web后台，管理员可以随时随地创建、查看、和封禁用户。
* **Token认证**: 每个用户都拥有独一无二的通行证 (Token)，确保服务安全可控。
* **安全至上**: 后端内置防爆破机制，前端与后端完全分离，最大化保障您的服务安全。
* **架构灵活**: 核心服务逻辑与用户客户端分离。管理员只需更新中央服务器，所有用户即可无感享受到最新的直播源和功能。
* **部署简单**: 为终端用户提供了极其友好的Web部署工具，只需几步即可在自己的设备上完成客户端的部署。
* **(未来) 社区驱动**: 欢迎全世界的开发者和爱好者共同贡献与维护直播源，打造一个永不失效的直播源仓库。

---

## 项目架构 🏗️

本项目采用“中央厨房”+“取餐窗口”的模式：

* **中央服务器 (您自己的后端服务)**:
    * 作为整个平台的“大脑”，负责处理所有核心逻辑：用户认证、直播源聚合与代理、以及访问日志记录。
    * 您作为管理员，拥有对这个中央服务器的绝对控制权。

* **客户端 (用户部署的Docker)**:
    * 作为轻量级的“信使”，它的唯一作用就是将用户的播放请求安全地转发到您的中央服务器进行处理。
    * 这种设计极大地降低了用户端的资源消耗，并使得服务更新变得异常简单。

---

## 部署指南 🚀

部署分为两部分：**A. 管理员部署中央服务器** 和 **B. 终端用户部署客户端**。

### A. 面向平台管理员 (您自己)

这是您作为平台所有者，**只需操作一次**的步骤。

1.  **克隆或下载本项目代码**到您的服务器。
2.  **配置 `docker-compose.yml`**:
    * 打开 `docker-compose.yml` 文件。
    * 找到 `environment` 部分，将 `ADMIN_TOKEN` 的值修改为您自己的、**复杂且保密的管理员密码**。
3.  **启动服务**:
    * 在项目根目录下，运行命令：
        ```bash
        docker-compose up -d --build
        ```
4.  **管理您的平台**:
    * 服务启动后，您就可以通过部署好的 `admin.html` 页面来访问您的专属管理后台，开始创建和管理您的第一批用户了！

### B. 面向终端用户

作为用户，您需要从管理员那里获取两样东西：
1.  **中央服务器的地址** (由管理员提供)
2.  **您的专属通行证Token** (由管理员在后台为您创建)

然后，访问管理员提供的**客户端部署页面**（例如 `https://wans.eu.org`），按照页面指引填写信息，即可一键生成您自己的 `docker-compose.yml` 配置文件。将该文件保存在您的设备（如NAS、服务器、电脑）上，并在该文件目录下运行 `docker-compose up -d`，即可开始享用服务！

---

## 如何贡献 ❤️

我们热烈欢迎所有人参与到 **OpenIPTV** 项目的建设中来！您可以通过以下两种方式做出贡献：

### 1. 贡献直播源 (最欢迎的方式！)

如果您有稳定、高质量的直播源，请通过以下步骤与我们分享：

1.  **Fork** 本仓库到您的GitHub账号。
2.  在您的仓库中，找到 `sources/` 目录。您可以编辑现有文件，或创建一个新的分类文件（如 `日韩频道.txt`）。
3.  在文件中按照 **`频道名称,直播链接`** 的格式添加新的直播源，每行一个。例如：
    ```
    某高清电影频道,[http://example.com/live/1.m3u8](http://example.com/live/1.m3u8)
    某体育频道,[http://example.com/live/2.m3u8](http://example.com/live/2.m3u8)
    ```
4.  完成添加后，回到您的仓库主页，点击 **"Contribute"** -> **"Open pull request"**，向我们提交您的更改。
5.  我们会在审核后将您宝贵的贡献合并到项目中，让所有用户都能享受到！

### 2. 贡献代码

如果您是一位开发者，并对项目有任何改进建议（例如优化代码、增加新功能），我们同样非常欢迎！

1.  **Fork** 本仓库。
2.  为您的新功能或修复创建一个新的分支 (`git checkout -b feature/AmazingFeature`)。
3.  提交您的代码 (`git commit -m 'Add some AmazingFeature'`)。
4.  将您的分支推送到GitHub (`git push origin feature/AmazingFeature`)。
5.  向我们提交一个 **Pull Request**，并详细说明您的改动。

---

## 免责声明 📜

本项目为开源项目，所有代码仅供学习和技术交流使用。

项目中涉及的所有直播源链接均由社区用户贡献或搜集自互联网。我们不存储任何视频内容，也不对任何链接的合法性、有效性负责。

请在遵守您当地法律法规的前提下使用本项目。任何因使用本项目而导致的法律责任或风险，均由使用者本人承担，与本项目发起人及贡献者无关。
