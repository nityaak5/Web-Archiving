# Web-Archiving
A repository to test web archiving automatically when a yaml file with links is added- using GitHub Actions

## Features

- Automatically detects when YAML files are added or modified
- Extracts all URLs from YAML files, including both single links and lists of links
- Archives each link using multiple services (Wayback Machine and Archive.today)
- Maintains a log of all archived links, including timestamps and archive status
- Commits the log back to your repository for permanent record-keeping

## How It Works

1. When you push changes to your repository that include YAML files, the GitHub Actions workflow is triggered
2. The workflow extracts all links from the modified YAML files
3. Each link is submitted to archive services
4. A comprehensive log is maintained in the `logs/archive_log.json` file
5. This log is automatically committed back to your repository

## Setup Instructions

1. Fork or clone this repository
2. Add your YAML files to the repository
3. Push to GitHub - links will be automatically archived
4. Check the `logs/archive_log.json` file for the results

## Example

If you have a YAML file like:

```yaml
system:
  name: ChatMusician
  link: https://huggingface.co/m-a-p/ChatMusician
org:
  name: Multimodal Art Projection
  link: https://m-a-p.ai/
  repos:
    - link: https://github.com/hf-lin/ChatMusician
    - link: https://huggingface.co/datasets/m-a-p/MusicPile
```

The archiver will extract and archive all four links.

## Log Format

The log file (`logs/archive_log.json`) contains entries like:

```json
{
  "archived_links": {
    "https://huggingface.co/m-a-p/ChatMusician": {
      "original_url": "https://huggingface.co/m-a-p/ChatMusician",
      "first_seen": "2025-05-07T14:30:00.000000",
      "files": ["models/chatmusician.yaml"],
      "services": {
        "wayback_machine": {
          "success": true,
          "archived_url": "https://web.archive.org/web/20250507143000/https://huggingface.co/m-a-p/ChatMusician"
        },
        "archive_today": {
          "success": true,
          "archived_url": "https://archive.today/abcd1"
        }
      }
    }
  }
}
```

## Technical Details:

- Written in Python with minimal dependencies
- Uses GitHub Actions for automation
- Respects rate limits of archiving services
- Retries failed archiving attempts with exponential backoff

