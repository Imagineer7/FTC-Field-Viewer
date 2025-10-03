# Re-run the interactive FTC field zone explorer with arrow-key control

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import gridspec
import matplotlib.patches as mpatches

# --- Build field grid ---
x = np.linspace(-100, 100, 1000)
y = np.linspace(-100, 100, 1000)
X, Y = np.meshgrid(x, y)

field_limit = 72  # ±72 inches => 144x144

# --- Zone boolean masks on the mesh (for shaded regions) ---
long_range = (Y <= X - 46) & (Y >= -X + 46)
short_range = (Y >= 1.015*X) & (Y <= -1.015*X)
red_parking = (X >= 30) & (X <= 45.75) & (Y >= -40.5) & (Y <= -24.7)
blue_parking = (X >= 30) & (X <= 45.75) & (Y >= 24.7) & (Y <= 40.5)
red_loading = (Y <= -47) & (X >= 47)
blue_loading = (Y >= 47) & (X >= 47)
red_alliance = ((Y < 0) & (X > 0)) | ((Y > 0) & (X < 0))
blue_alliance = ((Y > 0) & (X > 0)) | ((Y < 0) & (X < 0))

# --- Helper: evaluate zones for a single point (x0, y0) ---
def zone_membership(x0, y0):
    z = {
        "Long range": (y0 <= x0 - 46) and (y0 >= -x0 + 46),
        "Short range": (y0 >= 1.015*x0) and (y0 <= -1.015*x0),
        "Red parking": (x0 >= 30) and (x0 <= 45.75) and (y0 >= -40.5) and (y0 <= -24.7),
        "Blue parking": (x0 >= 30) and (x0 <= 45.75) and (y0 >= 24.7) and (y0 <= 40.5),
        "Red loading": (y0 <= -47) and (x0 >= 47),
        "Blue loading": (y0 >= 47) and (x0 >= 47),
        "Red alliance": ((y0 < 0) and (x0 > 0)) or ((y0 > 0) and (x0 < 0)),
        "Blue alliance": ((y0 > 0) and (x0 > 0)) or ((y0 < 0) and (x0 < 0)),
    }
    # Convenience flags
    z["In ANY launch zone"] = z["Long range"] or z["Short range"]
    z["In ANY parking"] = z["Red parking"] or z["Blue parking"]
    z["In ANY loading"] = z["Red loading"] or z["Blue loading"]
    return z

# --- Figure layout ---
fig = plt.figure(figsize=(12, 10))
gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1], wspace=0.25)
ax = fig.add_subplot(gs[0])
ax_info = fig.add_subplot(gs[1])
ax_info.axis("off")

# --- Draw zones ---
ax.contourf(X, Y, long_range, levels=[0.5, 1], alpha=0.6)
ax.contourf(X, Y, short_range, levels=[0.5, 1], alpha=0.6)
ax.contourf(X, Y, red_parking, levels=[0.5, 1], alpha=0.6)
ax.contourf(X, Y, blue_parking, levels=[0.5, 1], alpha=0.6)
ax.contourf(X, Y, red_loading, levels=[0.5, 1], alpha=0.6)
ax.contourf(X, Y, blue_loading, levels=[0.5, 1], alpha=0.6)
ax.contourf(X, Y, red_alliance, levels=[0.5, 1], alpha=0.25)
ax.contourf(X, Y, blue_alliance, levels=[0.5, 1], alpha=0.25)

# Axes, centerlines, and square boundary
ax.axhline(0, linewidth=0.8)
ax.axvline(0, linewidth=0.8)
ax.set_xlim(-field_limit, field_limit)
ax.set_ylim(-field_limit, field_limit)
ax.plot([-72, 72, 72, -72, -72], [-72, -72, 72, 72, -72], linewidth=2)
ax.set_xlabel("X (in)")
ax.set_ylabel("Y (in)")
ax.set_title("Interactive FTC Field Zones (Use Arrow Keys: ← ↑ → ↓)")

# Legend (bottom center)
legend_patches = [
    mpatches.Patch(label="Long Range Zone"),
    mpatches.Patch(label="Short Range Zone"),
    mpatches.Patch(label="Red Parking Zone"),
    mpatches.Patch(label="Blue Parking Zone"),
    mpatches.Patch(label="Red Loading Zone"),
    mpatches.Patch(label="Blue Loading Zone"),
    mpatches.Patch(label="Red Alliance Area"),
    mpatches.Patch(label="Blue Alliance Area"),
]
ax.legend(handles=legend_patches, loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=True)

# --- Movable point ---
state = {"x": 0.0, "y": 0.0, "step": 1.0}
pt = ax.plot(state["x"], state["y"], marker="o", markersize=8)[0]

# --- Info panel update ---
def render_info():
    z = zone_membership(state["x"], state["y"])
    lines = [
        f"Controls: arrow keys move, +/- change step",
        f"Position:  x = {state['x']:.2f} in,  y = {state['y']:.2f} in",
        f"Step: {state['step']:.2f} in",
        "",
        "Membership:",
    ]
    for k in ["Long range", "Short range", "Red parking", "Blue parking",
              "Red loading", "Blue loading", "Red alliance", "Blue alliance",
              "In ANY launch zone", "In ANY parking", "In ANY loading"]:
        lines.append(f" • {k}: {'YES' if z[k] else 'no'}")
    ax_info.clear()
    ax_info.axis("off")
    ax_info.text(0, 1, "\n".join(lines), va="top", fontsize=11)
    fig.canvas.draw_idle()

render_info()

# --- Movement / key handling ---
def on_key(event):
    key = event.key
    dx = dy = 0.0
    if key == "left":
        dx = -state["step"]
    elif key == "right":
        dx = state["step"]
    elif key == "up":
        dy = state["step"]
    elif key == "down":
        dy = -state["step"]
    elif key in ["+", "="]:
        state["step"] = min(12.0, state["step"] * 1.5)
    elif key in ["-", "_"]:
        state["step"] = max(0.25, state["step"] / 1.5)
    else:
        return

    # Update position, clamped to field bounds
    nx = np.clip(state["x"] + dx, -field_limit, field_limit)
    ny = np.clip(state["y"] + dy, -field_limit, field_limit)
    state["x"], state["y"] = nx, ny

    # Update plot
    pt.set_data([state["x"]], [state["y"]])
    render_info()

cid = fig.canvas.mpl_connect("key_press_event", on_key)

plt.show()
