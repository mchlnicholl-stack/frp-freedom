#!/usr/bin/env python3
"""
FRP Freedom - Factory Reset Protection Bypass Tool
Main application entry point

This tool is designed for legitimate device recovery purposes only.
Users must ensure they have legal authorization before proceeding with any bypass operations.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.bypass.types import BypassResult
from src.core.config import Config
from src.core.device_manager import DeviceManager
from src.core.logger import setup_logging


def _run_automation(config: Config, serial: str = None) -> int:
    """Run the device scan and automated bypass flow without opening the GUI."""
    from src.bypass.bypass_manager import BypassManager

    device_manager = DeviceManager(config)
    devices = device_manager.scan_devices()

    if not devices:
        print("No Android devices detected. Connect a device and try again.")
        return 1

    if serial:
        target_device = next((device for device in devices if device.serial == serial), None)
        if target_device is None:
            print(f"Device with serial '{serial}' was not detected.")
            return 1
    else:
        target_device = devices[0]

    print(f"Auto-selecting device: {target_device.manufacturer} {target_device.model} ({target_device.serial})")

    bypass_manager = BypassManager(config, device_manager)
    recommended_methods = bypass_manager.get_recommended_methods(target_device)
    if not recommended_methods:
        print("No compatible bypass methods were found for the detected device.")
        return 1

    for method in recommended_methods:
        method_name = getattr(method, 'name', str(method))
        print(f"Attempting automated bypass via {method_name}...")
        result = bypass_manager.execute_bypass(target_device, method_name)
        status = result.get('result')
        message = result.get('message', 'No status returned')

        if status in (BypassResult.SUCCESS, BypassResult.PARTIAL):
            print(f"Automation succeeded with {method_name}: {message}")
            return 0

        print(f"Method {method_name} did not succeed: {message}")

    print("All automated bypass attempts failed.")
    return 1


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="FRP Freedom")
    parser.add_argument("--auto", action="store_true", help="Run the bypass flow without the GUI.")
    parser.add_argument("--serial", help="Target a specific device serial in auto mode.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    try:
        setup_logging()
        logger = logging.getLogger(__name__)

        logger.info("Starting FRP Freedom application")
        logger.info("Version: 1.0.0")
        logger.info("For legitimate device recovery purposes only")

        config = Config()
        if args.debug:
            config.set('app.debug_mode', True)
            config.set('security.encrypt_logs', False)
        else:
            config.set('app.debug_mode', False)
            config.set('security.encrypt_logs', True)

        if args.auto:
            return _run_automation(config, serial=args.serial)

        from src.gui.main_window import FRPFreedomApp

        app = FRPFreedomApp(config)
        app.run()
        return 0

    except KeyboardInterrupt:
        logger.warning("Application interrupted by user")
        return 130
    except Exception as e:
        logging.error(f"Fatal error starting application: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())