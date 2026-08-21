"""
Watch the Obsidian vault and re-run the converter when markdown files change.
Usage: python scripts\watch_and_build.py -v ../absurdly-goud-obsidian -c scripts/obsidian_to_jekyll_old.py

Requires: watchdog (pip install watchdog)
"""
import argparse
import subprocess
import sys
import time
import threading
import os
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    print("Missing dependency 'watchdog'. Install with: python -m pip install watchdog")
    sys.exit(2)


def run_converter(converter, cwd=None):
    print(f"Running converter: {converter}")
    try:
        res = subprocess.run([sys.executable, converter], cwd=cwd, check=False)
        if res.returncode != 0:
            print(f"Converter exited with code {res.returncode}")
    except Exception as e:
        print(f"Failed to run converter: {e}")


class DebounceHandler(FileSystemEventHandler):
    def __init__(self, callback, debounce_seconds=0.8, patterns=('.md', '.markdown')):
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.timer = None
        self.lock = threading.Lock()
        self.patterns = patterns

    def _schedule(self):
        with self.lock:
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(self.debounce_seconds, self._run)
            self.timer.daemon = True
            self.timer.start()

    def _run(self):
        with self.lock:
            self.timer = None
        self.callback()

    def _is_relevant(self, event):
        # ignore directory events
        if event.is_directory:
            return False
        p = str(event.src_path).lower()
        return any(p.endswith(ext) for ext in self.patterns)

    def on_modified(self, event):
        if self._is_relevant(event):
            print(f"Modified: {event.src_path}")
            self._schedule()

    def on_created(self, event):
        if self._is_relevant(event):
            print(f"Created: {event.src_path}")
            self._schedule()

    def on_deleted(self, event):
        if self._is_relevant(event):
            print(f"Deleted: {event.src_path}")
            self._schedule()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-v', '--vault', default='absurdly-goud-obsidian', help='Path to obsidian vault (watched)')
    p.add_argument('-c', '--converter', default='scripts/obsidian_to_jekyll_old.py', help='Path to converter script')
    p.add_argument('-d', '--debounce', type=float, default=0.8, help='Debounce seconds')
    args = p.parse_args()

    vault = Path(args.vault).resolve()
    converter = Path(args.converter).resolve()

    if not vault.exists():
        print(f"Vault path does not exist: {vault}")
        sys.exit(1)
    if not converter.exists():
        print(f"Converter not found: {converter}")
        sys.exit(1)

    # Run converter once at start
    run_converter(str(converter), cwd=str(Path('.').resolve()))

    event_handler = DebounceHandler(lambda: run_converter(str(converter), cwd=str(Path('.').resolve())), debounce_seconds=args.debounce)
    observer = Observer()
    observer.schedule(event_handler, str(vault), recursive=True)

    print(f"Watching {vault} for changes. Press Ctrl+C to stop.")

    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping watcher...")
        observer.stop()
    observer.join()


if __name__ == '__main__':
    main()
