# Neon Dodge for Raspberry Pi 3

**Neon Dodge** is a small offline arcade game written in Python and Pygame. Move the ship, avoid falling neon blocks, and survive as long as possible. The game is designed to use modest CPU and memory so it is suitable for a Raspberry Pi 3.

## Controls

| Key | Action |
|---|---|
| Arrow keys or WASD | Move the ship |
| P | Pause or resume |
| R | Restart after game over |
| Esc | Quit |

## Install on Raspberry Pi OS

Open a terminal and run:

```bash
sudo apt update
sudo apt install -y python3-pygame
```

Copy the `pi_neon_dodge` folder to the Raspberry Pi, then start the game with:

```bash
cd pi_neon_dodge
python3 game.py
```

The game expects a graphical desktop session. If you are connected over SSH without display forwarding, run it directly from the Raspberry Pi desktop or connect a monitor and keyboard.

## Optional desktop launcher

To launch the game by double-clicking it, create a file named `NeonDodge.desktop` in the same folder:

```ini
[Desktop Entry]
Type=Application
Name=Neon Dodge
Comment=Raspberry Pi arcade game
Exec=python3 /home/pi/pi_neon_dodge/game.py
Path=/home/pi/pi_neon_dodge
Terminal=false
Categories=Game;
```

Then make it executable:

```bash
chmod +x NeonDodge.desktop
```

If your folder is stored somewhere other than `/home/pi/pi_neon_dodge`, update the `Exec` and `Path` lines accordingly.

## Performance notes

The game uses a fixed 800×480 window, simple rectangles and polygons, a 60 FPS update target, and no external assets. These choices keep the game responsive on Raspberry Pi 3 hardware. If the game feels slow, close other desktop applications and set the game window to a smaller size through the display settings.
