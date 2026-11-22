# Multi Web Search MCP

[![CI](https://github.com/6jeffr3y/multi-web-search/actions/workflows/ci.yml/badge.svg)](https://github.com/6jeffr3y/multi-web-search/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/6jeffr3y/multi-web-search?style=flat-square)](https://github.com/6jeffr3y/multi-web-search/releases)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/github/license/6jeffr3y/multi-web-search?style=flat-square)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-6f42c1?style=flat-square)](https://modelcontextprotocol.io/)
[![Stars](https://img.shields.io/github/stars/6jeffr3y/multi-web-search?style=social)](https://github.com/6jeffr3y/multi-web-search/stargazers)

Multi Web Search MCP 是 Codex 的联网搜索 MCP 服务。
项目面向多供应商搜索接口。
项目提供统一搜索入口。
项目返回结构化搜索结果。
项目支持自动故障转移。
项目支持短期熔断。
项目支持请求缓存。
项目支持并发限制。
项目提供 fast、balanced、deep 三种搜索模式。

## 项目特点

- 多供应商适配。
- 自动故障转移。
- 结构化结果。
- 短期熔断。
- 请求缓存。
- 并发限制。
- 三种搜索模式。
- 密钥不进入工具结果。

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

## 快速开始

运行环境为 Python 3.11 以上版本。
依赖列表位于 `requirements.txt`。

依赖安装命令：

```sh
python3 -m pip install -r requirements.txt
```

启动脚本为 `launch.sh`。
启动脚本读取同一目录的 `server.py`。

启动命令：

```sh
./launch.sh
```

## 配置

配置文件为 `providers.json`。
配置文件包含供应商名称。
配置文件包含接口类型。
配置文件包含启用状态。
配置文件包含优先级。
配置文件包含 API Key 来源。
配置修改后自动加载。
个人配置建议保存为 `providers.local.json`。
`MULTI_WEB_SEARCH_CONFIG` 可指定配置文件路径。
`providers.local.json` 已加入 `.gitignore`。

## Codex MCP 配置

配置示例：

```toml
[mcp_servers.multi_web_search]
command = "/path/to/multi-web-search/launch.sh"
startup_timeout_sec = 10.0
tool_timeout_sec = 45.0

[mcp_servers.multi_web_search.tools.web_search]
output_token_limit = 12000

[mcp_servers.multi_web_search.tools.web_search_batch]
output_token_limit = 20000
```

## 安全

API Key 从环境变量读取。
API Key 从密钥文件读取。
API Key 从 TOML 配置读取。
工具结果不返回 API Key。
仓库不包含 API Key。
仓库不包含个人配置。
仓库不包含用户数据。
仓库不包含搜索记录。
安全策略位于 `SECURITY.md`。

## 测试

检查命令：

```sh
make check
```

测试命令：

```sh
make test
```

## 支持

贡献指南位于 `CONTRIBUTING.md`。
项目的 Star 支持后续开发。

## English

Multi Web Search MCP is a web search MCP server for Codex.
It provides one search entry for multiple providers.
It supports automatic failover.
It returns structured search results.
It supports request caching.
It supports concurrency limits.
It provides three search modes: fast, balanced, deep.
API keys come from environment variables.
API keys come from key files.
API keys come from TOML fields.
MCP tool results do not include API keys.
The repository does not include API keys.
The repository does not include personal configuration.
The repository does not include user data.
The repository does not include search history.

## License

许可证为 MIT。
许可证文本位于 `LICENSE`。
