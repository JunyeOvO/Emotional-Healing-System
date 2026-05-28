"""
SRP Live Visualizer — 实时数据仪表盘
=====================================
监听 UDP 5005 端口，实时绘制 4 面板生理数据仪表盘。

用法:
    # 终端 1: 启动数据管道
    python main.py --weather storm --duration 120

    # 终端 2: 启动可视化
    python visualizer.py

    # 可选参数
    python visualizer.py --port 5005 --history 20 --fps 15

依赖: pip install matplotlib
"""

import argparse
import json
import queue
import socket
import sys
import threading
import time
from collections import deque

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ── Config ────────────────────────────────────────────────────────────────────

UDP_HOST = "127.0.0.1"
UDP_PORT = 5005
HISTORY_SECONDS = 20   # X 轴历史窗口（秒）
TARGET_FPS = 15         # 绘图刷新率
MAX_SAMPLES = 2000      # 缓冲区最大样本数

# ── Color palette ─────────────────────────────────────────────────────────────

WEATHER_COLORS = {
    "storm": "#4a6fa5",   # 蓝灰
    "heat":  "#e07b4c",   # 暖橙
    "snow":  "#b8d4e3",   # 淡蓝白
    "fade":  "#8b7e9b",   # 淡紫
}
PHASE_COLORS = {
    "inhale": "#5da37c",
    "exhale": "#c47b5a",
    "hold":   "#d4a843",
}


class UDPListener(threading.Thread):
    """后台线程：持续监听 UDP 并推入队列"""

    def __init__(self, host=UDP_HOST, port=UDP_PORT, data_queue=None):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.queue = data_queue or queue.Queue()
        self.running = True
        self.frame_count = 0

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.settimeout(0.5)

        while self.running:
            try:
                data, _ = sock.recvfrom(65535)
                msg = json.loads(data.decode("utf-8"))
                self.queue.put(msg)
                self.frame_count += 1
            except socket.timeout:
                continue
            except (json.JSONDecodeError, OSError):
                continue

        sock.close()

    def stop(self):
        self.running = False


class Dashboard:
    """4 面板实时仪表盘"""

    def __init__(self, history_seconds=HISTORY_SECONDS):
        self.history = history_seconds
        self.data = {
            "ts": deque(maxlen=MAX_SAMPLES),
            "respiration_raw": deque(maxlen=MAX_SAMPLES),
            "breath_phase": deque(maxlen=MAX_SAMPLES),
            "breath_score": deque(maxlen=MAX_SAMPLES),
            "calm_index": deque(maxlen=MAX_SAMPLES),
            "hr": deque(maxlen=MAX_SAMPLES),
            "rmssd": deque(maxlen=MAX_SAMPLES),
            "weather_intensity": deque(maxlen=MAX_SAMPLES),
            "weather_type": None,
            "guidance_prompt": "",
        }

        self._setup_figure()

    def _setup_figure(self):
        plt.rcParams.update({
            "figure.facecolor": "#1a1a2e",
            "axes.facecolor": "#16213e",
            "axes.edgecolor": "#333366",
            "axes.labelcolor": "#c0c0d0",
            "text.color": "#c0c0d0",
            "xtick.color": "#808090",
            "ytick.color": "#808090",
            "grid.color": "#2a2a4a",
        })

        self.fig, ((self.ax_breath, self.ax_hr),
                    (self.ax_score, self.ax_weather)) = plt.subplots(
            2, 2, figsize=(14, 9), dpi=100
        )
        self.fig.suptitle("SRP 实时生理数据监控台", fontsize=14,
                          color="#e0e0f0", fontweight="bold", y=0.97)

        # Panel 1: 呼吸波形
        self.ax_breath.set_title("Respiration Waveform", fontsize=11, color="#a0b0d0")
        self.ax_breath.set_ylabel("Amplitude")
        self.ax_breath.set_ylim(-0.2, 1.2)
        self.ax_breath.grid(True, alpha=0.3)
        (self.line_breath,) = self.ax_breath.plot([], [], color="#5da37c",
                                                   linewidth=1.2, alpha=0.9)
        self.breath_fill = self.ax_breath.fill_between(
            [], 0, [], alpha=0.15, color="#5da37c"
        )

        # Panel 2: 心率 + HRV
        self.ax_hr.set_title("Heart Rate & HRV", fontsize=11, color="#a0b0d0")
        self.ax_hr.set_ylabel("HR (BPM)", color="#e07b4c")
        self.ax_hr.set_ylim(40, 120)
        self.ax_hr.grid(True, alpha=0.3)
        (self.line_hr,) = self.ax_hr.plot([], [], color="#e07b4c",
                                           linewidth=1.5, label="HR")
        self.ax_hrv = self.ax_hr.twinx()
        self.ax_hrv.set_ylabel("RMSSD (ms)", color="#5b9bd5")
        self.ax_hrv.set_ylim(0, 100)
        (self.line_rmssd,) = self.ax_hrv.plot([], [], color="#5b9bd5",
                                                linewidth=1.2, alpha=0.8, label="RMSSD")
        lines = [self.line_hr, self.line_rmssd]
        labels = [l.get_label() for l in lines]
        self.ax_hr.legend(lines, labels, loc="upper left",
                          fontsize=7, facecolor="#16213e", edgecolor="#333366")

        # Panel 3: 评分曲线
        self.ax_score.set_title("Scores", fontsize=11, color="#a0b0d0")
        self.ax_score.set_ylabel("Score (0-100)")
        self.ax_score.set_ylim(-5, 105)
        self.ax_score.grid(True, alpha=0.3)
        (self.line_bs,) = self.ax_score.plot([], [], color="#f0c05a",
                                              linewidth=1.5, label="Breath Score")
        (self.line_ci,) = self.ax_score.plot([], [], color="#6cb4d9",
                                              linewidth=1.5, label="Calm Index")
        self.ax_score.legend(loc="upper left", fontsize=7,
                             facecolor="#16213e", edgecolor="#333366")

        # Panel 4: 天气状态面板
        self.ax_weather.set_title("Weather Status", fontsize=11, color="#a0b0d0")
        self.ax_weather.set_ylim(-0.1, 1.2)
        self.ax_weather.set_ylabel("Intensity")
        self.ax_weather.grid(True, alpha=0.3, axis="y")
        (self.line_wi,) = self.ax_weather.plot([], [], color="#d4a843",
                                                linewidth=1.5, drawstyle="steps-post")
        self.weather_text = self.ax_weather.text(
            0.02, 0.92, "", transform=self.ax_weather.transAxes,
            fontsize=20, color="#e0e0f0", va="top", fontweight="bold"
        )
        self.prompt_text = self.ax_weather.text(
            0.02, 0.45, "", transform=self.ax_weather.transAxes,
            fontsize=11, color="#a0a0c0", va="center",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#16213e", edgecolor="#333366")
        )

        self.fig.tight_layout(rect=[0, 0, 1, 0.95])

        # artists for blit
        self._artists = [
            self.line_breath, self.line_hr, self.line_rmssd,
            self.line_bs, self.line_ci, self.line_wi,
            self.weather_text, self.prompt_text,
        ]

    def feed(self, msg: dict):
        """从 UDP 消息提取数据并推入缓冲区"""
        now = time.time()
        self.data["ts"].append(now)
        self.data["respiration_raw"].append(
            msg.get("breath", {}).get("depth", 0)
        )
        self.data["breath_phase"].append(
            msg.get("breath", {}).get("phase", "exhale")
        )
        self.data["breath_score"].append(
            msg.get("breath", {}).get("score", 0)
        )
        self.data["calm_index"].append(
            msg.get("calm", {}).get("index", 0)
        )
        self.data["hr"].append(
            msg.get("hrv", {}).get("hr", 0)
        )
        self.data["rmssd"].append(
            msg.get("hrv", {}).get("rmssd", 0)
        )
        self.data["weather_intensity"].append(
            msg.get("weather", {}).get("intensity", 0)
        )
        self.data["weather_type"] = msg.get("weather", {}).get("type", "storm")
        self.data["guidance_prompt"] = msg.get("guidance", {}).get("prompt", "")

    def update(self, frame):
        """matplotlib FuncAnimation 回调"""
        ts = self.data["ts"]
        if len(ts) < 2:
            return self._artists

        t0 = ts[-1] - self.history
        t_rel = [t - ts[0] for t in ts]  # relative time from start

        # Panel 1: Breath waveform — 用 phase 着色
        self.line_breath.set_data(t_rel, self.data["respiration_raw"])
        self.ax_breath.set_xlim(max(0, t_rel[-1] - self.history), t_rel[-1] + 1)

        # Panel 2: HR + RMSSD
        self.line_hr.set_data(t_rel, self.data["hr"])
        self.line_rmssd.set_data(t_rel, self.data["rmssd"])
        self.ax_hr.set_xlim(max(0, t_rel[-1] - self.history), t_rel[-1] + 1)

        # Panel 3: Scores
        self.line_bs.set_data(t_rel, self.data["breath_score"])
        self.line_ci.set_data(t_rel, self.data["calm_index"])
        self.ax_score.set_xlim(max(0, t_rel[-1] - self.history), t_rel[-1] + 1)

        # Panel 4: Weather
        self.line_wi.set_data(t_rel, self.data["weather_intensity"])
        self.ax_weather.set_xlim(max(0, t_rel[-1] - self.history), t_rel[-1] + 1)

        wt = self.data["weather_type"] or "storm"
        wi = self.data["weather_intensity"][-1] if self.data["weather_intensity"] else 0

        weather_emoji = {"storm": "⛈", "heat": "🔥", "snow": "❄", "fade": "🌫"}
        weather_name = {"storm": "Storm 焦虑", "heat": "Heat 烦躁",
                        "snow": "Snow 低落", "fade": "Fade 孤独"}
        self.weather_text.set_text(
            f"{weather_emoji.get(wt, '?')}  {weather_name.get(wt, wt)}  强度:{wi:.2f}"
        )
        self.weather_text.set_color(WEATHER_COLORS.get(wt, "#e0e0f0"))

        prompt = self.data["guidance_prompt"]
        self.prompt_text.set_text(f"  {prompt}  " if prompt else "")

        return self._artists


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SRP Live Visualizer")
    parser.add_argument("--host", default=UDP_HOST, help=f"UDP host (default: {UDP_HOST})")
    parser.add_argument("--port", type=int, default=UDP_PORT, help=f"UDP port (default: {UDP_PORT})")
    parser.add_argument("--history", type=int, default=HISTORY_SECONDS,
                        help=f"History window in seconds (default: {HISTORY_SECONDS})")
    parser.add_argument("--fps", type=int, default=TARGET_FPS,
                        help=f"Refresh FPS (default: {TARGET_FPS})")
    args = parser.parse_args()

    data_queue = queue.Queue()
    listener = UDPListener(args.host, args.port, data_queue)
    listener.start()

    dashboard = Dashboard(history_seconds=args.history)

    # Timer: drain UDP queue into dashboard buffers
    def drain_queue():
        try:
            for _ in range(50):  # drain up to 50 messages per tick
                msg = data_queue.get_nowait()
                dashboard.feed(msg)
        except queue.Empty:
            pass

    ani = animation.FuncAnimation(
        dashboard.fig, dashboard.update,
        interval=1000 // args.fps,  # ms
        blit=False, cache_frame_data=False,
    )

    # Periodic drain via timer (FuncAnimation doesn't have pre-update hooks)
    _timer = dashboard.fig.canvas.new_timer(interval=1000 // args.fps)
    _timer.add_callback(drain_queue)

    print(f"SRP Visualizer ready — listening on UDP {args.host}:{args.port}")
    print(f"History: {args.history}s | Refresh: {args.fps} FPS")
    print("Start the data pipeline:  python main.py --weather storm")
    print("Close the window or Ctrl+C to exit.\n")

    _timer.start()
    plt.show()

    listener.stop()
    print(f"\nDone. UDP frames received: {listener.frame_count}")


if __name__ == "__main__":
    main()
