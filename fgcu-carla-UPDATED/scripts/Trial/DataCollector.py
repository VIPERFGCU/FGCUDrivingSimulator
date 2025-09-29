import carla
import os
import datetime
import json
import threading
import queue


class ScenarioRecorder:
    """
    ScenarioRecorder for CARLA.
    - User calls `record_frame(actor)` every tick with the ego vehicle.
    - Recorder logs control inputs, position, velocity, etc.
    - A background thread handles saving to file asynchronously.
    """

    def __init__(self, player, client: carla.Client, output_dir: str = "recordings", filename = None):
        self._player = player
        self.client = client
        self.world = self.client.get_world()
        self.output_dir = output_dir

        self.recording = False
        self.recording_file = None
        self._stop_event = threading.Event()
        self._queue = queue.Queue()
        self._writer_thread = None

        self.metadata = {
            "start_time": None,
            "end_time": None,
            "map": None,
            "actors": [],
            "events": [],
            "controls": []  # logs of control inputs
        }

        os.makedirs(self.output_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scenario_{timestamp}.log"
        self.filename = filename

    def start(self):
        """Start recording a CARLA scenario."""
        if self.recording:
            print("[Recorder] Already recording.")
            return


        self.recording_file = os.path.join(self.output_dir, self.filename)

        # Start CARLA's native recording
        self.client.start_recorder(self.recording_file)

        # Metadata
        self.metadata["start_time"] = datetime.datetime.now().isoformat()
        self.metadata["map"] = self.world.get_map().name
        self.metadata["actors"] = [actor.type_id for actor in self.world.get_actors()]

        # Background writer thread
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

        # Stop CARLA recording
        self.client.stop_recorder()

        # Stop writer thread
        self._stop_event.set()
        if self._writer_thread:
            self._writer_thread.join()

        self.metadata["end_time"] = datetime.datetime.now().isoformat()

        # Save metadata alongside recording file
        meta_file = self.recording_file.replace(".log", ".json")
        with open(meta_file, "w") as f:
            json.dump(self.metadata, f, indent=4)

        print(f"[Recorder] Recording stopped. Metadata saved: {meta_file}")

        self.recording = False
        self.recording_file = None
        self._writer_thread = None

    def record_frame(self):
        """Call this once per frame with the ego vehicle actor."""
        if not self.recording or not self._player or not self._player.is_alive:
            return

        control = self._player.get_control()
        velocity = self._player.get_velocity()
        transform = self._player.get_transform()

        control_data = {
            "time": datetime.datetime.now().isoformat(),
            "throttle": control.throttle,
            "brake": control.brake,
            "steer": control.steer,
            "hand_brake": control.hand_brake,
            "reverse": control.reverse,
            "gear": control.gear,
            "speed": (velocity.x**2 + velocity.y**2 + velocity.z**2) ** 0.5,
            "location": {
                "x": transform.location.x,
                "y": transform.location.y,
                "z": transform.location.z
            },
            "rotation": {
                "pitch": transform.rotation.pitch,
                "yaw": transform.rotation.yaw,
                "roll": transform.rotation.roll
            }
        }

        # Enqueue frame data for async writing
        self._queue.put(control_data)

    def _writer_loop(self):
        """Background loop that consumes queue and writes into metadata."""
        while not self._stop_event.is_set() or not self._queue.empty():
            try:
                data = self._queue.get(timeout=0.1)
                self.metadata["controls"].append(data)
            except queue.Empty:
                continue

    def log_event(self, event_type: str, description: str, actor_id: int = None):
        """Log a custom event in the scenario metadata."""
        event = {
            "time": datetime.datetime.now().isoformat(),
            "type": event_type,
            "description": description,
            "actor_id": actor_id
        }
        self.metadata["events"].append(event)
        print(f"[Recorder] Event logged: {event}")

    def get_metadata(self):
        """Get current metadata dictionary."""
        return self.metadata

    def replay(self, start: int = 0, duration: int = 0, camera: int = 0):
        """
        Replay a recording inside CARLA.
        start: start time in seconds
        duration: 0 means until end
        camera: follow camera actor ID
        """
        if not self.recording_file:
            print("[Recorder] No recording file available to replay.")
            return
        self.client.replay_file(self.recording_file, start, duration, camera)
        print(f"[Recorder] Replaying file: {self.recording_file}")
