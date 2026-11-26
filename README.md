# Football for Fenn

Live scores and today's fixtures for six leagues on your Fenn notch.

## What it does

- Wide tile: the live match, your favourite team's match, or the first fixture of the day. Team codes keep it short, e.g. `RMA v BAR`.
- Pill: pulses while any match in the chosen league is live.
- Page (click the tile): league chips (PL, La Liga, Serie A, Bundesliga, Ligue 1, UCL), an optional favourite-team box and the list of today's matches with kick-off times in your local time.

## Refresh

It asks ESPN for the selected league every 60 seconds while a match is live and every 5 minutes otherwise. The refresh button updates it at once. If the connection drops, the tile says `No internet, retrying` and tries again after 1, 2 and 4 minutes, then every 5 minutes.

Want less data? See [Fenn-FootballSaver](https://github.com/RoyalNetrix/Fenn-FootballSaver).

## Install

1. Copy this folder to `%APPDATA%\Fenn\plugins\football\` so that `plugin.toml` and `main.py` sit directly inside it.
2. In Fenn, open **Settings** and turn on **Plugin dev mode**. The tile appears within a few seconds, with no restart. (Without dev mode, restart Fenn.)
3. New tiles are added after the built-in ones, possibly on the second page. Use the pencil in the grid to move or resize it.

Requires Fenn with plugin support.

## Requirements

Python 3.8+ (Fenn can set it up for you, or use your own). No extra packages, no API key.

## Network and privacy

- `site.api.espn.com`: ESPN's public scoreboard JSON for the selected league. Nothing about you is sent.
- This is an unofficial, undocumented endpoint. It can change or stop working without notice.

## Settings and data

- League and favourite team are saved in `%APPDATA%\Fenn\plugin-data\football\config.json`.
- Favourite team is a substring match, e.g. `madrid`. With one set, the tile follows that team's matches.
- `LEAGUES` at the top of `main.py` lists the competitions by ESPN code. Add more there.

## Limitations

- It shows the matches the scoreboard returns for the current day, not a full season schedule.

## Troubleshooting

- **Tile says "Stopped":** hover it to see the error and the last lines of the plugin's output.
- **Nothing happens:** Fenn can set up Python for you. If that didn't work, make sure `python --version` works in a new PowerShell window, or install Python from python.org and tick "Add python.exe to PATH".
- **Full log:** the logs of the last ten Fenn runs are in `%APPDATA%\Fenn\logs`.
- **Plugins are programs.** They run with the same rights as Fenn. Read the code (one short file) before installing any plugin.

## Credits and license

Scores come from ESPN's public scoreboard feed, which is not an official API. Not affiliated with or endorsed by ESPN.

MIT. See `LICENSE`.

## Files

- `plugin.toml`: the plugin manifest.
- `main.py`: the whole plugin.
- `LICENSE`, `.gitignore`.
