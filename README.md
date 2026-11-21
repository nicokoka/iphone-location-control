# Location Control

A free, open-source tool that sets your iPhone's GPS location from your Mac. Pick a spot on a map, and every app on the phone (Find My, Maps, and the rest) reports that location until you turn it off.

It's built for privacy, so people who feel unsafe sharing their real location have a choice. It's a free alternative to paid location changers, and it uses the open-source [pymobiledevice3](https://github.com/doronz88/pymobiledevice3) library.

> **If you're worried about being stalked or tracked,** please also read [Staying safe](#staying-safe) below. A fake location can be noticed, and sometimes that makes things more dangerous.

---

## What you need

- A **Mac** (Apple Silicon or Intel) with [Homebrew](https://brew.sh) installed
- An **iPhone** on iOS 17 or newer (older versions may work but aren't tested)
- A **cable that carries data**, not just charging. An Apple cable is the safest bet.

## Install

1. Install Homebrew if you don't have it. Paste the command from [brew.sh](https://brew.sh) into Terminal.
2. Download this project. Click the green **Code** button on GitHub, choose **Download ZIP**, and unzip it. Or, if you use git:
   ```
   git clone https://github.com/nicokoka/iphone-location-control.git
   ```
3. Open Terminal in the project folder and run:
   ```
   chmod +x run.sh
   ```

## One-time iPhone setup

1. **Connect and trust.** Plug the iPhone into the Mac and unlock it. When **"Trust This Computer?"** appears, tap **Trust** and enter your passcode.
   - Your iPhone should now show up in the Finder sidebar. If it doesn't, see [Troubleshooting](#troubleshooting).
2. **Run the tool once** so it installs everything:
   ```
   ./run.sh
   ```
   You can stop it with Ctrl+C after it finishes setting up.
3. **Make the Developer Mode option appear.** It's hidden until a Mac asks for it:
   ```
   .venv/bin/pymobiledevice3 amfi reveal-developer-mode
   ```
4. **Turn on Developer Mode.** On the iPhone, go to **Settings → Privacy & Security** and scroll to the very bottom. Tap **Developer Mode**, turn it on, then tap **Restart**. After the restart, unlock the phone, tap **Turn On** and enter your passcode.

## Use it

1. Plug in the iPhone and unlock it.
2. Run:
   ```
   ./run.sh
   ```
   Enter your Mac password when asked. The phone connection needs it.
3. A map opens in your browser. **Click a spot**, then press **Set phone here**.
4. To check it worked, open Apple Maps on the phone.
5. To stop, press **Restore real location**, or press **Ctrl+C** in Terminal. Both put your real location back.

## Things to know

- **The fake location only lasts while `run.sh` is running and the phone is connected.** If you unplug the phone, close Terminal, or the phone restarts, your real location comes back. Find My may show that as a sudden jump.
- **A location that never moves** can look unusual to someone who checks often.
- **Developer Mode is visible** in Settings while it's on. To turn it off, go to Settings → Privacy & Security → Developer Mode.
- **Games:** Don't use this with location-based games like Pokémon GO. Faking your location breaks their rules and can get your account banned. Close those apps before you change your location.

## Staying safe

If you're using this because you're afraid of someone tracking you, these may protect you better than a fake location:

- **Safety Check** (Settings → Privacy & Security → Safety Check) shows exactly who can see your location and lets you remove access.
- **Check for hidden access:** unknown devices on your Apple ID (Settings → your name), shared Apple ID passwords, AirTags (Find My → Items → Identify Found Item), and other apps that share location, like Life360, Snap Map and Google Maps.
- **Talk to someone:** In the US, the National Domestic Violence Hotline (1-800-799-7233, or text START to 88788) helps with stalking and tech safety, including how to make changes without alerting the person. If you're in immediate danger, call 911 or your local emergency number.

## Troubleshooting

| Problem | Fix |
|---|---|
| Phone charges but "Trust This Computer" never appears | The cable probably only charges. Use a data cable. Also check **System Settings → Privacy & Security → Allow accessories to connect** on the Mac, and look for an "Allow accessory?" prompt on the Mac screen. |
| "No iPhone found" | Unlock the phone, try another USB port, plug straight into the Mac (not through a hub), and gently clean the Lightning port. |
| You tapped "Don't Trust" by accident | On the iPhone: Settings → General → Transfer or Reset iPhone → Reset → **Reset Location & Privacy**, then plug in again. |
| "Developer Mode is off" | Do steps 3–4 of the one-time setup. |
| "Can't reach the phone's tunnel" | Stop `run.sh` with Ctrl+C, make sure the phone is plugged in and unlocked, and start it again. |

## For developers

```
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
```

- `spoofer/device.py` wraps the `pymobiledevice3` CLI and holds the location session open
- `spoofer/server.py` is a Flask app that only listens on `127.0.0.1`
- `spoofer/static/index.html` is the map page (Leaflet + OpenStreetMap)

Contributions are welcome. Please open an issue or pull request.

## License

[MIT](LICENSE). Free to use, change and share.
