import os
import json
import time

from omni_learning_core import OmniLearner
from omni_data_listener import DataCollector
from omni_event_logger import EventLogger
from omni_vr_connector import OmniVRConnector
from omni_gcs_uploader import OmniGCSUploader


def load_config(path="omni_autolearn_config.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config '{path}': {e}")


def main():
    cfg_path = os.getenv("OMNI_AUTOSLEARN_CONFIG", "omni_autolearn_config.json")
    config = load_config(cfg_path)

    logger = EventLogger()
    learner = OmniLearner(config, logger=logger)
    collector = DataCollector(config, logger=logger)
    vr_connector = OmniVRConnector(config)
    gcs_uploader = OmniGCSUploader(config)

    logger.log("OMNI Auto-Learning System initialized.")
    logger.log(f"Learning mode: {config.get('learning_engine', {}).get('mode', 'unknown')}")
    logger.log("VR Connector initialized for AR/VR learning integration.")
    logger.log("GCS Uploader initialized for cloud storage integration.")

    try:
        while bool(config.get("system", {}).get("auto_learning", False)):
            # Zbere podatke iz senzorjev, očal ali API-jev
            data = collector.collect()
            vr_data = vr_connector.listen()
            if vr_data:
                data.append(vr_data)

            # AI se uči iz vseh vhodov
            learner.train(data)
            logger.log(f"Batch learned with {len(data)} items (VR data included).")

            # Auto-upload learning summaries to Google Cloud Storage
            try:
                gcs_uploader.check_and_upload()
            except Exception as e:
                logger.log(f"GCS upload check failed: {e}")

            time.sleep(int(config.get('learning_engine', {}).get('interval_seconds', 30)))
    except KeyboardInterrupt:
        logger.warn("Auto-learning interrupted by user.")
    except Exception as e:
        logger.error(f"Auto-learning crashed: {e}")


if __name__ == "__main__":
    main()