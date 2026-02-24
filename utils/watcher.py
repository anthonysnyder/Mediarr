"""
Filesystem watcher for automatically detecting new media directories.

Uses PollingObserver instead of the default inotify/FSEvents observer
because NFS/SMB mounts don't propagate kernel filesystem events reliably.
The polling approach compares directory snapshots on each interval.
"""
import os
import threading
import time

from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler


class MediaFolderEventHandler(FileSystemEventHandler):
    """Handles directory-creation events for a set of media base folders."""

    def __init__(self, media_type, base_folders, on_new_directory, settle_delay=5):
        """
        Args:
            media_type:       'movie' or 'tv'
            base_folders:     iterable of base folder paths this handler watches
            on_new_directory: callback(media_type, dir_name, dir_path)
            settle_delay:     seconds to wait after detection before firing the
                              callback, giving the download time to fully land
        """
        super().__init__()
        self.media_type = media_type
        # Normalise so path comparisons are consistent
        self.base_folders = {os.path.normpath(f) for f in base_folders}
        self.on_new_directory = on_new_directory
        self.settle_delay = settle_delay
        # Track in-flight events to suppress duplicates within the same poll cycle
        self._pending = set()
        self._lock = threading.Lock()

    def on_created(self, event):
        if not event.is_directory:
            return

        src_path = os.path.normpath(event.src_path)
        parent = os.path.dirname(src_path)

        # Only react to directories created directly inside a watched base folder,
        # not to sub-directories within a media title's own folder.
        if parent not in self.base_folders:
            return

        with self._lock:
            if src_path in self._pending:
                return
            self._pending.add(src_path)

        dir_name = os.path.basename(src_path)
        print(f"[Watcher] New {self.media_type} directory detected: {dir_name}", flush=True)

        t = threading.Thread(
            target=self._settle_and_notify,
            args=(dir_name, src_path),
            daemon=True,
            name=f"watcher-{self.media_type}-{dir_name[:24]}",
        )
        t.start()

    def _settle_and_notify(self, dir_name, dir_path):
        """Wait for the directory to settle, then invoke the cache callback."""
        time.sleep(self.settle_delay)
        try:
            self.on_new_directory(self.media_type, dir_name, dir_path)
        except Exception as e:
            print(f"[Watcher] Error processing '{dir_name}': {e}", flush=True)
        finally:
            with self._lock:
                self._pending.discard(dir_path)


def start_media_watcher(movie_folders, tv_folders, on_new_directory, poll_interval=60):
    """
    Start polling filesystem watchers for movie and TV base folders.

    Args:
        movie_folders:    list of movie base folder paths
        tv_folders:       list of TV base folder paths
        on_new_directory: callback(media_type, dir_name, dir_path)
        poll_interval:    polling interval in seconds (60s is a safe default for NFS)

    Returns:
        Running PollingObserver, or None if no valid folders were found.
    """
    observer = PollingObserver(timeout=poll_interval)

    movie_handler = MediaFolderEventHandler('movie', movie_folders, on_new_directory)
    tv_handler = MediaFolderEventHandler('tv', tv_folders, on_new_directory)

    scheduled = 0

    for folder in movie_folders:
        if os.path.isdir(folder):
            observer.schedule(movie_handler, folder, recursive=False)
            print(f"[Watcher] Monitoring movie folder: {folder}", flush=True)
            scheduled += 1
        else:
            print(f"[Watcher] Movie folder not accessible at startup, skipping: {folder}", flush=True)

    for folder in tv_folders:
        if os.path.isdir(folder):
            observer.schedule(tv_handler, folder, recursive=False)
            print(f"[Watcher] Monitoring TV folder: {folder}", flush=True)
            scheduled += 1
        else:
            print(f"[Watcher] TV folder not accessible at startup, skipping: {folder}", flush=True)

    if scheduled == 0:
        print(
            "[Watcher] No accessible folders found — watcher not started. "
            "Trigger a manual rescan once the mount is available.",
            flush=True,
        )
        return None

    observer.start()
    print(
        f"[Watcher] Polling observer started "
        f"(interval={poll_interval}s, {scheduled} folder(s) monitored)",
        flush=True,
    )
    return observer
