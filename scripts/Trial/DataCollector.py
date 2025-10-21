import carla
import os
import datetime
import json
import threading
import queue


class ScenarioRecorder:
    """
    ScenarioRecorder for CARLA.
    Logs player state & events asynchronously.
    """

    def __init__(self, player, client: carla.Client, output_dir: str = "recordings", filename=None):    # Make sure filename has .rec at the end
        self._player = player
        self.client = client
        self.world = self.client.get_world()
        self.output_dir = output_dir

        self.recording = False
        self.recording_file = None
        self._stop_event = threading.Event()
        self._queue = queue.Queue()
        self._writer_thread = None
        self._lock = threading.Lock()

        self.metadata = {
            "start_time": None,
            "end_time": None,
            "map": None,
            "actors": [],
            "events": [],  # event logs
        }

        os.makedirs(self.output_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scenario_{timestamp}.rec"  # For Carla internal use
        self.filename = filename

    def start(self):
        """Start recording a CARLA scenario."""
        if self.recording:
            print("[Recorder] Already recording.")
            return

        self.recording_file = os.path.join(self.output_dir, self.filename)

        # Start CARLA’s native recording
        self.client.start_recorder(self.recording_file)
        self.recorder_start_time = self.world.get_snapshot().timestamp.elapsed_seconds
        self.recorder_start_tick = self.world.get_snapshot().frame

        # Metadata setup
        # self.metadata["start_time"] = datetime.datetime.now().isoformat()
        self.metadata["start_time"] = self.recorder_start_time
        self.metadata["map"] = self.world.get_map().name
        self.metadata["actors"] = [actor.type_id for actor in self.world.get_actors()]

        # Start background writer
        self._stop_event.clear()
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()

        self.recording = True
        print(f"[Recorder] Started recording: {self.recording_file}")

    def stop(self):
        """Stop recording and save metadata."""
        if not self.recording:
            print("[Recorder] Not currently recording.")
            return

        self.client.stop_recorder()

        # Signal and join thread
        self._stop_event.set()
        if self._writer_thread:
            self._writer_thread.join()

        # Update end time
        self.metadata["end_time"] = self.world.get_snapshot().timestamp.elapsed_seconds

        # Save metadata
        meta_file = self.recording_file.replace(".rec", ".json")
        with self._lock:
            with open(meta_file, "w") as f:
                json.dump(self.metadata, f, indent=4)

        print(f"[Recorder] Recording stopped. Metadata saved: {meta_file}")

        self.recording = False
        self.recording_file = None
        self._writer_thread = None

    def log_event(self, event_name: str, additional_data_dict : dict = {}):
        """Log a custom event asynchronously."""
        if not self.recording or not self._player or not self._player.is_alive:
            return

        control = self._player.get_control()
        velocity = self._player.get_velocity()
        transform = self._player.get_transform()
        snapshot = self.world.get_snapshot()

        event_data = {
            "event_type": event_name,
            "tick": snapshot.frame - self.recorder_start_tick,
            "time": snapshot.timestamp.elapsed_seconds -  self.recorder_start_time,
            "speed": (velocity.x**2 + velocity.y**2 + velocity.z**2) ** 0.5,
            "location": {
                "x": transform.location.x,
                "y": transform.location.y,
                "z": transform.location.z
            },
            # "control": {
            #     "throttle": control.throttle,
            #     "brake": control.brake,
            #     "steer": control.steer,
            #     "reverse": control.reverse
            # }
        }

        event_data.update(additional_data_dict)

        # Enqueue for background writer
        self._queue.put(event_data)

    def _writer_loop(self):
        """Background loop that consumes the queue and stores events."""
        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                data = self._queue.get(timeout=0.1)
                with self._lock:
                    self.metadata["events"].append(data)
            except queue.Empty:
                continue

    def get_metadata(self):
        """Return a snapshot of metadata."""
        with self._lock:
            return dict(self.metadata)
