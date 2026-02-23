# MCP Gateway

E2B's MCP Gateway provides seamless access to 200+ Model Context Protocol (MCP) servers from the [Docker MCP Catalog](https://hub.docker.com/mcp), enabling sandboxes to integrate with external tools and services for data access, cloud operations, web scraping, business automation, and AI capabilities. You can also run [custom MCP servers](#custom-mcp-servers) from GitHub repositories.

## What is MCP Gateway?

### Model Context Protocol Overview

The Model Context Protocol (MCP) is an open standard that allows AI agents and LLMs to securely connect to external data sources and tools. MCP servers expose capabilities through a standardized interface that any MCP client can consume.

### E2B's MCP Integration

E2B provides built-in MCP Gateway functionality that:
- **Hosts 200+ pre-configured MCP servers** from Docker's catalog
- **Runs servers inside sandboxes** with proper isolation
- **Supports custom MCP servers** from public GitHub repositories
- **Provides HTTP access** both from outside and inside sandboxes
- **Manages authentication** through bearer tokens
- **Supports custom configuration** per server instance
- **Supports custom templates** with pre-pulled MCP server images for faster startup

### Benefits

1. **No Infrastructure Setup**: MCP servers are pre-configured and ready to use
2. **Secure Isolation**: Each sandbox gets its own MCP server instances
3. **Flexible Access**: Connect from external clients or from code running in the sandbox
4. **Rich Ecosystem**: Access to databases, cloud APIs, web tools, business platforms, and more
5. **Unified Interface**: All tools exposed through standardized MCP protocol

## Quickstart

### Enabling MCP Servers

Enable MCP servers when creating a sandbox by passing configuration for each server you want to use.

**Python (async):**
```python
import asyncio
from e2b import AsyncSandbox
import os

async def main():
    sandbox = await AsyncSandbox.create(mcp={
        "browserbase": {
            "apiKey": os.environ["BROWSERBASE_API_KEY"],
            "geminiApiKey": os.environ["GEMINI_API_KEY"],
            "projectId": os.environ["BROWSERBASE_PROJECT_ID"],
        },
        "exa": {
            "apiKey": os.environ["EXA_API_KEY"],
        },
        "notion": {
            "internalIntegrationToken": os.environ["NOTION_API_KEY"],
        },
    })

    mcp_url = sandbox.get_mcp_url()
    mcp_token = await sandbox.get_mcp_token()

asyncio.run(main())
```

**JavaScript:**
```javascript
import Sandbox from 'e2b'

const sandbox = await Sandbox.create({
    mcp: {
        browserbase: {
            apiKey: process.env.BROWSERBASE_API_KEY,
            geminiApiKey: process.env.GEMINI_API_KEY,
            projectId: process.env.BROWSERBASE_PROJECT_ID
        },
        exa: {
            apiKey: process.env.EXA_API_KEY
        },
        notion: {
            internalIntegrationToken: process.env.NOTION_API_KEY
        }
    }
})

const mcpUrl = sandbox.getMcpUrl()
const mcpToken = await sandbox.getMcpToken()
```

### Connecting from Outside the Sandbox

Connect to MCP servers from your application code running outside the sandbox.

**Using Official MCP Client (TypeScript):**
```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js'

const client = new Client({
    name: 'e2b-mcp-client',
    version: '1.0.0'
})

const transport = new StreamableHTTPClientTransport(
    new URL(sandbox.getMcpUrl()),
    {
        requestInit: {
            headers: {
                'Authorization': `Bearer ${await sandbox.getMcpToken()}`
            }
        }
    }
)

await client.connect(transport)

// List available tools
const tools = await client.listTools()
console.log('Available tools:', tools.tools.map(t => t.name))

// Call a tool
const result = await client.callTool({
    name: 'some_tool',
    arguments: { param: 'value' }
})

await client.close()
await sandbox.kill()
```

**Using Official MCP Client (Python):**
```python
import asyncio
from datetime import timedelta
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client(
        url=sandbox.get_mcp_url(),
        headers={"Authorization": f"Bearer {await sandbox.get_mcp_token()}"},
        timeout=timedelta(seconds=600)
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
    await sandbox.kill()

asyncio.run(main())
```

### Connecting from Inside the Sandbox

Access the MCP gateway from code running within the sandbox itself:

**Internal MCP URL:**
```
http://localhost:50005/mcp
```

**Important**: When connecting from inside the sandbox, you must include the Authorization header with the MCP token. How this is added depends on your MCP client.

## Available Servers (200+)

E2B provides access to 200+ MCP servers from [Docker's catalog](https://hub.docker.com/mcp). Below are the most commonly used servers in each category.

### Data & Database Servers

**MongoDB**
- **Purpose**: NoSQL document database operations
- **Configuration**: `mdbMcpConnectionString`
- **Use Cases**: CRUD operations, aggregations, document queries

**PostgreSQL**
- **Purpose**: Relational database operations
- **Configuration**: `url` (connection string)
- **Use Cases**: SQL queries, table operations, transactions

**Elasticsearch**
- **Purpose**: Search and analytics engine
- **Configuration**: `url`, optional `esApiKey`
- **Use Cases**: Full-text search, log analytics, data aggregation

**Redis**
- **Purpose**: In-memory data store
- **Configuration**: `host`, `port`, credentials, SSL options
- **Use Cases**: Caching, session storage, pub/sub messaging

**Astra DB**
- **Purpose**: Cassandra-based cloud database
- **Configuration**: `astraDbApplicationToken`, `endpoint`
- **Use Cases**: Wide-column NoSQL operations

### Cloud & Infrastructure

**Azure Kubernetes Service (AKS)**
- **Purpose**: Kubernetes cluster management on Azure
- **Configuration**: `azureDir`, `kubeconfig`, `accessLevel`
- **Use Cases**: Deploy and manage containerized applications

**Kubernetes**
- **Purpose**: Container orchestration
- **Configuration**: `configPath` to kubeconfig file
- **Use Cases**: Manage pods, deployments, services

### Web & Content Tools

**Firecrawl**
- **Purpose**: Web scraping and content extraction
- **Configuration**: `apiKey`, retry configuration, credit thresholds
- **Use Cases**: Extract structured data from websites

**Brave Search**
- **Purpose**: Web search API
- **Configuration**: `apiKey`
- **Use Cases**: Privacy-focused web search queries

**Exa**
- **Purpose**: AI-optimized search
- **Configuration**: `apiKey`
- **Use Cases**: Research, content discovery

### Business & Productivity

**Slack**
- **Purpose**: Team communication and automation
- **Configuration**: `botToken`, `teamId`, optional channel IDs
- **Use Cases**: Send messages, read channels, manage users

**Notion**
- **Purpose**: Workspace and knowledge management
- **Configuration**: `internalIntegrationToken`
- **Use Cases**: Create/read pages, manage databases, search content

**GitHub (Official)**
- **Purpose**: Git repository operations
- **Configuration**: `githubPersonalAccessToken`
- **Use Cases**: Code operations, issues, pull requests, workflows

**Atlassian (Jira/Confluence)**
- **Purpose**: Project management and documentation
- **Configuration**: Base URLs, API tokens
- **Use Cases**: Issue tracking, documentation management

**Airtable**
- **Purpose**: Database-spreadsheet hybrid
- **Configuration**: `airtableApiKey`
- **Use Cases**: Read schemas, query records, automate workflows

### Finance & Commerce

**Stripe**
- **Purpose**: Payment processing
- **Configuration**: `secretKey`
- **Use Cases**: Process payments, manage subscriptions, invoicing

### Special Purpose Servers

**Filesystem**
- **Purpose**: File system operations
- **Configuration**: `paths` array for allowed directory access
- **Use Cases**: Read/write files with controlled access

**Memory**
- **Purpose**: Knowledge graph-based persistent storage
- **Configuration**: None
- **Use Cases**: Store and retrieve structured information

## Custom MCP Servers

In addition to the 200+ pre-built MCP servers, you can run custom MCP servers directly from public GitHub repositories.

### How It Works

When you specify a GitHub repository, E2B will:
1. Clone the repository into the sandbox
2. Run the `installCmd` (optional) to install dependencies
3. Run the `runCmd` to start the MCP server with stdio transport

The `runCmd` must start an MCP server that follows the MCP specification and communicates via stdio.

### Using a Custom MCP Server

**JavaScript:**
```javascript
import Sandbox from 'e2b'

const sandbox = await Sandbox.create({
    mcp: {
        'github/modelcontextprotocol/servers': {
            installCmd: 'npm install',
            runCmd: 'sudo npx -y @modelcontextprotocol/server-filesystem /root',
        },
    },
})
```

**Python:**
```python
from e2b import Sandbox

sbx = Sandbox.create(
    mcp={
        "github/modelcontextprotocol/servers": {
            "install_cmd": "npm install",
            "run_cmd": "sudo npx -y @modelcontextprotocol/server-filesystem /root",
        },
    }
)
```

### Configuration

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `installCmd` / `install_cmd` | string | No | Command to install dependencies before starting the MCP server |
| `runCmd` / `run_cmd` | string | Yes | Command to start the stdio-enabled MCP server |

**Important for npx-based servers:** Always include `installCmd: 'npm install'` when using `npx` in your `runCmd`. Without installing dependencies first, npx will try to use the local repository and fail.

### Troubleshooting Custom Servers

If your custom MCP server doesn't work as expected:
1. Explore the sandbox via the dashboard or by connecting with `e2b connect <sandbox-id>`
2. Check the gateway log file with `sudo cat /var/log/mcp-gateway/gateway.log`

## Custom Templates with Pre-pulled MCP Servers

You can prepull MCP server Docker images during template build time for faster runtime performance.

### Building a Template with MCP Servers

You must use the `mcp-gateway` template as your base template.

**JavaScript:**
```javascript
import { Template, defaultBuildLogger } from 'e2b'

const template = Template()
  .fromTemplate("mcp-gateway")
  .addMcpServer(["browserbase", "exa"])

await Template.build(template, 'my-mcp-gateway', {
  cpuCount: 8,
  memoryMB: 8192,
  onBuildLogs: defaultBuildLogger(),
})
```

**Python:**
```python
from e2b import Template, default_build_logger

template = (
    Template()
    .from_template("mcp-gateway")
    .add_mcp_server(["browserbase", "exa"])
)

Template.build(
    template,
    'my-mcp-gateway',
    cpu_count=8,
    memory_mb=8192,
    on_build_logs=default_build_logger(),
)
```

### Using the Template

Once built, create sandboxes from your template. You still need to provide configuration for each MCP server.

```javascript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create({
    template: "my-mcp-gateway",
    mcp: {
        browserbase: {
            apiKey: process.env.BROWSERBASE_API_KEY,
            geminiApiKey: process.env.GEMINI_API_KEY,
            projectId: process.env.BROWSERBASE_PROJECT_ID,
        },
        exa: {
            apiKey: process.env.EXA_API_KEY,
        },
    },
})
```

## Connection Examples

### Claude Desktop / Claude Code

Connect Claude to your E2B MCP Gateway:

```bash
claude mcp add \
    --transport http \
    e2b-mcp-gateway \
    <mcp_url> \
    --header "Authorization: Bearer <mcp_token>"
```

### OpenAI Agents SDK

**TypeScript:**
```typescript
import { MCPServerStreamableHttp } from '@openai/agents'

const mcp = new MCPServerStreamableHttp({
    url: mcpUrl,
    name: 'E2B MCP Gateway',
    requestInit: {
        headers: {
            'Authorization': `Bearer ${await sandbox.getMcpToken()}`
        }
    }
})
```

**Python:**
```python
from agents.mcp import MCPServerStreamableHttp

async with MCPServerStreamableHttp(
    name="e2b-mcp-client",
    params={
        "url": sandbox.get_mcp_url(),
        "headers": {"Authorization": f"Bearer {await sandbox.get_mcp_token()}"},
    },
) as server:
    tools = await server.list_tools()
    print("Available tools:", [t.name for t in tools])
```

### MCP Inspector for Debugging

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is an official debugging tool that provides a web interface for testing MCP servers.

```bash
npx @modelcontextprotocol/inspector \
    --transport http \
    --url <mcp_url> \
    --header "Authorization: Bearer <mcp_token>"
```

This opens a web interface where you can:
- **Browse available tools** - See all tools exposed by enabled MCP servers
- **Test tool calls** - Execute tools with different parameters
- **Inspect payloads** - View request/response JSON
- **Debug connection issues** - Verify authentication and connectivity

## Example Projects

The E2B Cookbook contains ready-to-run example projects:

- **Claude Code** - Claude Code with MCP integration
- **Browserbase** - Web automation agent with Browserbase
- **Groq + Exa** - AI research using Groq and Exa
- **Research agent** - Research Agent using OpenAI Agents framework
- **MCP client** - Basic MCP client connecting to an E2B Sandbox
- **Custom MCP server** - Use custom MCP servers installed from GitHub
- **Custom template** - Create a custom E2B Sandbox with pre-installed MCP servers

All examples available at: https://github.com/e2b-dev/e2b-cookbook

## Common Patterns

### Pattern 1: Multi-Tool Agent

Enable multiple MCP servers for comprehensive capabilities:

```python
from e2b import Sandbox
import os

sandbox = Sandbox.create(
    mcp={
        # Data access
        'postgres': {'url': os.environ['DATABASE_URL']},

        # Web research
        'brave': {'apiKey': os.environ['BRAVE_API_KEY']},
        'firecrawl': {'apiKey': os.environ['FIRECRAWL_API_KEY']},

        # Business automation
        'slack': {
            'botToken': os.environ['SLACK_BOT_TOKEN'],
            'teamId': os.environ['SLACK_TEAM_ID']
        },
        'github': {
            'githubPersonalAccessToken': os.environ['GITHUB_TOKEN']
        }
    }
)

# Now your agent can query databases, search the web,
# send Slack messages, and manage GitHub issues all through MCP
```

### Pattern 2: Claude Code Inside Sandbox with MCP

Run Claude Code inside an E2B sandbox with MCP servers:

```typescript
import Sandbox from 'e2b'

const sbx = await Sandbox.create({
    mcp: {
        browserbase: {
            apiKey: process.env.BROWSERBASE_API_KEY,
            geminiApiKey: process.env.GEMINI_API_KEY,
            projectId: process.env.BROWSERBASE_PROJECT_ID,
        },
        exa: {
            apiKey: process.env.EXA_API_KEY,
        },
    },
})

const mcpUrl = sbx.getMcpUrl()
const mcpToken = await sbx.getMcpToken()

// Add MCP gateway to Claude inside the sandbox
await sbx.commands.run(
    `claude mcp add --transport http e2b-mcp-gateway ${mcpUrl} --header "Authorization: Bearer ${mcpToken}"`,
    { timeoutMs: 0, onStdout: console.log, onStderr: console.log }
)

// Run Claude with a task
await sbx.commands.run(
    `echo 'Research open positions at e2b.dev using browserbase and exa.' | claude -p --dangerously-skip-permissions`,
    { timeoutMs: 0, onStdout: console.log, onStderr: console.log }
)
```

### Pattern 3: Dynamic Tool Discovery

Discover available tools at runtime:

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js'

const client = new Client({ name: 'dynamic-agent', version: '1.0.0' })
const transport = new StreamableHTTPClientTransport(
    new URL(sandbox.getMcpUrl()),
    { requestInit: { headers: { 'Authorization': `Bearer ${await sandbox.getMcpToken()}` }}}
)
await client.connect(transport)

// Discover all available tools
const toolsResult = await client.listTools()
const tools = toolsResult.tools

// Group by provider
const byProvider = {}
for (const tool of tools) {
    const provider = tool.name.split('_')[0]
    if (!byProvider[provider]) byProvider[provider] = []
    byProvider[provider].push(tool)
}

console.log('Available tools by provider:')
for (const [provider, providerTools] of Object.entries(byProvider)) {
    console.log(`  ${provider}: ${providerTools.length} tools`)
}
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to MCP Gateway

**Solutions**:
1. Verify the MCP URL is correct:
   ```python
   print(f"MCP URL: {sandbox.get_mcp_url()}")
   ```

2. Check authentication token:
   ```python
   token = await sandbox.get_mcp_token()
   print(f"Token length: {len(token)}")
   ```

3. Test with MCP Inspector:
   ```bash
   npx @modelcontextprotocol/inspector --transport http --url $MCP_URL --header "Authorization: Bearer $MCP_TOKEN"
   ```

### Authentication Errors

**Problem**: 401 Unauthorized or 403 Forbidden

**Solutions**:
1. Ensure Authorization header is properly formatted:
   ```
   Authorization: Bearer <token>
   ```
   (Note: "Bearer" followed by a space, then the token)

2. Verify token hasn't expired (recreate sandbox if needed)

3. Check that the token matches the sandbox (tokens are sandbox-specific)

### Missing Tools

**Problem**: Expected tools not available when listing

**Solutions**:
1. Verify MCP servers were enabled at sandbox creation
2. Check server configuration is correct (each server has required fields)
3. List tools to see what's actually available

### Timeout Issues

**Problem**: MCP tool calls timing out

**Solutions**:
1. Increase sandbox timeout
2. Check network connectivity from sandbox
3. Use async operations where possible

## Best Practices

### Security

1. **Never hardcode credentials** - use environment variables
2. **Use minimal permissions** - configure API tokens with only required scopes
3. **Rotate credentials regularly** - especially for production workloads
4. **Isolate per user** - create separate sandboxes per user/session

### Performance

1. **Enable only needed servers** - don't enable all 200+ servers if you only need a few
2. **Use custom templates** - prepull MCP server images for faster startup
3. **Reuse sandboxes** - connect to existing sandboxes instead of creating new ones

### Reliability

1. **Handle errors gracefully** - implement try-catch around tool calls
2. **Implement retries** - with exponential backoff for transient failures
3. **Monitor tool availability** - check that required tools are available before use

## Additional Resources

- **E2B Documentation**: https://e2b.dev/docs
- **MCP Specification**: https://modelcontextprotocol.io
- **Docker MCP Catalog**: https://hub.docker.com/mcp
- **E2B Cookbook**: https://github.com/e2b-dev/e2b-cookbook (examples and tutorials)
- **MCP Inspector**: https://github.com/modelcontextprotocol/inspector
