# Code Interpreting and Data Analysis

## Overview

E2B Sandbox is ideal for running AI-generated code to analyze data, create visualizations, and perform computations. The sandbox runs code in a headless Jupyter server and supports multiple programming languages.

## Typical Workflow

1. User provides dataset (CSV, JSON, Excel, etc.)
2. LLM generates analysis code based on user request
3. Sandbox executes the code
4. Extract and return results (text, charts, tables)

## Supported Languages

E2B Sandbox supports the following languages out of the box:

- **Python** (default) - no `language` parameter needed
- **JavaScript / TypeScript** - use `language='js'`, `language='javascript'`, `language='ts'`, or `language='typescript'`
- **R** - use `language='r'`
- **Java** - use `language='java'`
- **Bash** - use `language='bash'`

You can also use any custom language runtime by creating a custom sandbox template.

### Running Python Code

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
execution = sandbox.run_code('print("hello world")')

# Access results
print(execution.text)         # Combined output
print(execution.logs.stdout)  # Standard output
print(execution.logs.stderr)  # Standard error
print(execution.results)      # Charts, tables, etc.
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const execution = await sandbox.runCode('print("hello world")')

console.log(execution.text)        // Combined output
console.log(execution.logs.stdout) // Standard output
console.log(execution.logs.stderr) // Standard error
console.log(execution.results)     // Charts, tables, etc.
```

### Running JavaScript/TypeScript Code

The E2B Code Interpreter supports TypeScript, top-level await, ESM-style imports, and automatic promise resolution.

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()

# Install npm packages first
sbx.commands.run("npm install axios")

# Run TypeScript code
execution = sbx.run_code("""
  import axios from "axios";

  const url: string = "https://api.github.com/status";
  const response = await axios.get(url);
  response.data;
""",
    language="ts",
)
print(execution)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sbx = await Sandbox.create()

// Install npm packages first
await sbx.commands.run("npm install axios")

// Run TypeScript code
const execution = await sbx.runCode(`
  import axios from "axios";

  const url: string = "https://api.github.com/status";
  const response = await axios.get(url);
  response.data;
`,
  { language: "ts" }
)
console.log(execution)
```

### Running R Code

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()
execution = sbx.run_code('print("Hello, world!")', language="r")
print(execution)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sbx = await Sandbox.create()
const execution = await sbx.runCode('print("Hello, world!")', { language: 'r' })
console.log(execution)
```

### Running Java Code

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()
execution = sbx.run_code('System.out.println("Hello, world!");', language="java")
print(execution)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sbx = await Sandbox.create()
const execution = await sbx.runCode('System.out.println("Hello, world!");', { language: 'java' })
console.log(execution)
```

### Running Bash Code

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox.create()
execution = sbx.run_code("echo 'Hello, world!'", language="bash")
print(execution)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sbx = await Sandbox.create()
const execution = await sbx.runCode('echo "Hello, world!"', { language: 'bash' })
console.log(execution)
```

## Code Contexts

Code contexts are isolated execution environments within a single sandbox. They allow you to parallelize code execution by running code in different contexts at the same time. By default, code runs in the sandbox's default code execution context.

### Create a New Code Context

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
context = sandbox.create_code_context(
    cwd='/home/user',
    language='python',
    request_timeout=60_000,
)
result = sandbox.run_code('print("Hello, world!")', context=context)
print(result)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const context = await sandbox.createCodeContext({
  cwd: '/home/user',
  language: 'python',
  requestTimeoutMs: 60_000,
})
const result = await sandbox.runCode('print("Hello, world!")', { context })
console.log(result)
```

### List Active Code Contexts

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
contexts = sandbox.list_code_contexts()
print(contexts)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const contexts = await sandbox.listCodeContexts()
console.log(contexts)
```

### Restart a Code Context

Restarting a context clears its state and starts a new code execution session in the same context.

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
context = sandbox.create_code_context(
    cwd='/home/user',
    language='python',
    request_timeout=60_000,
)

# Using context object
restarted_context = sandbox.restart_code_context(context)

# Using context ID
restarted_context = sandbox.restart_code_context(context.contextId)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const context = await sandbox.createCodeContext({
  cwd: '/home/user',
  language: 'python',
  requestTimeoutMs: 60_000,
})

// Using context object
await sandbox.restartCodeContext(context)

// Using context ID
await sandbox.restartCodeContext(context.contextId)
```

### Remove a Code Context

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
context = sandbox.create_code_context(
    cwd='/home/user',
    language='python',
    request_timeout=60_000,
)

# Using context object
sandbox.remove_code_context(context)

# Using context ID
sandbox.remove_code_context(context.contextId)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const context = await sandbox.createCodeContext({
    cwd: '/home/user',
    language: 'python',
    requestTimeoutMs: 60_000,
})

// Using context object
await sandbox.removeCodeContext(context)

// Using context ID
await sandbox.removeCodeContext(context.contextId)
```

## Handling Execution Results

```python
execution = sandbox.run_code(code)

# Check for errors
if execution.error:
    print(f"Error: {execution.error.name}")
    print(f"Message: {execution.error.value}")
    print(f"Traceback:\n{execution.error.traceback}")
else:
    # Process successful results
    print(f"Output: {execution.text}")

    # Process different result types
    for result in execution.results:
        if result.png:
            # Save chart/image (base64 encoded)
            save_base64_image(result.png, 'chart.png')
        elif result.jpeg:
            save_base64_image(result.jpeg, 'image.jpg')
        elif result.html:
            save_html(result.html, 'output.html')
        elif result.chart:
            # Interactive chart data (see Interactive Charts section)
            print(f"Chart type: {result.chart.type}")
        elif result.text:
            print(f"Text result: {result.text}")
```

## Streaming Code Output

You can stream stdout, stderr, and results when executing code.

### Stream stdout and stderr

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
sandbox.run_code(
  code_to_run,
  on_error=lambda error: print('error:', error),
  on_stdout=lambda data: print('stdout:', data),
  on_stderr=lambda data: print('stderr:', data),
)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
sandbox.runCode(codeToRun, {
  onError: error => console.error('error:', error),
  onStdout: data => console.log('stdout:', data),
  onStderr: data => console.error('stderr:', data),
})
```

### Stream results

Use `on_result`/`onResult` callback to receive results like charts, tables, and text as they are produced.

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
sandbox.run_code(
  code_to_run,
  on_result=lambda result: print('result:', result),
)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
await sandbox.runCode(codeToRun, {
  onResult: result => console.log('result:', result),
})
```

## Running Commands

You can run terminal commands inside the sandbox using `commands.run()`.

### Basic Command Execution

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
result = sandbox.commands.run('ls -l')
print(result)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const result = await sandbox.commands.run('ls -l')
console.log(result)
```

### Streaming Command Output

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()
result = sandbox.commands.run(
    'echo hello; sleep 1; echo world',
    on_stdout=lambda data: print(data),
    on_stderr=lambda data: print(data),
)
print(result)
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const result = await sandbox.commands.run('echo hello; sleep 1; echo world', {
  onStdout: (data) => console.log(data),
  onStderr: (data) => console.log(data),
})
console.log(result)
```

### Running Commands in Background

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()

# Start the command in the background
command = sandbox.commands.run('echo hello; sleep 10; echo world', background=True)

# Get stdout and stderr from the background command
# You can run this in a separate thread or use command.wait()
for stdout, stderr, _ in command:
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

# Kill the command
command.kill()
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()

// Start the command in the background
const command = await sandbox.commands.run('echo hello; sleep 10; echo world', {
  background: true,
  onStdout: (data) => console.log(data),
})

// Kill the command
await command.kill()
```

## Data Analysis Pattern

### Complete Example: CSV Analysis with Claude

```python
from e2b_code_interpreter import Sandbox
from anthropic import Anthropic
import base64

# 1. Create sandbox
sandbox = Sandbox.create()

# 2. Upload dataset
with open('sales_data.csv', 'rb') as f:
    content = f.read()
dataset_path = sandbox.files.write('/home/user/sales.csv', content)

# 3. Prepare analysis request
client = Anthropic()
prompt = f"""
I have a sales dataset at {dataset_path.path}.
Columns: date, product, quantity, revenue

Analyze:
1. Total revenue by product
2. Monthly sales trend
3. Top 10 selling products

Create a visualization showing the monthly revenue trend.

CRITICAL: Your code MUST end with this exact line to display the plot:
display(plt.gcf())
"""

# 4. Define tool for code execution
tools = [{
    "name": "execute_python",
    "description": "Execute python code in a Jupyter notebook",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute"
            }
        },
        "required": ["code"]
    }
}]

# 5. Get code from LLM
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=[{"role": "user", "content": prompt}],
    tools=tools
)

# 6. Execute generated code
if message.stop_reason == "tool_use":
    tool_use = next(block for block in message.content if block.type == "tool_use")
    if tool_use.name == "execute_python":
        code = tool_use.input['code']
        execution = sandbox.run_code(code)

        # 7. Process results
        if execution.error:
            print(f"Error: {execution.error.value}")
        else:
            # Save any charts generated
            for i, result in enumerate(execution.results):
                if result.png:
                    img_data = base64.b64decode(result.png)
                    with open(f'chart_{i}.png', 'wb') as f:
                        f.write(img_data)
                    print(f"Saved chart_{i}.png")

            # Print text output
            print(execution.text)

# 8. Clean up
sandbox.kill()
```

## Working with Different Data Formats

### CSV Files

```python
# Upload CSV
dataset = sandbox.files.write('/home/user/data.csv', csv_content)

# Analyze
code = f"""
import pandas as pd

df = pd.read_csv('{dataset.path}')
print(df.describe())
print(df.head())
"""
result = sandbox.run_code(code)
print(result.text)
```

### JSON Files

```python
import json

# Upload JSON
data = {'sales': [100, 200, 300]}
json_str = json.dumps(data)
sandbox.files.write('/home/user/data.json', json_str.encode('utf-8'))

# Analyze
code = """
import json
import pandas as pd

with open('/home/user/data.json') as f:
    data = json.load(f)

df = pd.DataFrame(data)
print(df.describe())
"""
result = sandbox.run_code(code)
```

### Excel Files

```python
# Upload Excel file
with open('workbook.xlsx', 'rb') as f:
    content = f.read()
sandbox.files.write('/home/user/data.xlsx', content)

# Analyze
code = """
import pandas as pd

# Read all sheets
excel_file = pd.ExcelFile('/home/user/data.xlsx')
sheets = {sheet: excel_file.parse(sheet) for sheet in excel_file.sheet_names}

for name, df in sheets.items():
    print(f"Sheet: {name}")
    print(df.head())
    print()
"""
result = sandbox.run_code(code)
```

## Creating Visualizations

### Static Charts (base64 PNG)

E2B automatically detects Matplotlib plots and sends them back as base64-encoded PNG images accessible on `result.png`.

**Python SDK:**
```python
import base64
from e2b_code_interpreter import Sandbox

code_to_run = """
import matplotlib.pyplot as plt

plt.plot([1, 2, 3, 4])
plt.ylabel('some numbers')
plt.show()
"""

sandbox = Sandbox.create()
execution = sandbox.run_code(code_to_run)

first_result = execution.results[0]
if first_result.png:
    with open('chart.png', 'wb') as f:
        f.write(base64.b64decode(first_result.png))
    print('Chart saved as chart.png')
```

**JavaScript SDK:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'
import fs from 'fs'

const codeToRun = `
import matplotlib.pyplot as plt

plt.plot([1, 2, 3, 4])
plt.ylabel('some numbers')
plt.show()
`
const sandbox = await Sandbox.create()
const execution = await sandbox.runCode(codeToRun)

const firstResult = execution.results[0]
if (firstResult.png) {
  fs.writeFileSync('chart.png', firstResult.png, { encoding: 'base64' })
  console.log('Chart saved as chart.png')
}
```

### Interactive Charts (structured data)

E2B automatically detects Matplotlib charts and extracts structured chart data accessible via `result.chart`. This data can be sent to a frontend to render with any charting library.

Supported interactive chart types:
- Line chart
- Bar chart
- Scatter plot
- Pie chart
- Box and whisker plot

**Python SDK:**
```python
from e2b_code_interpreter import Sandbox

code = """
import matplotlib.pyplot as plt

authors = ['Author A', 'Author B', 'Author C', 'Author D']
sales = [100, 200, 300, 400]

plt.figure(figsize=(10, 6))
plt.bar(authors, sales, label='Books Sold', color='blue')
plt.xlabel('Authors')
plt.ylabel('Number of Books Sold')
plt.title('Book Sales by Authors')

plt.tight_layout()
plt.show()
"""

sandbox = Sandbox.create()
execution = sandbox.run_code(code)
chart = execution.results[0].chart

print('Type:', chart.type)
print('Title:', chart.title)
print('X Label:', chart.x_label)
print('Y Label:', chart.y_label)
print('X Unit:', chart.x_unit)
print('Y Unit:', chart.y_unit)
print('Elements:')
for element in chart.elements:
    print('  Label:', element.label)
    print('  Value:', element.value)
    print('  Group:', element.group)
```

**JavaScript SDK:**
```javascript
import { Sandbox, BarChart } from '@e2b/code-interpreter'

const code = `
import matplotlib.pyplot as plt

authors = ['Author A', 'Author B', 'Author C', 'Author D']
sales = [100, 200, 300, 400]

plt.figure(figsize=(10, 6))
plt.bar(authors, sales, label='Books Sold', color='blue')
plt.xlabel('Authors')
plt.ylabel('Number of Books Sold')
plt.title('Book Sales by Authors')

plt.tight_layout()
plt.show()
`

const sandbox = await Sandbox.create()
const result = await sandbox.runCode(code)
const chart = result.results[0].chart as BarChart

console.log('Type:', chart.type)
console.log('Title:', chart.title)
console.log('X Label:', chart.x_label)
console.log('Y Label:', chart.y_label)
console.log('Elements:', chart.elements)
```

### Seaborn Visualizations

```python
code = """
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

df = pd.DataFrame({
    'category': ['A', 'B', 'C', 'D'] * 5,
    'value': np.random.randn(20)
})

plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x='category', y='value')
plt.title('Distribution by Category')
plt.show()
"""

execution = sandbox.run_code(code)
```

### Plotly Interactive Charts

```python
code = """
import plotly.graph_objects as go

fig = go.Figure(data=go.Scatter(
    x=[1, 2, 3, 4],
    y=[10, 11, 12, 13]
))

fig.update_layout(title='Interactive Chart')
fig.write_html('/home/user/chart.html')
fig.show()
"""

execution = sandbox.run_code(code)

# Download HTML chart
html_content = sandbox.files.read('/home/user/chart.html')
with open('chart.html', 'wb') as f:
    f.write(html_content)
```

## Multi-Step Analysis with Contexts

For complex analysis, use code contexts to maintain state across multiple executions or run analyses in parallel.

### Sequential Multi-Step Analysis

```python
sandbox = Sandbox.create(timeout=300)

# Step 1: Load data
sandbox.run_code("""
import pandas as pd
df = pd.read_csv('/home/user/sales.csv')
df['date'] = pd.to_datetime(df['date'])
print(f"Loaded {len(df)} rows")
""")

# Step 2: Clean data (shares state with Step 1 in default context)
sandbox.run_code("""
Q1 = df['revenue'].quantile(0.25)
Q3 = df['revenue'].quantile(0.75)
IQR = Q3 - Q1
df_clean = df[(df['revenue'] >= Q1 - 1.5*IQR) & (df['revenue'] <= Q3 + 1.5*IQR)]
print(f"After cleaning: {len(df_clean)} rows")
""")

# Step 3: Aggregate
result = sandbox.run_code("""
monthly = df_clean.groupby(df_clean['date'].dt.to_period('M'))['revenue'].sum()
print(monthly)
""")

print(result.text)
sandbox.kill()
```

### Parallel Analysis with Multiple Contexts

```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()

# Upload data once
with open('data.csv', 'rb') as f:
    sandbox.files.write('/home/user/data.csv', f)

# Create separate contexts for parallel analysis
ctx_summary = sandbox.create_code_context(cwd='/home/user', language='python')
ctx_charts = sandbox.create_code_context(cwd='/home/user', language='python')

# Run analyses in different contexts (each has its own state)
result_summary = sandbox.run_code("""
import pandas as pd
df = pd.read_csv('/home/user/data.csv')
print(df.describe())
""", context=ctx_summary)

result_charts = sandbox.run_code("""
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv('/home/user/data.csv')
df.hist(figsize=(12, 8))
plt.tight_layout()
plt.show()
""", context=ctx_charts)

# Clean up contexts when done
sandbox.remove_code_context(ctx_summary)
sandbox.remove_code_context(ctx_charts)
sandbox.kill()
```

## Pre-installed Libraries

E2B sandboxes come with many popular Python libraries pre-installed:

**Data Analysis:**
- pandas
- numpy
- scipy
- statsmodels

**Visualization:**
- matplotlib
- seaborn
- plotly

**Machine Learning:**
- scikit-learn
- tensorflow
- pytorch

**Others:**
- requests
- beautifulsoup4
- pillow

See full list: https://github.com/e2b-dev/code-interpreter/blob/main/template/requirements.txt

## Installing Additional Packages

```python
# Install packages during execution
code = """
!pip install xgboost

import xgboost as xgb
print(f"XGBoost version: {xgb.__version__}")
"""

execution = sandbox.run_code(code)
```

Or use `commands.run()` to install packages via terminal:

```python
# Install via commands
sandbox.commands.run("pip install xgboost")

# Then use in code execution
execution = sandbox.run_code("""
import xgboost as xgb
print(f"XGBoost version: {xgb.__version__}")
""")
```

For JavaScript/TypeScript packages:

```python
sandbox.commands.run("npm install axios")
execution = sandbox.run_code('import axios from "axios"; console.log("installed")', language="ts")
```

## Error Handling

### Comprehensive Error Handling

```python
def safe_execute(sandbox, code):
    """Execute code with comprehensive error handling"""
    try:
        execution = sandbox.run_code(code)

        if execution.error:
            # Runtime error in code
            error_info = {
                'type': execution.error.name,
                'message': execution.error.value,
                'traceback': execution.error.traceback
            }
            return {'success': False, 'error': error_info}

        # Successful execution
        results = {
            'success': True,
            'text': execution.text,
            'stdout': execution.logs.stdout,
            'stderr': execution.logs.stderr,
            'charts': [],
            'html': []
        }

        # Extract different result types
        for result in execution.results:
            if result.png:
                results['charts'].append(result.png)
            elif result.chart:
                results['charts'].append(result.chart)
            elif result.html:
                results['html'].append(result.html)

        return results

    except Exception as e:
        # SDK or network error
        return {
            'success': False,
            'error': {
                'type': 'SDKError',
                'message': str(e)
            }
        }

# Usage
result = safe_execute(sandbox, llm_generated_code)
if result['success']:
    print(result['text'])
    for chart in result['charts']:
        save_chart(chart)
else:
    print(f"Error: {result['error']['message']}")
```

## Best Practices

### 1. Set Appropriate Timeout

```python
# Quick analysis: 60-120 seconds
sandbox = Sandbox.create(timeout=120)

# Complex processing: 300-600 seconds
sandbox = Sandbox.create(timeout=600)
```

### 2. Upload Data Before Running Code

```python
# Good: Upload first
sandbox.files.write('/home/user/data.csv', dataset)
result = sandbox.run_code(f"df = pd.read_csv('/home/user/data.csv')")

# Bad: Inline data (size limits, slower)
code = f"""
data = {large_list}
df = pd.DataFrame(data)
"""
```

### 3. Use Code Contexts for Isolation

```python
# Use separate contexts when you need isolated environments
ctx_a = sandbox.create_code_context(language='python')
ctx_b = sandbox.create_code_context(language='python')

# These run in isolated environments - variables don't leak between them
sandbox.run_code("x = 42", context=ctx_a)
sandbox.run_code("print(x)", context=ctx_b)  # NameError: x is not defined
```

### 4. Save Outputs to Files

```python
# Generate outputs and save
code = """
import matplotlib.pyplot as plt

# ... create chart ...
plt.savefig('/home/user/output.png')

# ... generate report ...
with open('/home/user/report.txt', 'w') as f:
    f.write(report)
"""

sandbox.run_code(code)

# Download outputs
chart = sandbox.files.read('/home/user/output.png')
report = sandbox.files.read('/home/user/report.txt')
```

### 5. Use display() for Matplotlib Output

```python
# When working with Matplotlib, use display(plt.gcf()) to ensure the plot is captured
code = """
import matplotlib.pyplot as plt

plt.plot([1, 2, 3], [4, 5, 6])
plt.title('My Plot')

# This ensures the plot appears in execution.results
display(plt.gcf())
"""

execution = sandbox.run_code(code)
# execution.results[0].png contains the base64 PNG
```

## Common Patterns

### Pattern 1: Quick Data Summary

```python
with Sandbox.create() as sandbox:
    # Upload data
    sandbox.files.write('/home/user/data.csv', dataset)

    # Get summary
    result = sandbox.run_code("""
    import pandas as pd
    df = pd.read_csv('/home/user/data.csv')
    print(df.info())
    print(df.describe())
    print(df.head())
    """)

    print(result.text)
```

### Pattern 2: Multi-Language Analysis

```python
sandbox = Sandbox.create()
sandbox.files.write('/home/user/data.csv', data)

# Analyze with Python
python_result = sandbox.run_code("""
import pandas as pd
df = pd.read_csv('/home/user/data.csv')
print(df.describe())
""")

# Process with R
r_result = sandbox.run_code("""
data <- read.csv('/home/user/data.csv')
summary(data)
""", language="r")

# Quick shell inspection
bash_result = sandbox.run_code("wc -l /home/user/data.csv", language="bash")

sandbox.kill()
```

### Pattern 3: Interactive Analysis Session

```python
# Start session
sandbox = Sandbox.create(timeout=600)

# Load data once
sandbox.files.write('/home/user/dataset.csv', data)
sandbox.run_code("import pandas as pd; df = pd.read_csv('/home/user/dataset.csv')")

# User asks multiple questions - each query shares state in the default context
for user_query in user_queries:
    # Generate code for each query
    analysis_code = llm.generate_code(user_query)

    # Execute (variables from previous runs are available)
    result = sandbox.run_code(analysis_code)

    # Return results
    yield result

sandbox.kill()
```

### Pattern 4: Background Process with Foreground Analysis

```python
sandbox = Sandbox.create()

# Start a long-running data processing job in background
command = sandbox.commands.run(
    'python /home/user/process_data.py',
    background=True,
)

# Meanwhile, run quick analyses in the foreground
result = sandbox.run_code("""
import pandas as pd
df = pd.read_csv('/home/user/raw_data.csv')
print(f"Raw data has {len(df)} rows")
""")

# Later, kill the background job if needed
command.kill()
sandbox.kill()
```
