import json
from pathlib import Path
import shutil
import time
import libtorrent as lt
from constants import VIDEO_EXTENSIONS
from jellyfinIntegreation import triggerRefresh


class MultiTorrentManager:

    def __init__(self):
        self.ses = lt.session(
            {
                "listen_interfaces": "0.0.0.0:6881",
            }
        )

        self.ses.set_alert_mask(
            lt.alert.category_t.error_notification
            | lt.alert.category_t.status_notification
            | lt.alert.category_t.storage_notification
            | lt.alert.category_t.tracker_notification
            | lt.alert.category_t.progress_notification
            | lt.alert.category_t.dht_notification
        )

        self.handles = {}

        # Persistent state
        self.state_dir = Path("/var/lib/mytorrentmanager")
        self.resume_dir = self.state_dir / "resume"
        self.metadata_file = self.state_dir / "torrents.json"

        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.resume_dir.mkdir(parents=True, exist_ok=True)

        self.last_resume_save = time.time()

        # Restore torrents from disk
        self.load_torrents()

    def save_metadata(self):
        metadata = {}

        for info_hash, torrent in self.handles.items():
            metadata[info_hash] = {
                "imdb": torrent["imdb"],
                "filename": torrent["filename"],
                "type": torrent["type"],
                "save_path": torrent["save_path"],
            }

        temp_path = self.metadata_file.with_suffix(".tmp")

        try:
            with temp_path.open("w") as f:
                json.dump(
                    metadata,
                    f,
                    indent=2,
                )

            temp_path.replace(self.metadata_file)

        except Exception as e:
            print(f"Could not save metadata: {e}",flush=True)

    def load_torrents(self):
        if not self.metadata_file.exists():
            print("No previous torrent metadata found.",flush=True)
            return

        try:
            with self.metadata_file.open("r") as f:
                metadata = json.load(f)

        except Exception as e:
            print(f"Could not read torrent metadata: {e}",flush=True)
            return

        for info_hash, data in metadata.items():

            resume_path = self.resume_dir / f"{info_hash}.resume"

            if not resume_path.exists():
                print(f"No resume data found for " f"{info_hash[:10]}...",flush=True)
                continue

            try:
                with resume_path.open("rb") as f:
                    resume_data = f.read()

                if not resume_data:
                    print(f"Resume file is empty for " f"{info_hash[:10]}...",flush=True)
                    continue

                params = lt.read_resume_data(resume_data)

                handle = self.ses.add_torrent(params)

                self.handles[info_hash] = {
                    "handle": handle,
                    "imdb": data["imdb"],
                    "filename": data["filename"],
                    "type": data["type"],
                    "save_path": data["save_path"],
                }

                print(f"Restored torrent: " f"{info_hash[:10]}...",flush=True)

            except Exception as e:
                print(f"Could not restore torrent " f"{info_hash[:10]}...: {e}",flush=True)

    def add_torrent(
        self,
        imdb,
        magnet,
        save_path,
        filename,
    ):
        print("========== ADD TORRENT ==========",flush=True)
        print(f"IMDb: {imdb}",flush=True)
        print(f"Magnet: {magnet[:100]}...",flush=True)
        print(f"Save path: {save_path}",flush=True)
        print(f"Filename: {filename}",flush=True)

        try:
            print("Parsing magnet...",flush=True)

            params = lt.parse_magnet_uri(magnet)

            print("Magnet parsed successfully.",flush=True)

            params.save_path = str(save_path)

            print("Adding torrent to libtorrent...",flush=True)

            handle = self.ses.add_torrent(params)

            print("Torrent added to libtorrent.",flush=True)

            info_hash = str(handle.info_hash())

            print(f"Info hash: {info_hash}",flush=True)

            self.handles[info_hash] = {
                "handle": handle,
                "imdb": imdb,
                "filename": filename,
                "type": "signal",
                "save_path": str(save_path),
            }

            self.save_metadata()

            print("Metadata saved.",flush=True)

            handle.save_resume_data()

            print("Resume data requested.",flush=True)

            print(f"Added torrent: {info_hash[:10]}...",flush=True)

            return info_hash

        except Exception as e:
            print(f"Could not add torrent: {type(e).__name__}: {e}",flush=True)

            import traceback

            traceback.print_exc()

            return None

    def add_season_torrent(
        self,
        imdb,
        magnet,
        save_path,
        filename,
    ):
        print("========== ADD SEASON TORRENT ==========",flush=True)
        print(f"IMDb: {imdb}",flush=True)
        print(f"Magnet: {magnet[:100]}...",flush=True)
        print(f"Save path: {save_path}",flush=True)
        print(f"Filename: {filename}",flush=True)

        try:
            print("Parsing magnet...",flush=True)

            params = lt.parse_magnet_uri(magnet)

            print("Magnet parsed successfully.",flush=True)

            params.save_path = str(save_path)

            print("Adding season torrent to libtorrent...",flush=True)

            handle = self.ses.add_torrent(params)

            print("Season torrent added to libtorrent.",flush=True)

            info_hash = str(handle.info_hash())

            print(f"Info hash: {info_hash}",flush=True)

            self.handles[info_hash] = {
                "handle": handle,
                "imdb": imdb,
                "filename": filename,
                "type": "season",
                "save_path": str(save_path),
            }

            self.save_metadata()

            print("Metadata saved.",flush=True)

            handle.save_resume_data()

            print("Resume data requested.",flush=True)

            print(f"Added season torrent: " f"{info_hash[:10]}...",flush=True)

            return info_hash

        except Exception as e:
            print(f"Could not add season torrent: " f"{type(e).__name__}: {e}",flush=True)

            import traceback

            traceback.print_exc()

            return None

    def save_resume_data(self, alert):

        try:
            handle = alert.handle

            status = handle.status()

            info_hash = str(status.info_hashes.get_best())

            resume_path = self.resume_dir / f"{info_hash}.resume"

            # libtorrent 2.x
            # Returns serialized bytes
            resume_data = lt.write_resume_data_buf(alert.params)

            temp_path = resume_path.with_suffix(".tmp")

            with temp_path.open("wb") as f:
                f.write(resume_data)

            # Atomic replacement
            temp_path.replace(resume_path)

            print(
                f"Saved resume data: "
                f"{info_hash[:10]}... "
                f"({len(resume_data)} bytes)"
                ,flush=True
            )

        except Exception as e:
            print(f"Could not save resume data: " f"{e}",flush=True)

    # ---------------------------------------------------------
    # Request resume data for all torrents
    # ---------------------------------------------------------

    def save_all_resume_data(self):

        for info_hash, torrent in list(self.handles.items()):
            try:
                torrent["handle"].save_resume_data()

            except Exception as e:
                print(f"Could not request resume data " f"for {info_hash[:10]}...: {e}",flush=True)

    # ---------------------------------------------------------
    # Delete resume data
    # ---------------------------------------------------------

    def delete_resume_data(self, info_hash):

        resume_path = self.resume_dir / f"{info_hash}.resume"

        try:
            if resume_path.exists():
                resume_path.unlink()

        except Exception as e:
            print(f"Could not delete resume data " f"for {info_hash[:10]}...: {e}",flush=True)

    # ---------------------------------------------------------
    # Remove torrent
    # ---------------------------------------------------------

    def remove_torrent(
        self,
        info_hash,
        delete_files=False,
    ):
        torrent = self.handles.get(info_hash)

        if not torrent:
            return False

        try:
            handle = torrent["handle"]

            self.ses.remove_torrent(
                handle, lt.options_t.delete_files if delete_files else 0
            )

            del self.handles[info_hash]

            self.delete_resume_data(info_hash)

            self.save_metadata()

            print(f"Removed torrent: " f"{info_hash[:10]}...",flush=True)

            return True

        except Exception as e:
            print(f"Could not remove torrent " f"{info_hash[:10]}...: {e}",flush=True)
            return False

    def get_all_torrents(self):

        torrentsdata = []

        for info_hash, data in list(self.handles.items()):

            handle: lt.torrent_handle = data["handle"]

            status = handle.status()

            name = (
                status.name if status.has_metadata else f"Metadata... ({info_hash[:8]})"
            )

            name = (name[:22] + "...") if len(name) > 25 else name

            progress = f"{status.progress * 100:.1f}%"

            # Time left

            remaining = status.total_wanted - status.total_wanted_done

            download_rate = status.download_rate

            if download_rate > 0:

                seconds_left = remaining / download_rate

                hours, remainder = divmod(int(seconds_left), 3600)

                minutes, seconds = divmod(remainder, 60)

                if hours:

                    time_left = f"{hours}h {minutes}m"

                elif minutes:

                    time_left = f"{minutes}m {seconds}s"

                else:

                    time_left = f"{seconds}s"

            else:

                time_left = "∞"

            speed = f"{status.download_rate / 1000:,.1f} kB/s"
            total_size = "0"
            try:
                total_size = sum(f.size for f in handle.torrent_file().files())  # type: ignore
            except Exception as e:
                pass
            total_download = status.total_download
            state = str(status.state)
            status.total_download
            torrentsdata.append(
                {
                    "name": name,
                    "progress": progress,
                    "speed": speed,
                    "time_left": time_left,
                    "state": state,
                    "total_size": total_size,
                    "total_download": total_download,
                    "info_hash": info_hash
                }
            )

        return torrentsdata

    def get_video_files(self, directory):

        video_files = []

        directory = Path(directory)

        if not directory.exists():
            return video_files

        for path in directory.rglob("*"):

            if not path.is_file():
                continue

            if path.suffix.lower() in VIDEO_EXTENSIONS:
                video_files.append(path)
            else:
                path.unlink()
        return video_files

    def process_completed_torrent(
        self, info_hash, torrent, current_torrent_directory: Path
    ):
        handle = torrent["handle"]

        current_torrent_directory = Path(current_torrent_directory)
        filename = torrent["filename"]

        torrent_type = torrent["type"]

        video_files = self.get_video_files(current_torrent_directory)

        if not video_files:
            print(f"No video files found for " f"{info_hash[:10]}...",flush=True)
            return False

        if torrent_type == "signal":

            video_file = video_files[0]

            extension = video_file.suffix

            target = current_torrent_directory / f"{filename}{extension}"

            try:

                # Delete all non-video files
                for path in current_torrent_directory.rglob("*"):

                    if path.is_file() and path not in video_files:
                        try:
                            path.unlink()
                        except Exception as e:
                            print(f"Could not delete " f"{path}: {e}")

                if video_file != target:

                    if target.exists():
                        target.unlink()

                    video_file.rename(target)

                print(f"Completed torrent: " f"{filename}")

                return True

            except Exception as e:
                print(f"Could not process " f"{filename}: {e}")
                return False

        if torrent_type == "season":
            video_files.sort(key=lambda x: x.name.lower())

            try:

                for index, video_file in enumerate(
                    video_files,
                    start=1,
                ):

                    extension = video_file.suffix

                    target = (
                        current_torrent_directory / f"{filename}"
                        f"E{index:02d}"
                        f"{extension}"
                    )

                    if video_file != target:

                        if target.exists():
                            target.unlink()

                        video_file.rename(target)
                print(f"Completed season torrent: " f"{filename}",flush=True)
                for item in current_torrent_directory.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item) 
                return True

            except Exception as e:
                print(f"Could not process season " f"{filename}: {e}",flush=True)
                return False

        return False

    def periodic(self):

        # Save resume data every 30 seconds
        now = time.time()

        if now - self.last_resume_save >= 30:

            self.save_all_resume_data()

            self.last_resume_save = now

        # Process alerts
        alerts = self.ses.pop_alerts()

        for alert in alerts:
            print(alert)
            if isinstance(
                alert,
                lt.save_resume_data_alert,
            ):

                self.save_resume_data(alert)

            elif isinstance(
                alert,
                lt.torrent_finished_alert,
            ):

                try:
                    status = alert.handle.status()

                    info_hash = str(status.info_hashes.get_best())

                    torrent = self.handles.get(info_hash)

                    if not torrent:
                        continue

                    print(f"Torrent finished: " f"{info_hash[:10]}...", flush=True)
                    torrent_info = alert.handle.torrent_file()
                    save_directory = Path("")
                    if torrent_info:
                        files_storage = torrent_info.files()
                        save_directory = Path(status.save_path)
                    success = self.process_completed_torrent(
                        info_hash, torrent, save_directory
                    )

                    if success:

                        # If you have triggerRefresh()
                        # in your application, call it here.
                        try:
                            triggerRefresh()
                        except AttributeError:
                            pass

                        self.remove_torrent(
                            info_hash,
                            delete_files=False,
                        )

                except Exception as e:

                    print(f"Error processing finished " f"torrent: {e}",flush=True)

    def shutdown(self):

        print("Shutting down torrent manager...",flush=True)

        try:
            # Request final resume data
            self.save_all_resume_data()

            # Give libtorrent a moment to generate
            # the save_resume_data alerts.
            deadline = time.time() + 5

            while time.time() < deadline:

                alerts = self.ses.pop_alerts()

                for alert in alerts:

                    if isinstance(
                        alert,
                        lt.save_resume_data_alert,
                    ):
                        self.save_resume_data(alert)

                time.sleep(0.1)

        except Exception as e:
            print(f"Error during shutdown: {e}",flush=True)

        print("Torrent manager stopped.",flush=True)
