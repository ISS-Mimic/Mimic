from __future__ import annotations
import threading
import subprocess
import pathlib
import os
import math
import json
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    log_info("MainScreen: requests module not available, GitHub update checking disabled")
from kivy.clock import Clock

from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.lang import Builder

from utils.logger import log_info, log_error

kv_path = pathlib.Path(__file__).with_name("MainScreen.kv")
Builder.load_file(str(kv_path))

class MainScreen(Screen):
    """
    Home screen. Handles navigation to other screens and the EXIT button.
    """

    mimic_directory = pathlib.Path(__file__).resolve().parents[3]   # …/Mimic
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        log_info(f"MainScreen: mimic_directory set to: {self.mimic_directory}")
        log_info(f"MainScreen: Current working directory: {os.getcwd()}")
    
    # ISS animation variables
    _iss1_x: float = 0.0
    _iss1_y: float = 0.75
    _iss1_size_x: float = 0.07
    _iss1_size_y: float = 0.07
    _iss1_starting: bool = True
    
    _iss2_x: float = 0.0
    _iss2_y: float = 0.75

    def killproc(self, *_):
        """
        EXIT button callback — guaranteed to shut everything down.
    
        * UI thread:   closes the window right away (app.stop()).
        * Worker thread: terminates helper processes, cleans temp files,
          then forces *hard* interpreter exit via `os._exit(0)`.
        """
    
        if getattr(self, "_exiting", False):
            return                      # double-click guard
        self._exiting = True
    
        app = App.get_running_app()
        app.stop()                      # ⇢ window disappears instantly
    
        # ------------------------------------------------------------
        # launch daemon thread to finish cleanup in background
        # ------------------------------------------------------------
        threading.Thread(
            target=self._background_cleanup_and_exit,
            daemon=True
        ).start()
    
    
    # ──────────────────────────────────────────────────────────────
    # runs in a daemon thread; UI already closed
    # ──────────────────────────────────────────────────────────────
    def _background_cleanup_and_exit(self):
        app = App.get_running_app()
    
        # 1) stop observer
        observer = getattr(app, "tty_observer", None)
        if observer:
            try:
                observer.stop()
                log_info("TTY observer stopped.")
            except Exception as exc:
                log_error(f"Error stopping observer: {exc}")
    
        # 2) terminate helper subprocesses
        for attr in (
            "p", "TDRSproc",
            "demo_proc", "disco_proc",
            "htv_proc", "oft2_proc",
        ):
            self._terminate_attr(app, attr)
    
        # 3) wipe temporary sqlite caches
        for db in pathlib.Path("/dev/shm").glob("*.db*"):
            try:
                db.unlink()
            except OSError as exc:
                log_error(f"Could not remove {db}: {exc}")
    
        # 4) done – force interpreter exit (bypasses lingering threads)
        os._exit(0)                     # ← never returns
    
    def on_pre_enter(self, *_):
        """Start ISS animations when entering the screen."""
        self._start_iss_animations()
        self._start_arduino_monitoring()
        # Reset status label to welcome message
        if hasattr(self, 'ids') and 'status_label' in self.ids:
            self.ids.status_label.text = 'Welcome to ISS Mimic!'
        # Do an initial GitHub check after a short delay
        Clock.schedule_once(lambda dt: self._check_and_update_github_status(), 2.0)
    
    def on_pre_leave(self, *_):
        """Stop ISS animations when leaving the screen."""
        self._stop_iss_animations()
        self._stop_arduino_monitoring()
    
    def _start_iss_animations(self):
        """Start the ISS animation timers."""
        try:
            # Start the first ISS animation
            self._iss1_animation_event = Clock.schedule_interval(self._animate_iss1, 0.1)
            log_info("MainScreen: ISS animations started")
        except Exception as exc:
            log_error(f"Failed to start ISS animations: {exc}")
    
    def _stop_iss_animations(self):
        """Stop the ISS animation timers."""
        try:
            if hasattr(self, '_iss1_animation_event'):
                self._iss1_animation_event.cancel()
            if hasattr(self, '_iss2_animation_event'):
                self._iss2_animation_event.cancel()
            log_info("MainScreen: ISS animations stopped")
        except Exception as exc:
            log_error(f"Failed to stop ISS animations: {exc}")
    
    def _animate_iss1(self, dt):
        """Animate the first ISS icon (ISStiny)."""
        try:
            if self._iss1_x < 0.886:
                self._iss1_x += 0.007
                self._iss1_y = (math.sin(self._iss1_x * 30) / 18) + 0.75
                if hasattr(self, 'ids') and 'ISStiny' in self.ids:
                    self.ids.ISStiny.pos_hint = {"center_x": self._iss1_x, "center_y": self._iss1_y}
            else:
                if self._iss1_size_x <= 0.15:
                    self._iss1_size_x += 0.01
                    self._iss1_size_y += 0.01
                    if hasattr(self, 'ids') and 'ISStiny' in self.ids:
                        self.ids.ISStiny.size_hint = self._iss1_size_x, self._iss1_size_y
                else:
                    if self._iss1_starting:
                        # Start the second ISS animation
                        self._iss2_animation_event = Clock.schedule_interval(self._animate_iss2, 0.1)
                        self._iss1_starting = False
        except Exception as exc:
            log_error(f"Error in ISS1 animation: {exc}")
    
    def _animate_iss2(self, dt):
        """Animate the second ISS icon (ISStiny2)."""
        try:
            if hasattr(self, 'ids') and 'ISStiny2' in self.ids:
                self.ids.ISStiny2.size_hint = 0.07, 0.07
                self._iss2_x += 0.007
                self._iss2_y = (math.sin(self._iss2_x * 30) / 18) + 0.75
                if self._iss2_x > 1:
                    self._iss2_x -= 1.0
                self.ids.ISStiny2.pos_hint = {"center_x": self._iss2_x, "center_y": self._iss2_y}
        except Exception as exc:
            log_error(f"Error in ISS2 animation: {exc}")
    
    def _start_arduino_monitoring(self):
        """Start monitoring Arduino connection status."""
        try:
            self._arduino_monitor_event = Clock.schedule_interval(self._update_arduino_status, 2.0)
            log_info("MainScreen: Arduino monitoring started")
        except Exception as exc:
            log_error(f"Failed to start Arduino monitoring: {exc}")
    
    def _stop_arduino_monitoring(self):
        """Stop monitoring Arduino connection status."""
        try:
            if hasattr(self, '_arduino_monitor_event'):
                self._arduino_monitor_event.cancel()
            log_info("MainScreen: Arduino monitoring stopped")
        except Exception as exc:
            log_error(f"Failed to stop Arduino monitoring: {exc}")
    
    def _update_arduino_status(self, dt):
        """Update Arduino status display."""
        try:
            if hasattr(self, 'ids') and 'arduino' in self.ids and 'arduino_count' in self.ids:
                # Check if any Arduinos are connected
                arduino_count_text = self.ids.arduino_count.text
                arduino_connected = arduino_count_text and arduino_count_text.strip() != ''
                
                if arduino_connected:
                    # Arduino connected - show no_transmit status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_notransmit.png"
                else:
                    # No Arduino connected - show offline status
                    self.ids.arduino.source = f"{self.mimic_directory}/Mimic/Pi/imgs/signal/arduino_offline.png"
        except Exception as exc:
            log_error(f"Error updating Arduino status: {exc}")
    
    def _check_github_updates(self):
        """Check if there are GitHub repository updates available."""
        try:
            # Get the git repository path (should be the Mimic directory)
            repo_path = self.mimic_directory
            log_info(f"MainScreen: Checking for git repository at: {repo_path}")
            
            # Check if this is a git repository
            git_dir = os.path.join(repo_path, '.git')
            log_info(f"MainScreen: Looking for .git directory at: {git_dir}")
            if not os.path.exists(git_dir):
                log_info(f"MainScreen: Not a git repository at {repo_path}, skipping update check")
                return None
            
            # Get current local commit hash
            try:
                log_info(f"MainScreen: Running git rev-parse HEAD from working directory: {repo_path}")
                result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    log_error(f"Failed to get local commit hash: {result.stderr}")
                    return None
                local_commit = result.stdout.strip()
                log_info(f"MainScreen: Local commit hash: {local_commit[:8]}")
            except subprocess.TimeoutExpired:
                log_error("Git command timed out")
                return None
            except Exception as exc:
                log_error(f"Error getting local commit hash: {exc}")
                return None
            
            # Get remote origin URL
            try:
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    log_error(f"Failed to get remote URL: {result.stderr}")
                    return None
                remote_url = result.stdout.strip()
            except subprocess.TimeoutExpired:
                log_error("Git remote command timed out")
                return None
            except Exception as exc:
                log_error(f"Error getting remote URL: {exc}")
                return None
            
            # Extract owner and repo from GitHub URL
            if 'github.com' in remote_url:
                # Handle both HTTPS and SSH URLs
                if remote_url.startswith('https://'):
                    parts = remote_url.replace('https://github.com/', '').replace('.git', '').split('/')
                elif remote_url.startswith('git@'):
                    parts = remote_url.replace('git@github.com:', '').replace('.git', '').split('/')
                else:
                    log_error(f"Unsupported remote URL format: {remote_url}")
                    return None
                
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    
                    # Get the latest commit from GitHub API
                    if not REQUESTS_AVAILABLE:
                        log_info("MainScreen: requests module not available, cannot check GitHub API")
                        return None
                        
                    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits/main"
                    try:
                        response = requests.get(api_url, timeout=10)
                        if response.status_code == 200:
                            latest_commit = response.json()['sha']
                            
                            if latest_commit != local_commit:
                                log_info(f"MainScreen: GitHub update available. Local: {local_commit[:8]}, Remote: {latest_commit[:8]}")
                                return {
                                    'local': local_commit[:8],
                                    'remote': latest_commit[:8],
                                    'owner': owner,
                                    'repo': repo
                                }
                            else:
                                log_info("MainScreen: Repository is up to date")
                                return None
                        else:
                            log_error(f"GitHub API returned status {response.status_code}")
                            return None
                    except requests.exceptions.RequestException as exc:
                        log_error(f"Failed to check GitHub API: {exc}")
                        return None
                else:
                    log_error(f"Could not parse GitHub URL: {remote_url}")
                    return None
            else:
                log_info("MainScreen: Not a GitHub repository, skipping update check")
                return None
                
        except Exception as exc:
            log_error(f"Error checking GitHub updates: {exc}")
            return None
    
    def _check_and_update_github_status(self):
        """Check for GitHub updates and update status if needed."""
        try:
            # Only check if we have a status label
            if not hasattr(self.ids, 'status_label'):
                return
            
            # Check for GitHub updates
            update_info = self._check_github_updates()
            
            if update_info:
                # There's an update available
                status_text = f"GitHub update available! Run 'git pull' to update."
                self.ids.status_label.text = status_text
                log_info(f"MainScreen: Status updated with GitHub update info: {status_text}")
            else:
                # No update available - just log it
                log_info("MainScreen: No GitHub updates available")
                    
        except Exception as exc:
            log_error(f"Error updating GitHub status: {exc}")
    
    
    # helper stays unchanged
    @staticmethod
    def _terminate_attr(app: App, attr_name: str) -> None:
        proc = getattr(app, attr_name, None)
        if not proc:
            return
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        except Exception as exc:
            log_error(f"Failed to terminate {attr_name}: {exc}")
        finally:
            setattr(app, attr_name, None)
            log_info(f"{attr_name} terminated.")