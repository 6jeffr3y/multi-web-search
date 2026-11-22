# Multi Web Search MCP

Multi Web Search MCP 是 Codex 的联网搜索 MCP 服务。
项目面向多供应商搜索接口。
项目提供统一搜索入口。
项目返回结构化搜索结果。
项目支持自动故障转移。
项目支持短期熔断。
项目支持请求缓存。
项目支持并发限制。
项目提供 fast、balanced、deep 三种搜索模式。

## 搜索接口

项目适配以下接口：

- DeepSeek Search API
- DeepSeek Anthropic Messages
- MiMo Chat Completions
- GLM Chat Completions
- DashScope
- OpenAI-compatible Responses
- Gemini Google Search
- 自定义 Chat Completions 接口

## 工具

- `web_search`：单次搜索。
- `web_search_batch`：批量搜索。单次最多 8 个查询。
- `search_providers`：查看供应商状态。
- `reload_search_config`：重载配置。
- `clear_search_cache`：清理缓存。

## 配置

配置文件为 `providers.json`。
配置包含供应商名称。
配置包含接口类型。
配置包含启用状态。
配置包含优先级。
配置包含 API Key 来源。
配置修改后自动加载。

## 安全

API Key 从环境变量读取。
API Key 从密钥文件读取。
API Key 从 TOML 配置读取。
工具结果不返回 API Key。
仓库不包含 API Key。
仓库不包含本地配置。
仓库不包含用户数据。
仓库不包含搜索记录。

## 仓库

仓库当前只包含 README。
源码暂未公开。
