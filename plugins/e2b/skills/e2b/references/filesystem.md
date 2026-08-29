# Filesystem Operations

## Overview

Each E2B Sandbox has its own isolated filesystem.
- **Hobby tier**: 10 GB free disk space
- **Pro tier**: 20 GB disk space

The filesystem is completely isolated from other sandboxes and the host system.

With the E2B SDK you can:
- Read and write files
- Get file/directory metadata (info)
- Watch directories for changes
- Upload data to the sandbox
- Download data from the sandbox

## Writing Files

### Writing a Single File

**Python:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()

# Write string content
sandbox.files.write('/path/to/file', 'file content')

# Write from a local file (binary)
with open('path/to/local/file', 'rb') as file:
    sandbox.files.write('/path/in/sandbox', file)
```

**JavaScript:**
```javascript
import fs from 'fs'
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()

// Write string content
await sandbox.files.write('/path/to/file', 'file content')

// Write from a local file
const content = fs.readFileSync('/local/path')
await sandbox.files.write('/path/in/sandbox', content)
```

### Writing Multiple Files

**Python:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()

sandbox.files.write_files([
    {"path": "/path/to/a", "data": "file content"},
    {"path": "another/path/to/b", "data": "file content"}
])
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()

await sandbox.files.write([
    { path: '/path/to/a', data: 'file content' },
    { path: '/another/path/to/b', data: 'file content' }
])
```

### Upload Directory / Multiple Files

**Python:**
```python
import os
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()

def read_directory_files(directory_path):
    files = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, "rb") as file:
                files.append({
                    'path': file_path,
                    'data': file.read()
                })
    return files

files = read_directory_files("/local/dir")
sandbox.files.write_files(files)
```

**JavaScript:**
```javascript
import fs from 'fs'
import path from 'path'
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()

const readDirectoryFiles = (directoryPath) => {
  const files = fs.readdirSync(directoryPath)
  return files
    .filter(file => fs.statSync(path.join(directoryPath, file)).isFile())
    .map(file => {
      const filePath = path.join(directoryPath, file)
      return { path: filePath, data: fs.readFileSync(filePath, 'utf8') }
    })
}

const files = readDirectoryFiles('/local/dir')
await sandbox.files.write(files)
```

## Reading Files

Download files from the sandbox to your local system.

**Python:**
```python
# Read file from sandbox
content = sandbox.files.read('/path/in/sandbox')

# Save locally
with open('/local/path', 'w') as file:
    file.write(content)
```

**JavaScript:**
```javascript
// Read file from sandbox
const content = await sandbox.files.read('/path/in/sandbox')

// Save locally
fs.writeFileSync('/local/path', content)
```

## File and Directory Info (Metadata)

Get detailed information about a file or directory using `files.get_info()` (Python) or `files.getInfo()` (JavaScript).

### Getting File Info

**Python:**
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create()

# Create a file
sandbox.files.write('test_file.txt', 'Hello, world!')

# Get information about the file
info = sandbox.files.get_info('test_file.txt')

print(info)
# EntryInfo(
#   name='test_file.txt',
#   type=<FileType.FILE: 'file'>,
#   path='/home/user/test_file.txt',
#   size=13,
#   mode=0o644,
#   permissions='-rw-r--r--',
#   owner='user',
#   group='user',
#   modified_time='2025-05-26T12:00:00.000Z',
#   symlink_target=None
# )
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()

// Create a file
await sandbox.files.write('test_file.txt', 'Hello, world!')

// Get information about the file
const info = await sandbox.files.getInfo('test_file.txt')

console.log(info)
// {
//   name: 'test_file.txt',
//   type: 'file',
//   path: '/home/user/test_file.txt',
//   size: 13,
//   mode: 0o644,
//   permissions: '-rw-r--r--',
//   owner: 'user',
//   group: 'user',
//   modifiedTime: '2025-05-26T12:00:00.000Z',
//   symlinkTarget: null
// }
```

### Getting Directory Info

**Python:**
```python
sandbox.files.make_dir('test_dir')

info = sandbox.files.get_info('test_dir')

print(info)
# EntryInfo(
#   name='test_dir',
#   type=<FileType.DIR: 'dir'>,
#   path='/home/user/test_dir',
#   size=0,
#   mode=0o755,
#   permissions='drwxr-xr-x',
#   owner='user',
#   group='user',
#   modified_time='2025-05-26T12:00:00.000Z',
#   symlink_target=None
# )
```

**JavaScript:**
```javascript
await sandbox.files.makeDir('test_dir')

const info = await sandbox.files.getInfo('test_dir')

console.log(info)
// {
//   name: 'test_dir',
//   type: 'dir',
//   path: '/home/user/test_dir',
//   size: 0,
//   mode: 0o755,
//   permissions: 'drwxr-xr-x',
//   owner: 'user',
//   group: 'user',
//   modifiedTime: '2025-05-26T12:00:00.000Z',
//   symlinkTarget: null
// }
```

### Info Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | File or directory name |
| `type` | string | `'file'` or `'dir'` |
| `path` | string | Absolute path |
| `size` | number | Size in bytes (0 for directories) |
| `mode` | number | Unix file mode (e.g., 0o644) |
| `permissions` | string | Human-readable permissions (e.g., `-rw-r--r--`) |
| `owner` | string | File owner |
| `group` | string | File group |
| `modified_time` / `modifiedTime` | string | ISO 8601 modification timestamp |
| `symlink_target` / `symlinkTarget` | string or null | Target path if symlink, null otherwise |

## Listing Files

List files and directories in the sandbox.

**Python:**
```python
files = sandbox.files.list('/home/user')

for file in files:
    print(f"Name: {file.name}")
    print(f"Path: {file.path}")
    print(f"Is Directory: {file.is_dir}")
    print(f"Size: {file.size} bytes")
```

**JavaScript:**
```javascript
const files = await sandbox.files.list('/home/user')

for (const file of files) {
    console.log(`Name: ${file.name}`)
    console.log(`Path: ${file.path}`)
    console.log(`Is Directory: ${file.isDir}`)
    console.log(`Size: ${file.size} bytes`)
}
```

## Deleting Files

**Python:**
```python
# Remove a file
sandbox.files.remove('/home/user/temp.txt')

# Remove a directory (recursive)
sandbox.files.remove('/home/user/temp_dir')
```

**JavaScript:**
```javascript
// Remove a file
await sandbox.files.remove('/home/user/temp.txt')

// Remove a directory
await sandbox.files.remove('/home/user/temp_dir')
```

## Making Directories

**Python:**
```python
sandbox.files.make_dir('test_dir')
```

**JavaScript:**
```javascript
await sandbox.files.makeDir('test_dir')
```

## Watching Filesystem Changes

Monitor directories for changes in real-time using `files.watch_dir()` (Python) or `files.watchDir()` (JavaScript).

**Important:** Since events are tracked asynchronously, their delivery may be delayed. It is recommended not to collect or close a watcher immediately after making a change.

### Basic Watch

**Python:**
```python
from e2b_code_interpreter import Sandbox, FilesystemEventType

sandbox = Sandbox.create()
dirname = '/home/user'

# Watch directory for changes
handle = sandbox.files.watch_dir(dirname)

# Trigger file write event
sandbox.files.write(f"{dirname}/my-file", "hello")

# Retrieve the latest new events since the last get_new_events() call
events = handle.get_new_events()
for event in events:
    print(event)
    if event.type == FilesystemEventType.WRITE:
        print(f"wrote to file {event.name}")
```

**JavaScript:**
```javascript
import { Sandbox, FilesystemEventType } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()
const dirname = '/home/user'

// Start watching directory for changes
const handle = await sandbox.files.watchDir(dirname, async (event) => {
    console.log(event)
    if (event.type === FilesystemEventType.WRITE) {
        console.log(`wrote to file ${event.name}`)
    }
})

// Trigger file write event
await sandbox.files.write(`${dirname}/my-file`, 'hello')
```

### Recursive Watching

Enable recursive watching using the `recursive` parameter.

**Note:** When rapidly creating new folders (e.g., deeply nested path of folders), events other than `CREATE` might not be emitted. To avoid this behavior, create the required folder structure in advance.

**Python:**
```python
handle = sandbox.files.watch_dir(dirname, recursive=True)
sandbox.files.write(f"{dirname}/my-folder/my-file", "hello")

events = handle.get_new_events()
for event in events:
    print(event)
    if event.type == FilesystemEventType.WRITE:
        print(f"wrote to file {event.name}")
```

**JavaScript:**
```javascript
const handle = await sandbox.files.watchDir(dirname, async (event) => {
    console.log(event)
    if (event.type === FilesystemEventType.WRITE) {
        console.log(`wrote to file ${event.name}`)
    }
}, {
    recursive: true
})

await sandbox.files.write(`${dirname}/my-folder/my-file`, 'hello')
```

## Pre-signed URLs for Upload and Download

For use cases where you need to let users from unauthorized environments (like a browser) upload or download files, you can use pre-signed URLs. This requires creating a sandbox with `secure: true`.

### Download with Pre-signed URL

**Python:**
```python
from e2b import Sandbox

sandbox = Sandbox.create(timeout=12_000, secure=True)

# Create a pre-signed URL for file download with a 10-second expiration
signed_url = sandbox.download_url(
    path="demo.txt",
    user="user",
    use_signature_expiration=10_000
)
# The user only has to visit the URL to download the file
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create(template, { secure: true })

// Create a pre-signed URL for file download with a 10-second expiration
const publicUrl = await sandbox.downloadUrl('demo.txt', {
    useSignatureExpiration: 10_000, // optional
})

// Download a file with a pre-signed URL (works in a browser)
const res = await fetch(publicUrl)
const content = await res.text()
```

### Upload with Pre-signed URL

**Python:**
```python
from e2b import Sandbox
import requests

sandbox = Sandbox.create(timeout=12_000, secure=True)

# Create a pre-signed URL for file upload with a 10-second expiration
signed_url = sandbox.upload_url(
    path="demo.txt",
    user="user",
    use_signature_expiration=10_000
)

form_data = {"file": "file content"}
requests.post(signed_url, data=form_data)

# File is now available in the sandbox
content = sandbox.files.read('/path/in/sandbox')
```

**JavaScript:**
```javascript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create(template, { secure: true })

// Create a pre-signed URL for file upload with a 10-second expiration
const publicUploadUrl = await sandbox.uploadUrl('demo.txt', {
    useSignatureExpiration: 10_000, // optional
})

// Upload a file with a pre-signed URL (works in a browser)
const form = new FormData()
form.append('file', 'file content')
await fetch(publicUploadUrl, { method: 'POST', body: form })

// File is now available in the sandbox
const content = sandbox.files.read('/path/in/sandbox')
```

## File Paths Best Practices

### Use Absolute Paths

```python
# Good
sandbox.files.write('/home/user/data.csv', content)

# Bad - relative paths may not work as expected
sandbox.files.write('data.csv', content)
```

### Recommended Directory Structure

```
/home/user/
  data/           # Input datasets
    raw/
    processed/
  outputs/        # Generated files
    charts/
    reports/
  scripts/        # Code files
```

### Creating the Structure

```python
sandbox.commands.run('''
mkdir -p /home/user/data/raw
mkdir -p /home/user/data/processed
mkdir -p /home/user/outputs/charts
mkdir -p /home/user/outputs/reports
mkdir -p /home/user/scripts
''')
```

## Common Patterns

### Pattern 1: Upload Dataset, Run Analysis, Download Results

```python
# 1. Upload dataset
with open('sales_data.csv', 'rb') as f:
    sandbox.files.write('/home/user/data/sales.csv', f)

# 2. Run analysis
code = """
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('/home/user/data/sales.csv')
df.plot()
plt.savefig('/home/user/outputs/chart.png')
"""
sandbox.run_code(code)

# 3. Download result
chart = sandbox.files.read('/home/user/outputs/chart.png')
with open('sales_chart.png', 'wb') as f:
    f.write(chart)
```

### Pattern 2: Process Multiple Files

```python
# Upload multiple data files
for i, dataset in enumerate(datasets):
    path = f'/home/user/data/dataset_{i}.csv'
    sandbox.files.write(path, dataset)

# Process all at once
code = """
import pandas as pd
from pathlib import Path

data_files = list(Path('/home/user/data').glob('dataset_*.csv'))
dfs = [pd.read_csv(f) for f in data_files]
combined = pd.concat(dfs)
combined.to_csv('/home/user/outputs/combined.csv', index=False)
"""
sandbox.run_code(code)

# Download result
result = sandbox.files.read('/home/user/outputs/combined.csv')
```

### Pattern 3: Working with Binary Files

```python
# Upload image for processing
with open('input.jpg', 'rb') as f:
    sandbox.files.write('/home/user/image.jpg', f)

# Process image
code = """
from PIL import Image

img = Image.open('/home/user/image.jpg')
img = img.resize((800, 600))
img.save('/home/user/output.jpg')
"""
sandbox.run_code(code)

# Download processed image
output = sandbox.files.read('/home/user/output.jpg')
with open('output.jpg', 'wb') as f:
    f.write(output)
```

## Handling Different File Types

### Text Files

```python
# Write text file
sandbox.files.write('/home/user/message.txt', 'Hello, World!')

# Read text file
content = sandbox.files.read('/home/user/message.txt')
```

### CSV Files

```python
import csv
import io

output = io.StringIO()
writer = csv.writer(output)
writer.writerow(['Name', 'Age'])
writer.writerow(['Alice', 30])
csv_content = output.getvalue()

sandbox.files.write('/home/user/data.csv', csv_content)
```

### JSON Files

```python
import json

data = {'name': 'Alice', 'age': 30}
json_str = json.dumps(data)
sandbox.files.write('/home/user/data.json', json_str)

content = sandbox.files.read('/home/user/data.json')
data = json.loads(content)
```

## Troubleshooting

### File Not Found Errors

```python
# Check if file exists before reading
files = sandbox.files.list('/home/user')
file_paths = [f.path for f in files]

if '/home/user/data.csv' in file_paths:
    content = sandbox.files.read('/home/user/data.csv')
else:
    print("File not found")
```

### Permission Errors

Files in `/home/user/` should always be writable. If you get permission errors:

```python
sandbox.commands.run('chmod -R 755 /home/user')
```

### Large File Handling

For files larger than 10MB, consider:
1. Compressing before upload
2. Uploading to cloud storage and downloading in sandbox
3. Processing in chunks

```python
code = """
import urllib.request
url = 'https://example.com/large-dataset.csv'
urllib.request.urlretrieve(url, '/home/user/data.csv')
"""
sandbox.run_code(code)
```

### Disk Space Issues

Monitor disk usage:

```python
result = sandbox.commands.run('df -h /home/user')
print(result.stdout)

# Clean up temporary files
sandbox.commands.run('rm -rf /home/user/tmp/*')
```
