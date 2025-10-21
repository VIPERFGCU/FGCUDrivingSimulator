import carla
import os
from datetime import datetime

class CarlaScenarioRecorder:
    """
    ScenarioRecorder using CARLA's internal recorder.
    - Each tick is automatically recorded by CARLA.
    """

    def __init__(self, player, client: carla.Client, output_dir: str = "recordings", filename: str = None):
        self.player = player
        self.client = client
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Generate a timestamped filename if none provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scenario_{timestamp}.rec"  # Use .rec for CARLA recordings

        self.filepath = os.path.abspath(os.path.join(self.output_dir, filename))  # Absolute path
        self._recording = False

    def start(self):
        """Start CARLA internal recorder."""
        if not self._recording:
            self.client.start_recorder(self.filepath, True)  # True = record sensors too
            self._recording = True
            print(f"CARLA recorder started: {self.filepath}")

    def stop(self):
        """Stop CARLA internal recorder."""
        if self._recording:
            self.client.stop_recorder()
            self._recording = False
            print(f"CARLA recorder stopped: {self.filepath}")

    def record_frame(self):
        """
        Optional per-frame callback.
        CARLA recorder automatically records each tick.
        """
        if self._recording:
            transform = self.player.get_transform()
            velocity = self.player.get_velocity()
            print(f"Frame: pos={transform.location}, vel={velocity}")

    def get_metadata(self):
        """Return minimal metadata."""
        return {
            "filepath": self.filepath,
            "recording": self._recording
        }

    def replay(self, start: int = 0, duration: int = 0, camera: int = 0):
        """Replay the recorded scenario."""
        self.client.replay_file(self.filepath, start, duration, camera)
