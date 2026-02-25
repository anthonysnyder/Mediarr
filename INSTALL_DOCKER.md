# Mediarr - Docker Installation Guide

Run Mediarr in a Docker container with persistent caching and data storage.

## Prerequisites

1. **Docker** and **Docker Compose** installed
2. **Media folders** accessible to Docker (NFS/SMB mount or local path)
3. **TMDb API Key** (free from https://www.themoviedb.org/settings/api)

## Quick Start

### 1. Create docker-compose.yml

```yaml
version: '3.8'

services:
  mediarr:
    image: swguru2004/mediarr:latest
    container_name: mediarr
    ports:
      - "6789:6789"
    environment:
      - TMDB_API_KEY=your_tmdb_api_key_here
      - MOVIE_FOLDERS=/movies,/kids-movies
      - TV_FOLDERS=/tv,/kids-tv,/anime
      - SLACK_WEBHOOK_URL=your_slack_webhook_url_here  # Optional
    volumes:
      # Update these paths to match your media locations
      - /mnt/nas/Movies:/movies
      - /mnt/nas/Kids Movies:/kids-movies
      - /mnt/nas/TV Shows:/tv
      - /mnt/nas/Kids TV:/kids-tv
      - /mnt/nas/Anime:/anime
      # Persistent cache and data
      - ./mediarr-data/artwork_cache:/app/artwork_cache
      - ./mediarr-data/unavailable_artwork.json:/app/unavailable_artwork.json
    restart: unless-stopped
```

### 2. Create Data Directory

```bash
mkdir -p mediarr-data/artwork_cache
touch mediarr-data/unavailable_artwork.json
```

### 3. Start Mediarr

```bash
docker-compose up -d
```

### 4. Access Mediarr

Open your browser to: **http://localhost:6789**

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `TMDB_API_KEY` | Yes | Your TMDb API key | `abc123...` |
| `MOVIE_FOLDERS` | No | Comma-separated movie paths | `/movies,/kids-movies` |
| `TV_FOLDERS` | No | Comma-separated TV paths | `/tv,/anime` |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for notifications | `https://hooks.slack.com/...` |
| `WATCHER_POLL_INTERVAL` | No | Poll interval in seconds for new media detection (default: `60`) | `60` |

**Default Paths:**
- Movies: `/movies`
- TV: `/tv`

### Volume Mounts

**Media Folders** (read/write access needed):
```yaml
volumes:
  - /your/movie/path:/movies
  - /your/tv/path:/tv
```

**Persistent Data** (required for cache and state):
```yaml
volumes:
  - ./mediarr-data/artwork_cache:/app/artwork_cache
  - ./mediarr-data/unavailable_artwork.json:/app/unavailable_artwork.json
```

## Using .env File (Recommended)

Create a `.env` file in the same directory as docker-compose.yml:

```bash
# TMDb Configuration
TMDB_API_KEY=your_tmdb_api_key_here

# Media Paths (update to match your setup)
MOVIE_FOLDERS=/movies,/kids-movies
TV_FOLDERS=/tv,/kids-tv,/anime

# Optional: Slack Notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url_here

# Optional: Watcher poll interval in seconds (default 60, safe for NFS/SMB)
# WATCHER_POLL_INTERVAL=60
```

Then simplify docker-compose.yml:

```yaml
environment:
  - TMDB_API_KEY=${TMDB_API_KEY}
  - MOVIE_FOLDERS=${MOVIE_FOLDERS:-/movies}
  - TV_FOLDERS=${TV_FOLDERS:-/tv}
  - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
```

## Docker Commands

### Start Mediarr
```bash
docker-compose up -d
```

### Stop Mediarr
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f mediarr
```

### Restart Mediarr
```bash
docker-compose restart mediarr
```

### Update to Latest Version
```bash
docker-compose pull
docker-compose up -d
```

### Clear Cache (if needed)
```bash
docker-compose down
rm -rf mediarr-data/artwork_cache/*
docker-compose up -d
```

## Advantages of Docker Deployment

- ✅ **Consistent Environment**: Same setup on any OS
- ✅ **Easy Updates**: `docker-compose pull` to update
- ✅ **Isolated**: Doesn't affect host system
- ✅ **Portable**: Move to any Docker-capable system
- ✅ **Resource Limits**: Can set memory/CPU limits

## Troubleshooting

### Cannot Access Mediarr

Check if container is running:
```bash
docker ps | grep mediarr
```

Check logs:
```bash
docker-compose logs mediarr
```

### Permission Issues

Ensure media folders are readable/writable:
```bash
# Check permissions
ls -la /path/to/your/movies

# Fix if needed (adjust UID/GID as needed)
chown -R 1000:1000 /path/to/your/movies
```

### Cache Not Persisting

Ensure volume is mounted correctly:
```bash
docker inspect mediarr | grep -A 10 Mounts
```

Check if data directory exists:
```bash
ls -la mediarr-data/
```

### TMDb API Not Working

Verify API key is set:
```bash
docker exec mediarr env | grep TMDB_API_KEY
```

## NAS-Specific Configurations

### Synology NAS

1. Enable Docker package in Package Center
2. Use Synology's file paths (e.g., `/volume1/Movies`)
3. Create project folder in Docker directory
4. Use Container Manager UI or SSH with docker-compose

### QNAP NAS

1. Install Container Station from App Center
2. Use QNAP paths (e.g., `/share/Multimedia/Movies`)
3. Create docker-compose.yml in Container Station
4. Deploy from Container Station UI

### Unraid

1. Add from Community Applications (if available)
2. Or use "Add Container" with custom settings:
   - Repository: `swguru2004/mediarr:latest`
   - Port: `6789 → 6789`
   - Paths: Map your media folders
   - Variables: Add TMDB_API_KEY

## Building Custom Image

To build your own image:

```bash
# Clone repository
git clone https://github.com/anthonysnyder/Mediarr.git
cd Mediarr

# Build image
docker build -t mediarr:local .

# Update docker-compose.yml to use local image
# image: mediarr:local

# Start
docker-compose up -d
```

## Support

For issues or questions:
- View logs: `docker-compose logs -f mediarr`
- Check GitHub Issues: https://github.com/anthonysnyder/Mediarr/issues
- Discord/Forum: [Add link if available]

## Uninstall

```bash
# Stop and remove container
docker-compose down

# Remove data (optional)
rm -rf mediarr-data

# Remove image (optional)
docker rmi swguru2004/mediarr:latest
```
