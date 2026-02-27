import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from rembg import remove
import os
import threading
import math

# ── Palette ──────────────────────────────────────────────────────────────────
BG_DARK      = "#0D0F14"
BG_CARD      = "#151820"
BG_SURFACE   = "#1C2030"
ACCENT       = "#6C63FF"
ACCENT_GLOW  = "#4B44CC"
ACCENT_LIGHT = "#9D97FF"
TEXT_PRIMARY = "#F0F2FF"
TEXT_MUTED   = "#6B7280"
SUCCESS      = "#22D3A0"
ERROR_COLOR  = "#FF5F7E"
BORDER       = "#252A3A"

output_image_global = None  # holds the processed PIL image for saving


def make_rounded_rect(canvas, x1, y1, x2, y2, r, **kwargs):
    """Draw a rounded rectangle on a canvas."""
    canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90,  extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0,   extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
    canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
    canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)


def create_checkerboard(size=(260, 260), tile=12):
    """Generate a checkerboard pattern as a PhotoImage (transparency indicator)."""
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    cols = math.ceil(size[0] / tile)
    rows = math.ceil(size[1] / tile)
    light, dark = (200, 200, 200), (155, 155, 155)
    for r in range(rows):
        for c in range(cols):
            color = light if (r + c) % 2 == 0 else dark
            draw.rectangle([c*tile, r*tile, (c+1)*tile, (r+1)*tile], fill=color)
    return img


class AnimatedButton(tk.Canvas):
    """Pill-shaped button with hover animation."""

    def __init__(self, parent, text, command, width=220, height=46,
                 bg_color=ACCENT, hover_color=ACCENT_GLOW,
                 text_color=TEXT_PRIMARY, font=None, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=BG_DARK, highlightthickness=0, **kwargs)
        self._text = text
        self._cmd = command
        self._width, self._height = width, height
        self._bg = bg_color
        self._hover = hover_color
        self._tc = text_color
        self._font = font or ("Helvetica", 11, "bold")
        self._current = bg_color
        self._disabled = False

        self._draw(bg_color)
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self, color):
        self.delete("all")
        r = self._height // 2
        # shadow (solid fallback, tkinter doesn't support alpha in color strings)
        self.create_oval(4, 4, self._width-4, self._height+4, fill="#000000", outline="")
        # body
        self.create_oval(0, 0, self._height, self._height, fill=color, outline="")
        self.create_oval(self._width-self._height, 0, self._width, self._height, fill=color, outline="")
        self.create_rectangle(r, 0, self._width-r, self._height, fill=color, outline="")
        # text
        self.create_text(self._width//2, self._height//2, text=self._text,
                         fill=self._tc if not self._disabled else TEXT_MUTED,
                         font=self._font)

    def _on_enter(self, _):
        if not self._disabled:
            self._draw(self._hover)

    def _on_leave(self, _):
        if not self._disabled:
            self._draw(self._bg)

    def _on_click(self, _):
        if not self._disabled and self._cmd:
            self._cmd()

    def set_state(self, disabled: bool, text: str = None):
        self._disabled = disabled
        if text:
            self._text = text
        self._draw(TEXT_MUTED if disabled else self._bg)

    def set_text(self, text):
        self._text = text
        self._draw(TEXT_MUTED if self._disabled else self._bg)


# ── Main App ──────────────────────────────────────────────────────────────────
class BGRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BG Eraser")
        self.root.geometry("480x700")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DARK)

        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=BG_DARK)
        header.pack(fill="x", padx=30, pady=(28, 0))

        tk.Label(header, text="BG", font=("Georgia", 22, "bold"),
                 fg=ACCENT, bg=BG_DARK).pack(side="left")
        tk.Label(header, text=" Eraser", font=("Georgia", 22, "bold"),
                 fg=TEXT_PRIMARY, bg=BG_DARK).pack(side="left")
        tk.Label(header, text="Powered by rembg",
                 font=("Helvetica", 9), fg=TEXT_MUTED, bg=BG_DARK).pack(side="right", pady=6)

        # divider
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(14, 0))

        # ── Drop / Preview card ───────────────────────────────────────────────
        self.card = tk.Frame(self.root, bg=BG_CARD,
                             highlightbackground=BORDER, highlightthickness=1)
        self.card.pack(padx=30, pady=20, fill="x")

        self.preview_canvas = tk.Canvas(self.card, width=420, height=300,
                                        bg=BG_CARD, highlightthickness=0)
        self.preview_canvas.pack(padx=20, pady=20)
        self._draw_placeholder()

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Upload an image to get started")
        status_frame = tk.Frame(self.root, bg=BG_SURFACE,
                                highlightbackground=BORDER, highlightthickness=1)
        status_frame.pack(padx=30, fill="x")

        self.status_dot = tk.Label(status_frame, text="●", font=("Helvetica", 9),
                                   fg=TEXT_MUTED, bg=BG_SURFACE)
        self.status_dot.pack(side="left", padx=(14, 4), pady=10)
        tk.Label(status_frame, textvariable=self.status_var,
                 font=("Helvetica", 10), fg=TEXT_MUTED, bg=BG_SURFACE,
                 anchor="w").pack(side="left", pady=10)

        # ── Progress bar (hidden by default) ─────────────────────────────────
        self.progress_frame = tk.Frame(self.root, bg=BG_DARK)
        self.progress_frame.pack(padx=30, fill="x", pady=(10, 0))
        self.progress_canvas = tk.Canvas(self.progress_frame, height=4,
                                         bg=BG_SURFACE, highlightthickness=0)
        self.progress_canvas.pack(fill="x")
        self.progress_bar = None
        self._progress_val = 0
        self._animating = False

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = tk.Frame(self.root, bg=BG_DARK)
        btn_row.pack(pady=22)

        self.upload_btn = AnimatedButton(
            btn_row, text="Upload Image", command=self._upload,
            width=190, height=46, bg_color=ACCENT, hover_color=ACCENT_GLOW
        )
        self.upload_btn.pack(side="left", padx=8)

        self.save_btn = AnimatedButton(
            btn_row, text="Save Image", command=self._save,
            width=190, height=46, bg_color="#1E2A1E", hover_color=SUCCESS,
            text_color=TEXT_MUTED
        )
        self.save_btn.pack(side="left", padx=8)
        self.save_btn.set_state(True)

        # ── Footer ────────────────────────────────────────────────────────────
        tk.Label(self.root, text="PNG · JPG · JPEG · WEBP  •  Transparent PNG output",
                 font=("Helvetica", 8), fg=TEXT_MUTED, bg=BG_DARK).pack(pady=(0, 14))

    # ── Placeholder ──────────────────────────────────────────────────────────
    def _draw_placeholder(self):
        c = self.preview_canvas
        c.delete("all")
        W, H = 420, 300
        # dashed border
        dash_step = 12
        for x in range(20, W-20, dash_step*2):
            c.create_line(x, 20, x+dash_step, 20, fill=BORDER, width=1)
            c.create_line(x, H-20, x+dash_step, H-20, fill=BORDER, width=1)
        for y in range(20, H-20, dash_step*2):
            c.create_line(20, y, 20, y+dash_step, fill=BORDER, width=1)
            c.create_line(W-20, y, W-20, y+dash_step, fill=BORDER, width=1)
        # icon
        c.create_text(W//2, H//2 - 24, text="⬆", font=("Helvetica", 36), fill=BORDER)
        c.create_text(W//2, H//2 + 20, text="Drop or upload an image",
                      font=("Helvetica", 12), fill=TEXT_MUTED)
        c.create_text(W//2, H//2 + 42, text="Background will be removed automatically",
                      font=("Helvetica", 9), fill=BORDER)

    # ── Show preview ─────────────────────────────────────────────────────────
    def _show_preview(self, pil_image):
        c = self.preview_canvas
        c.delete("all")
        W, H = 420, 300

        # checkerboard background
        checker = create_checkerboard((W, H))
        self._checker_photo = ImageTk.PhotoImage(checker)
        c.create_image(0, 0, anchor="nw", image=self._checker_photo)

        # thumbnail
        thumb = pil_image.copy()
        thumb.thumbnail((W - 40, H - 40), Image.LANCZOS)
        # composite on white to show alpha
        bg = Image.new("RGBA", thumb.size, (0, 0, 0, 0))
        composite = Image.alpha_composite(bg, thumb) if thumb.mode == "RGBA" else thumb
        self._preview_photo = ImageTk.PhotoImage(composite)
        c.create_image(W//2, H//2, anchor="center", image=self._preview_photo)

    # ── Progress animation ────────────────────────────────────────────────────
    def _start_progress(self):
        self._animating = True
        self._progress_val = 0
        self._tick_progress()

    def _tick_progress(self):
        if not self._animating:
            return
        self._progress_val = (self._progress_val + 2) % 100
        self._draw_progress(self._progress_val)
        self.root.after(20, self._tick_progress)

    def _draw_progress(self, val):
        c = self.progress_canvas
        c.delete("all")
        W = c.winfo_width() or 420
        fill_w = int(W * val / 100)
        c.create_rectangle(0, 0, fill_w, 4, fill=ACCENT, outline="")
        c.create_rectangle(fill_w, 0, W, 4, fill=BG_SURFACE, outline="")

    def _stop_progress(self, success=True):
        self._animating = False
        c = self.progress_canvas
        c.delete("all")
        W = c.winfo_width() or 420
        color = SUCCESS if success else ERROR_COLOR
        c.create_rectangle(0, 0, W, 4, fill=color, outline="")
        self.root.after(1200, lambda: c.delete("all"))

    # ── Upload flow ───────────────────────────────────────────────────────────
    def _upload(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")]
        )
        if not path:
            return

        self.upload_btn.set_state(True, "Processing…")
        self.save_btn.set_state(True)
        self.status_dot.config(fg=ACCENT)
        self.status_var.set("Removing background…")
        self._draw_placeholder()
        self._start_progress()

        threading.Thread(target=self._process, args=(path,), daemon=True).start()

    def _process(self, file_path):
        global output_image_global
        try:
            inp = Image.open(file_path)
            out = remove(inp)
            output_image_global = out

            self.root.after(0, lambda: self._on_success(out))
        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))

    def _on_success(self, image):
        self._stop_progress(True)
        self._show_preview(image)
        self.upload_btn.set_state(False, "Upload Image")
        self.save_btn.set_state(False)
        self.save_btn._bg = SUCCESS
        self.save_btn._tc = "#0D1A0D"
        self.save_btn.set_text("Save Image")
        self.status_dot.config(fg=SUCCESS)
        self.status_var.set("Background removed successfully  ✓")

    def _on_error(self, msg):
        self._stop_progress(False)
        self.upload_btn.set_state(False, "Upload Image")
        self.status_dot.config(fg=ERROR_COLOR)
        self.status_var.set(f"Error: {msg}")
        messagebox.showerror("Error", msg)

    # ── Save flow ─────────────────────────────────────────────────────────────
    def _save(self):
        global output_image_global
        if output_image_global is None:
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            title="Save Transparent Image"
        )
        if not save_path:
            return

        try:
            output_image_global.save(save_path)
            self.status_var.set(f"Saved → {os.path.basename(save_path)}")
            messagebox.showinfo("Saved!", f"Image saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = BGRemoverApp(root)
    root.mainloop()