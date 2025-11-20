# Dify Workflows DSL Exporter

A Python tool to quickly export all your Dify workflows/applications as DSL (Domain-Specific Language) YAML files via the Dify API. This tool allows you to backup, version control, and migrate your Dify workflows efficiently.

## Quick Reference

```bash
# 1. Install Poetry (one-time setup)
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# 2. Setup project
git clone <repository-url>
cd dify-apps-dsl-exporter
poetry install

# 3. Configure credentials
cp .env.example .env
# Edit .env with your Dify credentials

# 4. Export all workflows
poetry run python src/export.py
```

**Output**: All workflows are saved as YAML files in `./dsl/` directory.

## Features

- ✅ **Bulk Export**: Export all workflows from your Dify instance in one command
- ✅ **Fast & Concurrent**: Uses async requests for fast downloads
- ✅ **Automatic Naming**: Files are named after your workflow titles
- ✅ **Duplicate Handling**: Automatically handles workflows with duplicate names
- ✅ **Cookie-based Auth**: Supports Dify's cookie-based authentication
- ✅ **Error Handling**: Retries failed requests automatically

## Requirements

- **Python 3.13+** (or Python 3.10+)
- **Poetry** (for dependency management)

## Quick Start

### 1. Install Poetry (if not already installed)

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to your PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/sattosan/dify-apps-dsl-exporter.git
cd dify-apps-dsl-exporter

# Install dependencies
poetry install
```

### 3. Configure Your Dify Credentials

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your Dify instance details:

```env
DIFY_ORIGIN=https://dify.dctrl.ai  # Your Dify instance URL (no trailing slash)
EMAIL=your-email@example.com        # Your Dify login email
PASSWORD=your-password              # Your Dify login password
```

**Important Notes:**
- Remove any trailing slashes from `DIFY_ORIGIN` (e.g., use `https://dify.dctrl.ai` not `https://dify.dctrl.ai/`)
- For self-hosted instances, use your full URL (e.g., `http://localhost:3000`)
- For cloud instances, use the full domain (e.g., `https://api.dify.ai`)

### 4. Export All Workflows

```bash
# Make sure Poetry is in your PATH
export PATH="$HOME/.local/bin:$PATH"

# Run the export script
poetry run python src/export.py
```

The script will:
1. Authenticate with your Dify instance
2. Fetch all your workflows/applications
3. Download each workflow's DSL file as YAML
4. Save them to the `./dsl` folder

**Example Output:**
```
Login successful - using cookie-based authentication
Total apps: 25, Total pages: 1
Same name app count: 1, renamed list: ['openai_benchmark_rag -> 【same】openai_benchmark_rag-9c8c995f']
Starting to download YML files...
✅ Downloaded: ./dsl/Benchmarking-prod.yml
✅ Downloaded: ./dsl/demo_RAG.yml
...
```

## Output

All exported workflows are saved in the `./dsl/` directory as YAML files:

```
dsl/
├── Benchmarking-prod.yml
├── demo_RAG.yml
├── get_history.yml
└── ...
```

- Files are named after your workflow titles
- Duplicate names are automatically prefixed with `【same】` and an ID
- Each file contains the complete DSL definition of the workflow

## Additional Features

### Import Workflows

To import workflows from the `./dsl/` folder back into Dify:

```bash
poetry run python src/import.py
```

### Delete All Workflows

⚠️ **Warning**: This will delete all workflows from your Dify instance!

```bash
poetry run python src/delete.py
```

## Troubleshooting

### Poetry Command Not Found

If you get `command not found: poetry`, add Poetry to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Or add it permanently to your shell config (`~/.zshrc` or `~/.bashrc`):

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Authentication Errors (401 Unauthorized)

- **Check your credentials**: Verify your email and password in `.env`
- **Check the URL**: Ensure `DIFY_ORIGIN` is correct and has no trailing slash
- **Check API access**: For self-hosted instances, ensure API access is enabled

### No Workflows Found

- Verify you have workflows in your Dify instance
- Check that your account has access to the workflows
- Ensure the Dify instance URL is correct

### Connection Errors

- Verify your Dify instance is accessible
- Check network connectivity
- For self-hosted instances, ensure the server is running

## How It Works

1. **Authentication**: The script logs in to Dify using your credentials and receives session cookies
2. **Token Extraction**: Extracts the JWT access token from cookies for API authentication
3. **Pagination**: Fetches all workflows using paginated API requests
4. **Concurrent Downloads**: Downloads DSL files concurrently (up to 3 at a time) for speed
5. **File Naming**: Sanitizes workflow names for filesystem compatibility

## Project Structure

```
dify-apps-dsl-exporter/
├── src/
│   ├── export.py      # Main export script
│   ├── import.py      # Import workflows script
│   ├── delete.py      # Delete workflows script
│   └── dify_api.py    # Dify API client
├── dsl/               # Exported workflow files (created after export)
├── .env               # Your credentials (create from .env.example)
├── .env.example       # Example configuration file
├── pyproject.toml     # Poetry dependencies
└── README.md          # This file
```

## Security Notes

- **Never commit `.env`**: The `.env` file contains your credentials and should be in `.gitignore`
- **Keep credentials secure**: Share credentials only through secure channels
- **Use environment variables**: For CI/CD, consider using environment variables instead of `.env` files

## Contributing

This is a community-maintained tool. Contributions are welcome!

## License

See the repository for license information.

## Sharing with Your Team

To share this tool with your team:

1. **Share the repository**: Clone or fork this repository
2. **Each team member sets up their own `.env`**: 
   - Each person should create their own `.env` file with their credentials
   - Never commit `.env` files to version control
3. **Quick setup for team members**:
   ```bash
   git clone <repository-url>
   cd dify-apps-dsl-exporter
   poetry install
   cp .env.example .env
   # Edit .env with their credentials
   poetry run python src/export.py
   ```

### Team Workflow

1. **Export workflows** regularly to backup your work
2. **Version control the DSL files**: Commit the `dsl/` folder to git for version history
3. **Share workflows**: Team members can import workflows from the `dsl/` folder

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the error messages for specific guidance
- Open an issue on the GitHub repository
